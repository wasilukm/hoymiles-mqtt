"""Hoymiles to MQTT tool."""

import argparse
import logging
import sys

import configargparse
from hoymiles_modbus.client import HoymilesModbusTCP

from hoymiles_mqtt import MI_ENTITIES, PORT_ENTITIES, _main_logger
from hoymiles_mqtt.ha import HassMqtt
from hoymiles_mqtt.mqtt import MqttPublisher
from hoymiles_mqtt.runners import HoymilesQueryJob, run_periodic_job

DEFAULT_MQTT_PORT = 1883
DEFAULT_MODBUS_PORT = 502
DEFAULT_QUERY_PERIOD_SEC = 60
DEFAULT_MODBUS_UNIT_ID = 1

logger = _main_logger.getChild('__main__')


def _setup_logger(options: configargparse.Namespace) -> None:
    handlers: list[logging.Handler] = []
    if options.log_to_console:
        handlers.append(logging.StreamHandler(sys.stdout))
    if options.log_file:
        handlers.append(logging.FileHandler(options.log_file))

    logging.basicConfig(
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  [%(name)s] %(message)s",
        handlers=handlers,
    )
    _main_logger.setLevel(options.log_level)


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
        help='MQTT broker port. Note that when using TLS connection you may need to specify port 8883',
    )
    cfg_parser.add('--mqtt-user', required=False, type=str, env_var='MQTT_USER', help='User name for MQTT broker')
    cfg_parser.add('--mqtt-password', required=False, type=str, env_var='MQTT_PASSWORD', help='Password to MQTT broker')
    cfg_parser.add(
        '--mqtt-tls',
        required=False,
        default=False,
        action='store_true',
        env_var='MQTT_TLS',
        help='MQTT TLS connection',
    )
    cfg_parser.add(
        '--mqtt-tls-insecure',
        required=False,
        default=False,
        action='store_true',
        env_var='MQTT_TLS_INSECURE',
        help=(
            'MQTT TLS insecure connection (only relevant when using with the '
            '--mqtt-tls option). Do not use in production environments.'
        ),
    )
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
        '--mi-entities',
        required=False,
        nargs="+",
        default=MI_ENTITIES,
        env_var='MI_ENTITIES',
        help='Microinverter entities that will be sent to MQTT. By default all entities are presented.',
    )
    cfg_parser.add(
        '--port-entities',
        required=False,
        nargs="+",
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
        '--comm-reconnect-delay',
        required=False,
        type=float,
        default=0,
        env_var='COMM_RECONNECT_DELAY',
        help="Additional low level modbus communication parameter - Minimum "
        "delay in seconds.milliseconds before reconnecting. "
        "Doubles automatically with each unsuccessful connect, from "
        "**reconnect_delay** to **reconnect_delay_max**. "
        "Default is 0 which means that reconnecting is disabled.",
    )
    cfg_parser.add(
        '--comm-reconnect-delay-max',
        required=False,
        type=float,
        default=300,
        env_var='COMM_RECONNECT_DELAY_MAX',
        help="Additional low level modbus communication parameter - maximum "
        "delay in seconds.milliseconds before reconnecting.",
    )
    cfg_parser.add(
        '--log-level',
        required=False,
        type=str,
        default='WARNING',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        env_var='LOG_LEVEL',
        help="Python logger log level. Default: WARNING",
    )
    cfg_parser.add(
        '--log-file',
        required=False,
        type=str,
        default=None,
        env_var='LOG_FILE',
        help="Python logger log file. Default: not writing into a file",
    )
    cfg_parser.add(
        '--log-to-console',
        required=False,
        action='store_true',
        default=False,
        env_var='LOG_TO_CONSOLE',
        help="Enable logging to console.",
    )
    return cfg_parser.parse_args()


def main():
    """Main entry point."""
    options = _parse_args()
    _setup_logger(options)
    mqtt_builder = HassMqtt(
        mi_entities=options.mi_entities, port_entities=options.port_entities, expire_after=options.expire_after
    )
    modbus_client = HoymilesModbusTCP(
        host=options.dtu_host,
        port=options.dtu_port,
        unit_id=options.modbus_unit_id,
    )
    modbus_client.comm_params.timeout = options.comm_timeout
    modbus_client.comm_params.retries = options.comm_retries
    modbus_client.comm_params.reconnect_delay = options.comm_reconnect_delay
    modbus_client.comm_params.reconnect_delay = options.comm_reconnect_delay_max

    mqtt_publisher = MqttPublisher(
        mqtt_broker=options.mqtt_broker,
        mqtt_port=options.mqtt_port,
        mqtt_user=options.mqtt_user,
        mqtt_password=options.mqtt_password,
        mqtt_tls=options.mqtt_tls,
        mqtt_tls_insecure=options.mqtt_tls_insecure,
    )
    query_job = HoymilesQueryJob(mqtt_builder=mqtt_builder, mqtt_publisher=mqtt_publisher, modbus_client=modbus_client)
    run_periodic_job(period=options.query_period, job=query_job.execute)


if __name__ == '__main__':
    main()
