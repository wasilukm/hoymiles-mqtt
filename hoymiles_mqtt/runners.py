import threading
import time

from hoymiles_modbus.client import HoymilesModbusTCP

from hoymiles_mqtt.ha import HassMqtt
from hoymiles_mqtt.mqtt import MqttPublisher

RESET_HOUR = 23


class HoymilesQueryJob:

    _lock = threading.Lock()

    def __init__(self, mqtt_builder: HassMqtt, mqtt_publisher: MqttPublisher, modbus_client: HoymilesModbusTCP):
        self._mqtt_builder: HassMqtt = mqtt_builder
        self._mqtt_publisher: MqttPublisher = mqtt_publisher
        self._modbus_client: HoymilesModbusTCP = modbus_client
        self._mqtt_configured: bool = False

    def execute(self):
        is_acquired = self._lock.acquire(blocking=False)
        if is_acquired:
            if time.localtime().tm_hour == RESET_HOUR:
                self._mqtt_builder.clear_production_today()
            try:
                plant_data = self._modbus_client.plant_data
                if not self._mqtt_configured:
                    for topic, payload in self._mqtt_builder.get_configs(plant_data=plant_data):
                        self._mqtt_publisher.publish(topic=topic, payload=payload)
                    self._mqtt_configured = True
                for topic, payload in self._mqtt_builder.get_states(plant_data=plant_data):
                    self._mqtt_publisher.publish(topic=topic, payload=payload)
            finally:
                self._lock.release()


def run_periodic_job(period: int, job) -> None:
    while True:
        threading.Thread(target=job).start()
        time.sleep(period)
