"""Tests for the runners module."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from pymodbus.exceptions import ModbusIOException

from hoymiles_mqtt.runners import RESET_HOUR, HoymilesQueryJob


@pytest.fixture
def mqtt_builder():
    """Creates a mock HassMqtt builder with necessary properties and methods."""
    builder = MagicMock()
    builder.get_configs.return_value = [("topic/config", "payload/config")]
    builder.get_states.return_value = [("topic/state", "payload/state")]
    builder.clear_production_today = MagicMock()
    return builder


@pytest.fixture
def mqtt_publisher():
    """Creates a mock MqttPublisher with necessary properties and methods."""
    publisher = MagicMock()
    publisher.broker = "localhost"
    publisher.broker_port = 1883
    schedule_ctx = MagicMock()
    schedule_ctx.__enter__.return_value = MagicMock()
    schedule_ctx.__exit__.return_value = None
    publisher.schedule_publish.return_value = schedule_ctx
    return publisher


@pytest.fixture
def modbus_client():
    """Creates a mock Modbus client with plant_data property."""
    client = MagicMock()
    client.plant_data = {"some": "data"}
    return client


def test_execute_first_run_publishes_configs_and_states(mqtt_builder, mqtt_publisher, modbus_client):
    """Tests if, during the first execution, configurations and states are published."""
    job = HoymilesQueryJob(mqtt_builder, mqtt_publisher, modbus_client)
    job.execute()
    mqtt_builder.get_configs.assert_called_once_with(plant_data=modbus_client.plant_data)
    mqtt_builder.get_states.assert_called_once_with(plant_data=modbus_client.plant_data)
    mqtt_publisher.schedule_publish.assert_called()


def test_execute_subsequent_run_only_publishes_states(mqtt_builder, mqtt_publisher, modbus_client):
    """Tests if, on subsequent executions, only states are published without re-publishing configurations."""
    job = HoymilesQueryJob(mqtt_builder, mqtt_publisher, modbus_client)
    job.execute()
    mqtt_builder.get_configs.assert_called_once_with(plant_data=modbus_client.plant_data)
    mqtt_builder.get_states.assert_called_once_with(plant_data=modbus_client.plant_data)
    mqtt_publisher.schedule_publish.assert_called()


def test_execute_no_plant_data(mqtt_builder, mqtt_publisher, modbus_client):
    """Tests that when plant_data is None, neither configurations nor states are published."""
    modbus_client.plant_data = None
    job = HoymilesQueryJob(mqtt_builder, mqtt_publisher, modbus_client)
    job.execute()
    mqtt_builder.get_configs.assert_not_called()
    mqtt_builder.get_states.assert_not_called()
    mqtt_publisher.schedule_publish.assert_not_called()


def test_execute_modbus_exception(mqtt_builder, mqtt_publisher, modbus_client):
    """Tests that in case of ModbusIOException, no data or configurations are published."""
    exc = ModbusIOException("No response received, expected at least 8 bytes")
    type(modbus_client).plant_data = PropertyMock(side_effect=ModbusIOException(exc))
    job = HoymilesQueryJob(mqtt_builder, mqtt_publisher, modbus_client)
    job.execute()
    mqtt_builder.get_configs.assert_not_called()
    mqtt_builder.get_states.assert_not_called()
    mqtt_publisher.schedule_publish.assert_not_called()


def test_execute_other_exception(mqtt_builder, mqtt_publisher, modbus_client):
    """Tests that in case of another exception when accessing plant_data, no data or configurations are published."""
    type(modbus_client).plant_data = PropertyMock(side_effect=ModbusIOException("Some other modbus error"))
    job = HoymilesQueryJob(mqtt_builder, mqtt_publisher, modbus_client)
    job.execute()
    mqtt_builder.get_configs.assert_not_called()
    mqtt_builder.get_states.assert_not_called()
    mqtt_publisher.schedule_publish.assert_not_called()


def test_execute_reset_hour_triggers_clear(mqtt_builder, mqtt_publisher, modbus_client):
    """Tests that at RESET_HOUR, the clear_production_today method is called."""
    with patch("time.localtime") as mock_localtime:
        mock_localtime.return_value.tm_hour = RESET_HOUR
        job = HoymilesQueryJob(mqtt_builder, mqtt_publisher, modbus_client)
        job.execute()
        mqtt_builder.clear_production_today.assert_called_once()


def test_execute_does_not_call_clear_production_today_outside_reset_hour(mqtt_builder, mqtt_publisher, modbus_client):
    """Tests that outside RESET_HOUR, the clear_production_today method is not called."""
    with patch("time.localtime") as mock_localtime:
        mock_localtime.return_value.tm_hour = (RESET_HOUR + 1) % 24
        job = HoymilesQueryJob(mqtt_builder, mqtt_publisher, modbus_client)
        job.execute()
        mqtt_builder.clear_production_today.assert_not_called()
