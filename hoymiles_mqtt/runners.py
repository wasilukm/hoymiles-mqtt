"""Runners."""

import logging
import threading
import time
from typing import Callable

from hoymiles_modbus.client import HoymilesModbusTCP
from pymodbus import exceptions as pymodbus_exceptions

from hoymiles_mqtt.ha import HassMqtt
from hoymiles_mqtt.mqtt import MqttPublisher

logger = logging.getLogger(__name__)

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
        if not is_acquired:
            return

        if time.localtime().tm_hour == RESET_HOUR:
            self._mqtt_builder.clear_production_today()
            logger.info("Reset hour reached")

        logger.debug("Read data from DTU")
        plant_data = None
        publish_count = 0
        try:
            plant_data = self._modbus_client.plant_data
            logger.debug("Received data from DTU")
        except pymodbus_exceptions.ModbusIOException as exc:
            if 'No response received, expected at least 8 bytes' in exc.message:
                logger.warning("Failed to read data from DTU via Modbus. Will retry.")
            else:
                logger.exception("Failed to read data from DTU via Modbus.")
        except Exception:
            logger.exception("Failed to read data from DTU. Unknown failure type.")

        if plant_data:
            try:
                # Publish configurations?
                # This is done only for the first data set
                if not self._mqtt_configured:
                    for topic, payload in self._mqtt_builder.get_configs(plant_data=plant_data):
                        self._mqtt_publisher.publish(topic=topic, message=payload, retain=True)
                        mqtt_broker = "mqtt://{}:{}/{}".format(
                            self._mqtt_publisher._mqtt_broker, self._mqtt_publisher._mqtt_port, topic
                        )
                        logger.debug("Published config into {}".format(mqtt_broker))
                    self._mqtt_configured = True

                # Publish data
                for topic, payload in self._mqtt_builder.get_states(plant_data=plant_data):
                    self._mqtt_publisher.publish(topic=topic, message=payload)
                    publish_count += 1
                    mqtt_broker = "mqtt://{}:{}/{}".format(
                        self._mqtt_publisher._mqtt_broker, self._mqtt_publisher._mqtt_port, topic
                    )
                    logger.debug("Published data into %s", mqtt_broker)
            except Exception:
                logger.exception("Failed to publish data from DTU. Unknown failure type.")

            logger.info(
                "DTU data received and published. %s messages into mqtt://%s:%d",
                publish_count,
                self._mqtt_publisher._mqtt_broker,
                self._mqtt_publisher._mqtt_port,
            )
        else:
            logger.warning("No DTU data received!")

        self._lock.release()


def run_periodic_job(period: int, job: Callable) -> None:
    """Run given function periodically.

    Arguments:
        period: execution period
        job: function to execute

    """
    running = True
    logger.info("Begin looping messages")
    while running:
        try:
            threading.Thread(target=job).start()
            time.sleep(period)
        except KeyboardInterrupt:
            running = False
    logger.info("Done looping messages")
