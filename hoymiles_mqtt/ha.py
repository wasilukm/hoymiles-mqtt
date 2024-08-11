"""MQTT message builders for Home Assistant."""
import json
import logging
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Tuple
import time

from hoymiles_modbus.datatypes import PlantData

logger = logging.getLogger(__name__)

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


def _ignore_when_zero(data, entity_name):
    return getattr(data, entity_name) == ZERO


def _ignore_when_zero_operating_status(data, _):
    return _ignore_when_zero(data, 'operating_status')


@dataclass
class EntityDescription:
    """Common entity properties."""

    platform: str = PLATFORM_SENSOR
    device_class: Optional[str] = None
    unit: Optional[str] = None
    state_class: Optional[str] = None
    ignore_rule: Optional[Callable] = None
    expire: Optional[bool] = True
    value_converter: Optional[Callable] = None


MicroinverterEntities = {
    'grid_voltage': EntityDescription(
        device_class=DEVICE_CLASS_VOLTAGE,
        unit=UNIT_VOLTS,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'grid_frequency': EntityDescription(
        device_class=DEVICE_CLASS_FREQUENCY,
        unit=UNIT_HERTZ,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'temperature': EntityDescription(
        device_class=DEVICE_CLASS_TEMPERATURE,
        unit=UNIT_CELSIUS,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'operating_status': EntityDescription(),
    'alarm_code': EntityDescription(),
    'alarm_count': EntityDescription(),
    'link_status': EntityDescription(),
}

PortEntities = {
    'pv_voltage': EntityDescription(
        device_class=DEVICE_CLASS_VOLTAGE,
        unit=UNIT_VOLTS,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'pv_current': EntityDescription(
        device_class=DEVICE_CLASS_CURRENT,
        unit=UNIT_AMPERES,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
    'pv_power': EntityDescription(
        device_class=DEVICE_CLASS_POWER,
        unit=UNIT_WATS,
        state_class=STATE_CLASS_MEASUREMENT,
        value_converter=float,
        ignore_rule=_ignore_when_zero_operating_status,
    ),
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
    'pv_power': EntityDescription(
        device_class=DEVICE_CLASS_POWER, unit=UNIT_WATS, state_class=STATE_CLASS_MEASUREMENT, value_converter=float
    ),
    'today_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY,
        unit=UNIT_WATS_PER_HOUR,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        ignore_rule=_ignore_when_zero,
        expire=False,
    ),
    'total_production': EntityDescription(
        device_class=DEVICE_CLASS_ENERGY,
        unit=UNIT_WATS_PER_HOUR,
        state_class=STATE_CLASS_TOTAL_INCREASING,
        ignore_rule=_ignore_when_zero,
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

    RESET_HOUR: int = 22

    def __init__(
        self, mi_entities: List[str], port_entities: List[str],
        post_process: bool = True, expire_after: int = 0
    ) -> None:
        """Initialize the object.

        Arguments:
            mi_entities: names of microinverter entities that shall be handled by the builder
            port_entities: names of microinverter port entities that shall be handled by the builder
            post_process: if to cache energy production
            expire_after: number of seconds after which an entity state should expire. This setting is added to the
                          entity configuration. Applied only when `expire` flag is set in the entity description.

        """
        self._logger = logging.getLogger(self.__class__.__name__)
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
        self._last_daily_reset: Optional[time.struct_time] = None

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
        port_prefix = f'port_{port}' if port is not None else ''
        entity_prefix = port_prefix if port_prefix else device_name
        for entity_name, entity_definition in entity_definitions.items():
            state_topic = self._get_state_topic(device_serial_number, port)
            config_payload = {
                "device": {
                    "name": f"{device_name}_{device_serial_number}",
                    "identifiers": [f"hoymiles_mqtt_{device_serial_number}"],
                    "manufacturer": "Hoymiles",
                },
                "name": f'{port_prefix}_{entity_name}' if port_prefix else entity_name,
                "unique_id": f"hoymiles_mqtt_{entity_prefix}_{device_serial_number}_{entity_name}",
                "state_topic": state_topic,
                "value_template": f"{{{{ iif(value_json.{entity_name} is defined, value_json.{entity_name}, '') }}}}",
                "availability_topic": state_topic,
                "availability_template": f"{{{{ iif(value_json.{entity_name} is defined, 'online', 'offline') }}}}",
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
        self._logger.debug('Clear today production cache.')
        self._prod_today_cache = {}
        self._last_daily_reset = time.localtime()

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
            if description.ignore_rule and description.ignore_rule(entity_data, entity_name):
                continue
            if description.value_converter:
                value = description.value_converter(value)
            values[entity_name] = value
        payload = json.dumps(values)
        state_topic = self._get_state_topic(device_serial, port)
        return state_topic, payload

    def _update_cache(self, plant_data: PlantData) -> None:
        """
        Update plant data to cache.
        While doing the update, take daily production reset occurring around hour 22 into account.
        :param plant_data: Plant production data as retrieved from DTU
        :return: None, plant_data will be altered, if necessary
        """
        microinverters = {}
        data_to_cache = {}
        cache_failure_cnt = 0
        for idx, microinverter in enumerate(plant_data.microinverter_data):
            microinverters[idx] = microinverter
            if microinverter.operating_status > 0:
                cache_key = (microinverter.serial_number, microinverter.port_number)

                # Today data will be handled later
                data_to_cache[idx] = microinverter.today_production
                if (cache_key in self._prod_today_cache and
                    microinverter.today_production < self._prod_today_cache[cache_key]):
                    cache_failure_cnt += 1
                    logger.debug("Today production cache failure detected! Microinverter %s, port %d",
                                 microinverter.serial_number, microinverter.port_number)

                # Total data is handled on this go as there is no daily reset on it
                if cache_key not in self._prod_total_cache:
                    self._prod_total_cache[cache_key] = ZERO
                if microinverter.total_production >= self._prod_total_cache[cache_key]:
                    self._prod_total_cache[cache_key] = microinverter.total_production
                else:
                    self._logger.warning(
                        'Total production for microinverter %s, port %d '
                        'is smaller (%d) than cached (%d). Using cached value.',
                        microinverter.serial_number, microinverter.port_number,
                        microinverter.total_production, self._prod_total_cache[cache_key]
                    )
                    microinverter.total_production = self._prod_total_cache[cache_key]

        # Estimate if today production data was retrieved.
        # Reset today production cache only once per day.
        now = time.localtime()
        running_hour = now.tm_hour
        running_during_reset_hour = running_hour == HassMqtt.RESET_HOUR
        running_after_reset_hour = running_hour > HassMqtt.RESET_HOUR
        if not data_to_cache:
            # No today production data received.
            # Maybe it's after sundown.
            if ((running_during_reset_hour or running_after_reset_hour) and
                (not self._last_daily_reset or
                self._last_daily_reset.tm_yday < now.tm_yday)):
                logger.info("No production data received. Today production reset hour past. Reset cache.")
                self.clear_production_today()
            return

        # Depending on DTU's geographical location, on high latitudes, during summer there will be production
        # during reset hour of 22. Obviously, this doesn't happen on lower latitudes or other seasons.
        # If all data points failed caching, assume reset hour passed on all DTUs.
        # Note: A solar panel installation typically contains multiple DTUs. Any DTU can reset daily or not.
        if (cache_failure_cnt == len(data_to_cache) and
            running_during_reset_hour and
            (not self._last_daily_reset or
            self._last_daily_reset.tm_yday < now.tm_yday)):
            logger.info("Today production reset detected")
            self.clear_production_today()
        else:
            logger.warning("Debug: %d data points, %d failures, running during reset hour: %d",
                           len(data_to_cache), cache_failure_cnt,
                           running_during_reset_hour)

        # Update today production cache or alter return value.
        for idx, today_production in data_to_cache.items():
            microinverter = microinverters[idx]
            cache_key = (microinverter.serial_number, microinverter.port_number)

            if cache_key not in self._prod_today_cache:
                self._prod_today_cache[cache_key] = ZERO
            if today_production >= self._prod_today_cache[cache_key]:
                self._prod_today_cache[cache_key] = today_production
            else:
                self._logger.warning(
                    'Today production for microinverter %s, port %d '
                    'is smaller (%d) than cached (%d). Using cached value.',
                    cache_key[0], cache_key[1],
                    today_production, self._prod_today_cache[cache_key]
                )
                microinverter.today_production = self._prod_today_cache[cache_key]

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
