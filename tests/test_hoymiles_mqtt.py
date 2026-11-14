#!/usr/bin/env python
"""Tests for `hoymiles_mqtt` package."""
import json

from hoymiles_modbus.datatypes import InverterData, PlantData

from hoymiles_mqtt import MI_ENTITIES, PORT_ENTITIES
from hoymiles_mqtt.ha import HassMqtt


def get_example_data() -> PlantData:
    """Create example PlantData."""
    example_inverters = InverterData(
        data_type=0,
        serial_number='102162804827',
        port_number=3,
        pv_voltage=1.234,
        pv_current=2.34,
        grid_voltage=22.33,
        grid_frequency=32.12,
        pv_power=40.31,
        today_production=431,
        total_production=8844,
        temperature=20.4,
        operating_status=3,
        alarm_code=0,
        alarm_count=2,
        link_status=1,
        reserved=[],
    )
    return PlantData('dtu_serial', inverters=[example_inverters])


def test_config_payload():
    """Test HassMqtt.config_payload."""
    ha = HassMqtt(mi_entities=['grid_voltage'], port_entities=['pv_voltage'])
    payload = list(ha.get_configs(get_example_data()))
    assert payload[0] == (
        'homeassistant/sensor/dtu_serial/DTU_pv_power/config',
        json.dumps(
            {
                'device': {
                    'name': 'DTU_dtu_serial',
                    'identifiers': ['hoymiles_mqtt_dtu_serial'],
                    'manufacturer': 'Hoymiles',
                },
                'name': 'pv_power',
                'unique_id': 'hoymiles_mqtt_DTU_dtu_serial_pv_power',
                'state_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                'value_template': "{{ iif(value_json.pv_power is defined, value_json.pv_power, '') }}",
                'availability_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                'availability_template': "{{ iif(value_json.pv_power is defined, 'online', 'offline') }}",
                'device_class': 'power',
                'unit_of_measurement': 'W',
                'state_class': 'measurement',
            }
        ),
    )
    assert payload[1] == (
        'homeassistant/sensor/dtu_serial/DTU_today_production/config',
        json.dumps(
            {
                'device': {
                    'name': 'DTU_dtu_serial',
                    'identifiers': ['hoymiles_mqtt_dtu_serial'],
                    'manufacturer': 'Hoymiles',
                },
                'name': 'today_production',
                'unique_id': 'hoymiles_mqtt_DTU_dtu_serial_today_production',
                'state_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                'value_template': "{{ iif(value_json.today_production is defined, value_json.today_production, '') }}",
                'availability_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                'availability_template': "{{ iif(value_json.today_production is defined, 'online', 'offline') }}",
                'device_class': 'energy',
                'unit_of_measurement': 'Wh',
                'state_class': 'total_increasing',
            }
        ),
    )
    assert payload[2] == (
        'homeassistant/sensor/dtu_serial/DTU_total_production/config',
        json.dumps(
            {
                'device': {
                    'name': 'DTU_dtu_serial',
                    'identifiers': ['hoymiles_mqtt_dtu_serial'],
                    'manufacturer': 'Hoymiles',
                },
                'name': 'total_production',
                'unique_id': 'hoymiles_mqtt_DTU_dtu_serial_total_production',
                'state_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                'value_template': "{{ iif(value_json.total_production is defined, value_json.total_production, '') }}",
                'availability_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                'availability_template': "{{ iif(value_json.total_production is defined, 'online', 'offline') }}",
                'device_class': 'energy',
                'unit_of_measurement': 'Wh',
                'state_class': 'total_increasing',
            }
        ),
    )
    assert payload[3] == (
        'homeassistant/binary_sensor/dtu_serial/DTU_alarm_flag/config',
        json.dumps(
            {
                'device': {
                    'name': 'DTU_dtu_serial',
                    'identifiers': ['hoymiles_mqtt_dtu_serial'],
                    'manufacturer': 'Hoymiles',
                },
                'name': 'alarm_flag',
                'unique_id': 'hoymiles_mqtt_DTU_dtu_serial_alarm_flag',
                'state_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                'value_template': "{{ iif(value_json.alarm_flag is defined, value_json.alarm_flag, '') }}",
                'availability_topic': 'homeassistant/hoymiles_mqtt/dtu_serial/state',
                'availability_template': "{{ iif(value_json.alarm_flag is defined, 'online', 'offline') }}",
                'device_class': 'problem',
            }
        ),
    )
    assert payload[4] == (
        'homeassistant/sensor/102162804827/inv_grid_voltage/config',
        json.dumps(
            {
                'device': {
                    'name': 'inv_102162804827',
                    'identifiers': ['hoymiles_mqtt_102162804827'],
                    'manufacturer': 'Hoymiles',
                },
                'name': 'grid_voltage',
                'unique_id': 'hoymiles_mqtt_inv_102162804827_grid_voltage',
                'state_topic': 'homeassistant/hoymiles_mqtt/102162804827/state',
                'value_template': "{{ iif(value_json.grid_voltage is defined, value_json.grid_voltage, '') }}",
                'availability_topic': 'homeassistant/hoymiles_mqtt/102162804827/state',
                'availability_template': "{{ iif(value_json.grid_voltage is defined, 'online', 'offline') }}",
                'device_class': 'voltage',
                'unit_of_measurement': 'V',
                'state_class': 'measurement',
            }
        ),
    )
    assert payload[5] == (
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
                'value_template': "{{ iif(value_json.pv_voltage is defined, value_json.pv_voltage, '') }}",
                'availability_topic': 'homeassistant/hoymiles_mqtt/102162804827/3/state',
                'availability_template': "{{ iif(value_json.pv_voltage is defined, 'online', 'offline') }}",
                'device_class': 'voltage',
                'unit_of_measurement': 'V',
                'state_class': 'measurement',
            }
        ),
    )


