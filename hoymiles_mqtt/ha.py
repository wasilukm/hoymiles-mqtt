"""MQTT message builders for Home Assistant."""
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from hoymiles_modbus.datatypes import PlantData

PLATFORM_SENSOR = 'sensor'
PLATFORM_BINARY_SENSOR = 'binary_sensor'

DEVICE_CLASS_VOLTAGE = 'voltage'
DEVICE_CLASS_CURRENT = 'current'
DEVICE_CLASS_FREQUENCY = 'frequency'
DEVICE_CLASS_POWER = 'power'
DEVICE_CLASS_ENERGY = 'energy'
DEVICE_CLASS_TEMPERATURE = 'temperature'
DEVICE_CLASS_PROBLEM = 'problem'

STATE_CLASS_MEASUREMENT = 'measurement'
STATE_CLASS_TOTAL_INCREASING = 'total_increasing'

UNIT_VOLTS = 'V'
UNIT_AMPERES = 'A'
UNIT_HERTZ = 'Hz'
UNIT_CELSIUS = '°C'
UNIT_WATS = 'W'
UNIT_WATS_PER_HOUR = 'Wh'

ZERO = 0


@dataclass
class EntityDescription:
    """Common entity properties."""

    platform: str = PLATFORM_SENSOR
    device_class: Optional[str] = None
    unit: Optional[str] = None
    state_class: Optional[str] = None
    ignored_value: Optional[Any] = None
    expire: Optional[bool] = True
    value_converter: Optional[Callable] = None


MicroinverterEntities = {
    'grid_voltage': EntityDescription(
        device_class=DEVICE_CLASS_VOLTAGE, unit=UNIT_VOLTS, state_class=STATE_CLASS_MEASUREMENT
    ),
    'grid_frequency': EntityDescription(
        device_class=DEVICE_CLASS_FREQUENCY, unit=UNIT_HERTZ, state_class=STATE_CLASS_MEASUREMENT
    ),
    'temperature': EntityDescription(
        device_class=DEVICE_CLASS_TEMPERATURE, unit=UNIT_CELSIUS, state_class=STATE_CLASS_MEASUREMENT
    ),
    'operating_status': EntityDescription(),
    'alarm_code': EntityDescription(),
    'alarm_count': EntityDescription(),
    'link_status': EntityDescription(),
}

PortEntities = {
    'pv_voltage': EntityDescription(
        device_class=DEVICE_CLASS_VOLTAGE, unit=UNIT_VOLTS, state_class=STATE_CLASS_MEASUREMENT
    ),
    'pv_current': EntityDescription(
        device_class=DEVICE_CLASS_CURRENT, unit=UNIT_AMPERES, state_class=STATE_CLASS_MEASUREMENT
    ),
    'pv_power': EntityDescription(device_class=DEVICE_CLASS_POWER, unit=UNIT_WATS, state_class=STATE_CLASS_MEASUREMENT),
    'today_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY,
        unit=UNIT_WATS_PER_HOUR,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        expire=False,
    ),
    'total_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY,
        unit=UNIT_WATS_PER_HOUR,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        expire=False,
    ),
}

DtuEntities = {
    'pv_power': EntityDescription(device_class=DEVICE_CLASS_POWER, unit=UNIT_WATS, state_class=STATE_CLASS_MEASUREMENT),
    'today_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY,
        unit=UNIT_WATS_PER_HOUR,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        ignored_value=ZERO,
        expire=False,
    ),
    'total_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY,
        unit=UNIT_WATS_PER_HOUR,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        ignored_value=ZERO,
        expire=False,
    ),
    'alarm_flag': EntityDescription(
        platform=PLATFORM_BINARY_SENSOR,
        device_class=DEVICE_CLASS_PROBLEM,
        value_converter=lambda x: 'ON' if x else 'OFF',
    ),
}


