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


def _parse_args() -> argparse.Namespace:
    cfg_parser = configargparse.ArgParser()
    cfg_parser.add('-c', '--config', required=False, type=str, is_config_file=True, help='Config file path')
    cfg_parser.add('--mqtt-broker', required=True, type=str, env_var='MQTT_BROKER', help='Address of MQTT broker')
    cfg_parser.add(
        '--mqtt-port',
        required=False,
        default=DEFAULT_MQTT_PORT,
        type=int,
        env_var='MQTT_PORT',
        help=f'MQTT broker port (default: {DEFAULT_MQTT_PORT}',
    )
    cfg_parser.add('--mqtt-user', required=False, type=str, env_var='MQTT_USER', help='User name for MQTT broker')
    cfg_parser.add('--mqtt-password', required=False, type=str, env_var='MQTT_PASSWORD', help='Password to MQTT broker')
    cfg_parser.add('--dtu-host', required=True, type=str, env_var='DTU_HOST', help='Address of Hoymiles DTU')
    cfg_parser.add(
        '--dtu-port', required=False, type=int, default=DEFAULT_MODBUS_PORT, env_var='DTU_PORT', help='DTU modbus port'
    )
    cfg_parser.add('--query-period', required=False, type=int, default=DEFAULT_QUERY_PERIOD_SEC, env_var='QUERY_PERIOD')
    cfg_parser.add(
        '--microinverter-type',
        required=False,
        type=str,
        choices=['MI', 'HM'],
        default='MI',
        env_var='MICROINVERTER_TYPE',
    )
    cfg_parser.add(
        '--hide-microinverters',
        required=False,
        type=bool,
        default=False,
        env_var='HIDE_MICROINVERTERS',
        help='If true then detailed microinverter date will not be send to MQTT broker',
    )
    return cfg_parser.parse_args()


options = _parse_args()
mqtt_builder = HassMqtt(hide_microinverters=options.hide_microinverters)
microinverter_type = getattr(MicroinverterType, options.microinverter_type)
modbus_client = HoymilesModbusTCP(host=options.dtu_host, port=options.dtu_port, microinverter_type=microinverter_type)
mqtt_publisher = MqttPublisher(
    mqtt_broker=options.mqtt_broker,
    mqtt_port=options.mqtt_port,
    mqtt_user=options.mqtt_user,
    mqtt_password=options.mqtt_password,
)
query_job = HoymilesQueryJob(mqtt_builder=mqtt_builder, mqtt_publisher=mqtt_publisher, modbus_client=modbus_client)
run_periodic_job(period=options.query_period, job=query_job.execute)