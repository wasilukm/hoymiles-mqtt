"""Hoymiles to MQTT tool."""
import argparse

import configargparse
from hoymiles_modbus.client import HoymilesModbusTCP
from hoymiles_modbus.datatypes import MicroinverterType

from hoymiles_mqtt.ha import HassMqtt
from hoymiles_mqtt.mqtt import MqttPublisher
from hoymiles_mqtt.runners import HoymilesQueryJob, run_periodic_job

DEFAULT_MQTT_PORT = 1883
DEFAULT_MODBUS_PORT = 502
DEFAULT_QUERY_PERIOD_SEC = 60
DEFAULT_MODBUS_UNIT_ID = 1

MI_ENTITIES = [
    'grid_voltage',
    'grid_frequency',
    'temperature',
    'operating_status',
    'alarm_code',
    'alarm_count',
    'link_status',
]

PORT_ENTITIES = ['pv_voltage', 'pv_current', 'pv_power', 'today_production', 'total_production']


def _parse_args() -> argparse.Namespace:
    cfg_parser = configargparse.ArgParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, prog='python3 -m hoymiles_mqtt'
    )
    cfg_parser.add('-c', '--config', required=False, type=str, is_config_file=True, help='Config file path')
    cfg_parser.add('--mqtt-broker', required=True, type=str, env_var='MQTT_BROKER', help='Address of MQTT broker')
    cfg_parser.add(
        '--mqtt-port',
        required=False,
        default=DEFAULT_MQTT_PORT,
        type=int,
        env_var='MQTT_PORT',
        help='MQTT broker port',
    )
    cfg_parser.add('--mqtt-user', required=False, type=str, env_var='MQTT_USER', help='User name for MQTT broker')
    cfg_parser.add('--mqtt-password', required=False, type=str, env_var='MQTT_PASSWORD', help='Password to MQTT broker')
    cfg_parser.add('--dtu-host', required=True, type=str, env_var='DTU_HOST', help='Address of Hoymiles DTU')
    cfg_parser.add(
        '--dtu-port', required=False, type=int, default=DEFAULT_MODBUS_PORT, env_var='DTU_PORT', help='DTU modbus port'
    )
    cfg_parser.add(
        '--modbus-unit-id',
        required=False,
        type=int,
        default=DEFAULT_MODBUS_UNIT_ID,
        env_var='MODBUS_UNIT_ID',
        help='Modbus Unit ID',
    )
    cfg_parser.add(
        '--query-period',
        required=False,
        type=int,
        default=DEFAULT_QUERY_PERIOD_SEC,
        env_var='QUERY_PERIOD',
        help='How often (in seconds) DTU shall be queried.',
    )
    cfg_parser.add(
        '--microinverter-type',
        required=False,
        type=str,
        choices=['MI', 'HM'],
        default='MI',
        env_var='MICROINVERTER_TYPE',
        help='Type od microinverters in the installation. Mixed types are not supported.',
    )
    cfg_parser.add(
        '--mi-entities',
        required=False,
        nargs="+",
        action='append',
        default=MI_ENTITIES,
        env_var='MI_ENTITIES',
        help='Microinverter entities that will be sent to MQTT. By default all entities are presented.',
    )
    cfg_parser.add(
        '--port-entities',
        required=False,
        nargs="+",
        action='append',
        default=PORT_ENTITIES,
        env_var='PORT_ENTITIES',
        help="Microinverters' port entities (in fact PV panel entities) that will be sent to MQTT. By default all "
        "entities are presented.",
    )
    cfg_parser.add(
        '--expire-after',
        required=False,
        type=int,
        default=0,
        env_var='EXPIRE_AFTER',
        help=(
            "Defines number of seconds after which DTU or microinverter entities expire, if updates are not received "
            "(for example due to communication issues). After expiry, entities become unavailable in Home Assistant."
            "By default it is 0, which means that entities never expire. When different than 0, the value shall"
            "be greater than the query period. This setting does not apply to entities that represent a total amount "
            "such as daily energy production (they never expire)."
        ),
    )
    cfg_parser.add(
        '--comm-timeout',
        required=False,
        type=int,
        default=3,
        env_var='COMM_TIMEOUT',
        help="Additional low level modbus communication parameter - request timeout.",
    )
    cfg_parser.add(
        '--comm-retries',
        required=False,
        type=int,
        default=3,
        env_var='COMM_RETRIES',
        help="Additional low level modbus communication parameter - max number of retries per request.",
    )
    cfg_parser.add(
        '--comm-retry-on-empty',
        required=False,
        type=bool,
        default=False,
        env_var='COMM_RETRY_ON_EMPTY',
        help="Additional low level modbus communication parameter - retry if received an empty response.",
    )
    cfg_parser.add(
        '--comm-close-comm-on-error',
        required=False,
        type=bool,
        default=False,
        env_var='COMM_CLOSE_COMM_ON_ERROR',
        help="Additional low level modbus communication parameter - close connection on error.",
    )
    cfg_parser.add(
        '--comm-strict',
        required=False,
        type=bool,
        default=True,
        env_var='COMM_STRICT',
        help="Additional low level modbus communication parameter - strict timing, 1.5 character between requests.",
    )
    cfg_parser.add(
        '--comm-reconnect-delay',
        required=False,
        type=int,
        default=60000 * 5,
        env_var='COMM_RECONNECT_DELAY',
        help="Additional low level modbus communication parameter - delay in milliseconds before reconnecting.",
    )
    return cfg_parser.parse_args()


options = _parse_args()
mqtt_builder = HassMqtt(
    mi_entities=options.mi_entities, port_entities=options.port_entities, expire_after=options.expire_after
)
microinverter_type = getattr(MicroinverterType, options.microinverter_type)
modbus_client = HoymilesModbusTCP(
    host=options.dtu_host, port=options.dtu_port, microinverter_type=microinverter_type, unit_id=options.modbus_unit_id
)
modbus_client.comm_params.timeout = options.comm_timeout
modbus_client.comm_params.retries = options.comm_retries
modbus_client.comm_params.retry_on_empty = options.comm_retry_on_empty
modbus_client.comm_params.close_comm_on_error = options.comm_close_comm_on_error
modbus_client.comm_params.strict = options.comm_strict
modbus_client.comm_params.reconnect_delay = options.comm_reconnect_delay

mqtt_publisher = MqttPublisher(
    mqtt_broker=options.mqtt_broker,
    mqtt_port=options.mqtt_port,
    mqtt_user=options.mqtt_user,
    mqtt_password=options.mqtt_password,
)
query_job = HoymilesQueryJob(mqtt_builder=mqtt_builder, mqtt_publisher=mqtt_publisher, modbus_client=modbus_client)
run_periodic_job(period=options.query_period, job=query_job.execute)