def test_get_states():
    """Test HassMqtt.get_states."""
    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES)
    example_data = get_example_data()
    states = list(ha.get_states(example_data))
    assert states[0] == (
        'homeassistant/hoymiles_mqtt/dtu_serial/state',
        '{"pv_power": 0.0, "today_production": 431, "total_production": 8844, "alarm_flag": "OFF"}',
    )
    assert states[1] == (
        'homeassistant/hoymiles_mqtt/102162804827/state',
        '{"grid_voltage": 22.33, "grid_frequency": 32.12, "temperature": 20.4, "operating_status": 3, '
        '"alarm_code": 0, "alarm_count": 2, "link_status": 1}',
    )
    assert states[2] == (
        'homeassistant/hoymiles_mqtt/102162804827/3/state',
        '{"pv_voltage": 1.234, "pv_current": 2.34, "pv_power": 40.31, "today_production": 431, '
        '"total_production": 8844}',
    )
    example_data.inverters[0].today_production += 1
    example_data.inverters[0].total_production += 2
    states = list(ha.get_states(example_data))
    assert states[0] == (
        'homeassistant/hoymiles_mqtt/dtu_serial/state',
        '{"pv_power": 0.0, "today_production": 432, "total_production": 8846, "alarm_flag": "OFF"}',
    )
    assert states[2] == (
        'homeassistant/hoymiles_mqtt/102162804827/3/state',
        '{"pv_voltage": 1.234, "pv_current": 2.34, "pv_power": 40.31, "today_production": 432, '
        '"total_production": 8846}',
    )


def test_zero_operating_status():
    """Verify that data is not updated when operating status is zero."""
    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES)
    example_data = get_example_data()
    list(ha.get_states(example_data))

    example_data.inverters[0].operating_status = 0
    example_data.inverters[0].today_production += 1
    example_data.inverters[0].total_production += 2
    states = list(ha.get_states(example_data))
    assert states[0] == (
        'homeassistant/hoymiles_mqtt/dtu_serial/state',
        '{"pv_power": 0.0, "today_production": 431, "total_production": 8844, "alarm_flag": "OFF"}',
    )


def test_production_drop():
    """Verify that drop in production is ignored."""
    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES)
    example_data = get_example_data()
    list(ha.get_states(example_data))
    example_data.inverters[0].today_production -= 1
    example_data.inverters[0].total_production -= 2
    states = list(ha.get_states(example_data))
    assert states[0] == (
        'homeassistant/hoymiles_mqtt/dtu_serial/state',
        '{"pv_power": 0.0, "today_production": 431, "total_production": 8844, "alarm_flag": "OFF"}',
    )
    assert states[2] == (
        'homeassistant/hoymiles_mqtt/102162804827/3/state',
        '{"pv_voltage": 1.234, "pv_current": 2.34, "pv_power": 40.31, "today_production": 431, '
        '"total_production": 8844}',
    )


