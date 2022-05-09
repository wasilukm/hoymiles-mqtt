"""Runners."""
import threading
import time
from typing import Callable

from hoymiles_modbus.client import HoymilesModbusTCP

from hoymiles_mqtt.ha import HassMqtt
from hoymiles_mqtt.mqtt import MqttPublisher

RESET_HOUR = 23


class HoymilesQueryJob:
    """Get data from DTU and publish to MQTT broker."""

    _lock = threading.Lock()

    def __init__(self, mqtt_builder: HassMqtt, mqtt_publisher: MqttPublisher, modbus_client: HoymilesModbusTCP):
        """Initialize the object.

        Arguments:
            mqtt_builder: an instance of MQTT message builder
            mqtt_publisher: an instance of MQTT publisher
            modbus_client: an instance of Modbus client

        """
        self._mqtt_builder: HassMqtt = mqtt_builder
        self._mqtt_publisher: MqttPublisher = mqtt_publisher
        self._modbus_client: HoymilesModbusTCP = modbus_client
        self._mqtt_configured: bool = False

    def execute(self):
        """Get data from DTU and publish to MQTT broker."""
        is_acquired = self._lock.acquire(blocking=False)
        if is_acquired:
            if time.localtime().tm_hour == RESET_HOUR:
                self._mqtt_builder.clear_production_today()
            try:
                plant_data = self._modbus_client.plant_data
                if not self._mqtt_configured:
                    for topic, payload in self._mqtt_builder.get_configs(plant_data=plant_data):
                        self._mqtt_publisher.publish(topic=topic, message=payload, retain=True)
                    self._mqtt_configured = True
                for topic, payload in self._mqtt_builder.get_states(plant_data=plant_data):
                    self._mqtt_publisher.publish(topic=topic, message=payload)
            finally:
                self._lock.release()


def run_periodic_job(period: int, job: Callable) -> None:
    """Run given function periodically.

    Arguments:
        period: execution period
        job: function to execute

    """
    while True:
        threading.Thread(target=job).start()
        time.sleep(period)
