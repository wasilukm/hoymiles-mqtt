#!/usr/bin/env python
"""Tests for `hoymiles_mqtt` package."""
import json

from hoymiles_modbus.client import MISeriesMicroinverterData, PlantData

from hoymiles_mqtt.ha import HassMqtt


def test_config_payload():
    """Test HassMqtt.config_payload."""
    microinverter_data = MISeriesMicroinverterData(
        data_type=0,
        serial_number='102162804827',
        port_number=3,
        pv_voltage=0,
        pv_current=0,
        grid_voltage=0,
        grid_frequency=0,
        pv_power=0,
        today_production=0,
        total_production=0,
        temperature=0,
        operating_status=0,
        alarm_code=0,
        alarm_count=0,
        link_status=0,
        reserved=[],
    )
    plant_data = PlantData('dtu_serial', microinverter_data=[microinverter_data])
    ha = HassMqtt(mi_entities=['grid_voltage'], port_entities=['pv_voltage'])
    payload = list(ha.get_configs(plant_data))
    assert payload == [
        (
            'homeassistant/sensor/dtu_serial/_pv_power/config',
            json.dumps(
                {
                    'device': {
                        'name': 'DTU_dtu_serial',
                        'identifiers': ['hoymiles_mqtt_dtu_serial'],
                        'manufacturer': 'Hoymiles',
                    },
                    'name': 'pv_power',
                    'unique_id': 'hoymiles_mqtt__dtu_serial_pv_power',
                    'state_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                    'value_template': '{{ value_json.pv_power }}',
                    'device_class': 'power',
                    'unit_of_measurement': 'W',
                    'state_class': 'measurement',
                }
            ),
        ),
        (
            'homeassistant/sensor/dtu_serial/_today_production/config',
            json.dumps(
                {
                    'device': {
                        'name': 'DTU_dtu_serial',
                        'identifiers': ['hoymiles_mqtt_dtu_serial'],
                        'manufacturer': 'Hoymiles',
                    },
                    'name': 'today_production',
                    'unique_id': 'hoymiles_mqtt__dtu_serial_today_production',
                    'state_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                    'value_template': '{{ value_json.today_production }}',
                    'device_class': 'energy',
                    'unit_of_measurement': 'Wh',
                    'state_class': 'total_increasing',
                }
            ),
        ),
        (
            'homeassistant/sensor/dtu_serial/_total_production/config',
            json.dumps(
                {
                    'device': {
                        'name': 'DTU_dtu_serial',
                        'identifiers': ['hoymiles_mqtt_dtu_serial'],
                        'manufacturer': 'Hoymiles',
                    },
                    'name': 'total_production',
                    'unique_id': 'hoymiles_mqtt__dtu_serial_total_production',
                    'state_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                    'value_template': '{{ value_json.total_production }}',
                    'device_class': 'energy',
                    'unit_of_measurement': 'Wh',
                    'state_class': 'total_increasing',
                }
            ),
        ),
        (
            'homeassistant/binary_sensor/dtu_serial/_alarm_flag/config',
            json.dumps(
                {
                    'device': {
                        'name': 'DTU_dtu_serial',
                        'identifiers': ['hoymiles_mqtt_dtu_serial'],
                        'manufacturer': 'Hoymiles',
                    },
                    'name': 'alarm_flag',
                    'unique_id': 'hoymiles_mqtt__dtu_serial_alarm_flag',
                    'state_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                    'value_template': '{{ value_json.alarm_flag }}',
                    'device_class': 'problem',
                }
            ),
        ),
        (
            'homeassistant/sensor/102162804827/_grid_voltage/config',
            json.dumps(
                {
                    'device': {
                        'name': 'inv_102162804827',
                        'identifiers': ['hoymiles_mqtt_102162804827'],
                        'manufacturer': 'Hoymiles',
                    },
                    'name': 'grid_voltage',
                    'unique_id': 'hoymiles_mqtt__102162804827_grid_voltage',
                    'state_topic': 'homeassistant/hoymiles_mqtt/102162804827/state',
                    'value_template': '{{ value_json.grid_voltage }}',
                    'device_class': 'voltage',
                    'unit_of_measurement': 'V',
                    'state_class': 'measurement',
                }
            ),
        ),
        (
            'homeassistant/sensor/102162804827/port_3_pv_voltage/config',
            json.dumps(
                {
                    'device': {
                        'name': 'inv_102162804827',
                        'identifiers': ['hoymiles_mqtt_102162804827'],
                        'manufacturer': 'Hoymiles',
                    },
                    'name': 'port_3_pv_voltage',
                    'unique_id': 'hoymiles_mqtt_port_3_102162804827_pv_voltage',
                    'state_topic': 'homeassistant/hoymiles_mqtt/102162804827/3/state',
                    'value_template': '{{ value_json.pv_voltage }}',
                    'device_class': 'voltage',
                    'unit_of_measurement': 'V',
                    'state_class': 'measurement',
                }
            ),
        ),
    ]