def get_two_port_data() -> PlantData:
    """Create example PlantData with two ports."""
    plant_data = get_example_data()
    second_port = get_example_data().inverters[0]
    second_port.port_number = 4
    second_port.today_production = 100
    second_port.total_production = 1000
    plant_data.inverters.append(second_port)
    return plant_data


def get_sleeping_data(plant_data: PlantData) -> PlantData:
    """Make all inverters look like at night (no valid data)."""
    for inverter in plant_data.inverters:
        inverter.operating_status = 0
        inverter.today_production = 0
        inverter.total_production = 0
    return plant_data


def test_cache_survives_restart(tmp_path):
    """Verify that cached production is restored from the cache file after a restart."""
    cache_file = tmp_path / 'cache.json'
    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    list(ha.get_states(get_two_port_data()))
    assert [path.name for path in tmp_path.iterdir()] == ['cache.json']

    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    states = list(ha.get_states(get_sleeping_data(get_two_port_data())))
    assert json.loads(states[0][1]) == {
        'pv_power': 0.0,
        'today_production': 531,
        'total_production': 9844,
        'alarm_flag': 'OFF',
    }


def test_cache_restart_inverters_wake_up_one_by_one(tmp_path):
    """Verify that total production does not drop when inverters wake up one after another after a restart."""
    cache_file = tmp_path / 'cache.json'
    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    list(ha.get_states(get_two_port_data()))

    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    plant_data = get_sleeping_data(get_two_port_data())
    plant_data.inverters[0].operating_status = 3
    plant_data.inverters[0].total_production = 8850
    states = list(ha.get_states(plant_data))
    assert json.loads(states[0][1])['total_production'] == 9850


def test_cache_today_production_dropped_on_new_day(tmp_path):
    """Verify that today production from the cache file is ignored when saved on another day."""
    cache_file = tmp_path / 'cache.json'
    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    list(ha.get_states(get_two_port_data()))
    content = json.loads(cache_file.read_text())
    content['date'] = '2000-01-01'
    cache_file.write_text(json.dumps(content))

    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    states = list(ha.get_states(get_sleeping_data(get_two_port_data())))
    assert json.loads(states[0][1]) == {'pv_power': 0.0, 'total_production': 9844, 'alarm_flag': 'OFF'}


def test_cache_clear_production_today_is_saved(tmp_path):
    """Verify that clearing today production is reflected in the cache file."""
    cache_file = tmp_path / 'cache.json'
    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    list(ha.get_states(get_two_port_data()))
    ha.clear_production_today()
    list(ha.get_states(get_sleeping_data(get_two_port_data())))

    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    states = list(ha.get_states(get_sleeping_data(get_two_port_data())))
    assert json.loads(states[0][1]) == {'pv_power': 0.0, 'total_production': 9844, 'alarm_flag': 'OFF'}


def test_cache_file_corrupted(tmp_path):
    """Verify that a corrupted cache file is ignored and then overwritten."""
    cache_file = tmp_path / 'cache.json'
    cache_file.write_text('{not a json')
    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    states = list(ha.get_states(get_two_port_data()))
    assert json.loads(states[0][1])['total_production'] == 9844
    assert json.loads(cache_file.read_text())['total_production'] == {'102162804827:3': 8844, '102162804827:4': 1000}


def test_total_production_not_published_until_all_ports_reported():
    """Verify that DTU total production is withheld until every port reported a valid value."""
    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES)
    plant_data = get_two_port_data()
    plant_data.inverters[1].operating_status = 0
    states = list(ha.get_states(plant_data))
    assert json.loads(states[0][1]) == {'pv_power': 0.0, 'today_production': 431, 'alarm_flag': 'OFF'}

    states = list(ha.get_states(get_two_port_data()))
    assert json.loads(states[0][1])['total_production'] == 9844


def test_total_production_never_lower_than_published(tmp_path):
    """Verify that DTU total production lower than the last published one is not published."""
    cache_file = tmp_path / 'cache.json'
    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    list(ha.get_states(get_two_port_data()))
    content = json.loads(cache_file.read_text())
    assert content['published_total_production'] == 9844
    content['total_production']['102162804827:4'] = 10
    cache_file.write_text(json.dumps(content))

    ha = HassMqtt(mi_entities=MI_ENTITIES, port_entities=PORT_ENTITIES, cache_file=str(cache_file))
    states = list(ha.get_states(get_sleeping_data(get_two_port_data())))
    assert 'total_production' not in json.loads(states[0][1])

    states = list(ha.get_states(get_two_port_data()))
    assert json.loads(states[0][1])['total_production'] == 9844