class HassMqtt:
    """MQTT message builder for Home Assistant."""

    def __init__(
        self, mi_entities: List[str], port_entities: List[str], post_process: bool = True, expire_after: int = 0
    ) -> None:
        """Initialize the object.

        Arguments:
            mi_entities: names of microinverter entities that shall be handled by the builder
            port_entities: names of microinverter port entities that shall be handled by the builder
            post_process: if to cache energy production
            expire_after: number of seconds after which an entity state should expire. This setting is added to the
                          entity configuration. Applied only when `expire` flag is set in the entity description.

        """
        self._state_topics: Dict = {}
        self._config_topics: Dict = {}
        self._post_process: bool = post_process
        self._expire_after: int = expire_after
        self._prod_today_cache: Dict[Tuple[str, int], int] = {}
        self._prod_total_cache: Dict[Tuple[str, int], int] = {}
        self._mi_entities: Dict[str, EntityDescription] = {}
        self._port_entities: Dict[str, EntityDescription] = {}
        for entity_name, description in MicroinverterEntities.items():
            if entity_name in mi_entities:
                self._mi_entities[entity_name] = description
        for entity_name, description in PortEntities.items():
            if entity_name in port_entities:
                self._port_entities[entity_name] = description

    @staticmethod
    def _get_config_topic(platform: str, device_serial: str, entity_name) -> str:
        return f"homeassistant/{platform}/{device_serial}/{entity_name}/config"

    @staticmethod
    def _get_state_topic(device_serial: str, port: Optional[int]) -> str:
        if port is not None:
            sub_topic = f'{device_serial}/{port}'
        else:
            sub_topic = device_serial
        return f"homeassistant/hoymiles_mqtt/{sub_topic}/state"

    def _get_config_payloads(
        self,
        device_name: str,
        device_serial_number,
        entity_definitions: Dict[str, EntityDescription],
        port: Optional[int] = None,
    ) -> Iterable[Tuple[str, str]]:
        if port is not None:
            entity_prefix = f'port_{port}'
        else:
            entity_prefix = device_name
        for entity_name, entity_definition in entity_definitions.items():
            config_payload = {
                "device": {
                    "name": f"{device_name}_{device_serial_number}",
                    "identifiers": [f"hoymiles_mqtt_{device_serial_number}"],
                    "manufacturer": "Hoymiles",
                },
                "name": f"{entity_prefix}_{device_serial_number}_{entity_name}",
                "unique_id": f"hoymiles_mqtt_{entity_prefix}_{device_serial_number}_{entity_name}",
                "state_topic": self._get_state_topic(device_serial_number, port),
                "value_template": "{{ value_json.%s }}" % entity_name,
            }
            if entity_definition.device_class:
                config_payload['device_class'] = entity_definition.device_class
            if entity_definition.unit:
                config_payload['unit_of_measurement'] = entity_definition.unit
            if entity_definition.state_class:
                config_payload['state_class'] = entity_definition.state_class
            if entity_definition.expire and self._expire_after:
                config_payload['expire_after'] = str(self._expire_after)
            config_topic = self._get_config_topic(
                entity_definition.platform, device_serial_number, f'{entity_prefix}_{entity_name}'
            )
            yield config_topic, json.dumps(config_payload)

    def clear_production_today(self) -> None:
        """Clear todays' energy production."""
        self._prod_today_cache = {}

    def get_configs(self, plant_data: PlantData) -> Iterable[Tuple[str, str]]:
        """Get MQTT config messages for given data from DTU.

        Arguments:
            plant_data: data from DTU

        """
        for topic, payload in self._get_config_payloads('DTU', plant_data.dtu, DtuEntities):
            yield topic, payload
        for microinverter_data in plant_data.microinverter_data:
            for topic, payload in self._get_config_payloads('inv', microinverter_data.serial_number, self._mi_entities):
                yield topic, payload
            for topic, payload in self._get_config_payloads(
                'inv',
                microinverter_data.serial_number,
                self._port_entities,
                microinverter_data.port_number,
            ):
                yield topic, payload

    def _get_state(
        self,
        device_serial: str,
        entity_definitions: Dict[str, EntityDescription],
        entity_data,
        port: Optional[int] = None,
    ) -> Tuple[str, str]:
        values = {}
        for entity_name, description in entity_definitions.items():
            value = getattr(entity_data, entity_name)
            if description.ignored_value is not None and value == description.ignored_value:
                continue
            if description.value_converter:
                value = description.value_converter(value)
            values[entity_name] = str(value)
        payload = json.dumps(values)
        state_topic = self._get_state_topic(device_serial, port)
        return state_topic, payload

    def _update_cache(self, plant_data: PlantData) -> None:
        for microinverter in plant_data.microinverter_data:
            cache_key = (microinverter.serial_number, microinverter.port_number)
            if cache_key not in self._prod_today_cache:
                self._prod_today_cache[cache_key] = ZERO
            if cache_key not in self._prod_total_cache:
                self._prod_total_cache[cache_key] = ZERO
            if microinverter.link_status:
                self._prod_today_cache[cache_key] = microinverter.today_production
                self._prod_total_cache[cache_key] = microinverter.total_production

    def _process_plant_data(self, plant_data: PlantData) -> None:
        self._update_cache(plant_data)
        plant_data.today_production = sum(self._prod_today_cache.values()) if self._prod_today_cache else ZERO
        plant_data.total_production = sum(self._prod_total_cache.values()) if self._prod_total_cache else ZERO

    def get_states(self, plant_data: PlantData) -> Iterable[Tuple[str, str]]:
        """Get MQTT message for DTU data.

        Arguments:
            plant_data: data from DTU

        """
        if self._post_process:
            self._process_plant_data(plant_data)
        yield self._get_state(plant_data.dtu, DtuEntities, plant_data)
        known_serials = []
        for microinverter_data in plant_data.microinverter_data:
            if microinverter_data.serial_number not in known_serials:
                known_serials.append(microinverter_data.serial_number)
                yield self._get_state(microinverter_data.serial_number, self._mi_entities, microinverter_data)
            yield self._get_state(
                microinverter_data.serial_number,
                self._port_entities,
                microinverter_data,
                microinverter_data.port_number,
            )
