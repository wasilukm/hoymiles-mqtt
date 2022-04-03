import json
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

from hoymiles_modbus.datatypes import PlantData

PLATFORM_SENSOR = 'sensor'
PLATFORM_BINARY_SENSOR = 'binary_sensor'

DEVICE_CLASS_VOLTAGE = 'voltage'
DEVICE_CLASS_CURRENT = 'current'
DEVICE_CLASS_FREQUENCY = 'frequency'
DEVICE_CLASS_POWER = 'power'
DEVICE_CLASS_ENERGY = 'energy'
DEVICE_CLASS_TEMPERATURE = 'temperature'

STATE_CLASS_MEASUREMENT = 'measurement'
STATE_CLASS_TOTAL = 'total'

UNIT_VOLTS = 'V'
UNIT_AMPERES = 'A'
UNIT_HERTZ = 'Hz'
UNIT_CELSIUS = '°C'
UNIT_WATS = 'W'
UNIT_WATS_PER_HOUR = 'Wh'


@dataclass
class EntityDescription:
    platform: str = PLATFORM_SENSOR
    device_class: Optional[str] = None
    unit: Optional[str] = None
    state_class: Optional[str] = None


MicroinverterEntities = {
    'port_number': EntityDescription(),
    'pv_voltage': EntityDescription(
        device_class=DEVICE_CLASS_VOLTAGE, unit=UNIT_VOLTS, state_class=STATE_CLASS_MEASUREMENT
    ),
    'pv_current': EntityDescription(
        device_class=DEVICE_CLASS_CURRENT, unit=UNIT_AMPERES, state_class=STATE_CLASS_MEASUREMENT
    ),
    'grid_voltage': EntityDescription(
        device_class=DEVICE_CLASS_VOLTAGE, unit=UNIT_VOLTS, state_class=STATE_CLASS_MEASUREMENT
    ),
    'grid_frequency': EntityDescription(
        device_class=DEVICE_CLASS_FREQUENCY, unit=UNIT_HERTZ, state_class=STATE_CLASS_MEASUREMENT
    ),
    'pv_power': EntityDescription(device_class=DEVICE_CLASS_POWER, unit=UNIT_WATS, state_class=STATE_CLASS_MEASUREMENT),
    'today_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY, unit=UNIT_WATS_PER_HOUR, state_class=STATE_CLASS_TOTAL
    ),
    'total_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY, unit=UNIT_WATS_PER_HOUR, state_class=STATE_CLASS_TOTAL
    ),
    'temperature': EntityDescription(
        device_class=DEVICE_CLASS_TEMPERATURE, unit=UNIT_CELSIUS, state_class=STATE_CLASS_MEASUREMENT
    ),
    'operating_status': EntityDescription(),
    'alarm_code': EntityDescription(),
    'alarm_count': EntityDescription(),
    'link_status': EntityDescription(),
}

DtuEntities = {
    'pv_power': EntityDescription(device_class=DEVICE_CLASS_POWER, unit=UNIT_WATS, state_class=STATE_CLASS_MEASUREMENT),
    'today_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY, unit=UNIT_WATS_PER_HOUR, state_class=STATE_CLASS_TOTAL
    ),
    'total_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY, unit=UNIT_WATS_PER_HOUR, state_class=STATE_CLASS_TOTAL
    ),
    'alarm_flag': EntityDescription(platform=PLATFORM_BINARY_SENSOR),
}


class HassMqtt:
    def __init__(self, hide_microinverters=False):
        self._hide_microinverters = hide_microinverters
        self._state_topics = {}
        self._config_topics = {}

    def _get_config_topic(self, platform: str, device_serial: str, entity_name):
        return f"homeassistant/{platform}/{device_serial}/{entity_name}/config"

    def _get_state_topic(self, device_serial: str):
        return f"homeassistant/hoymiles_mqtt/{device_serial}/state"

    def _get_config_payloads(
        self, device_name: str, device_serial_number, entity_definitions: Dict[str, EntityDescription]
    ) -> Iterable[Tuple[str, str]]:
        for entity_name, entity_definition in entity_definitions.items():
            config_payload = {
                "device": {
                    "name": f"{device_name}_{device_serial_number}",
                    "identifiers": [f"hoymiles_mqtt_{device_serial_number}"],
                    "manufacturer": "Hoymiles",
                },
                "name": f"{device_name}_{device_serial_number}_{entity_name}",
                "unique_id": f"hoymiles_mqtt_{device_serial_number}_{entity_name}",
                "state_topic": self._get_state_topic(device_serial_number),
                "value_template": "{{ value_json.%s }}" % entity_name,
            }
            if entity_definition.device_class:
                config_payload['device_class'] = entity_definition.device_class
            if entity_definition.unit:
                config_payload['unit_of_measurement'] = entity_definition.unit
            if entity_definition.state_class:
                config_payload['state_class'] = entity_definition.state_class
            config_topic = self._get_config_topic(entity_definition.platform, device_serial_number, entity_name)
            yield config_topic, json.dumps(config_payload)

    def get_configs(self, plant_data: PlantData):
        for topic, payload in self._get_config_payloads('DTU', plant_data.dtu, DtuEntities):
            yield topic, payload
        if not self._hide_microinverters:
            for microinverter_data in plant_data.microinverter_data:
                for topic, payload in self._get_config_payloads(
                    'Microinverter', microinverter_data.serial_number, MicroinverterEntities
                ):
                    yield topic, payload

    def _get_state(self, device_serial: str, entity_definitions: Dict[str, EntityDescription], entity_data):
        values = {}
        for entity_name, _ in entity_definitions.items():
            values[entity_name] = str(getattr(entity_data, entity_name))
            payload = json.dumps(values)
            state_topic = self._get_state_topic(device_serial)
        return state_topic, payload

    def get_states(self, plant_data: PlantData):
        yield self._get_state(plant_data.dtu, DtuEntities, plant_data)
        if not self._hide_microinverters:
            for microinverter_data in plant_data.microinverter_data:
                yield self._get_state(microinverter_data.serial_number, MicroinverterEntities, microinverter_data)
