from paho.mqtt.publish import single as publish_single


class MqttPublisher:
    def __init__(self, mqtt_broker: str, mqtt_port: int, mqtt_user: str = None, mqtt_password: str = None):
        self._mqtt_broker = mqtt_broker
        self._mqtt_port = mqtt_port
        self._auth = None
        if mqtt_user and mqtt_password:
            self._auth = {'username': mqtt_user, 'password': mqtt_password}

    def publish(self, topic: str, payload: str, retain: bool = False) -> None:
        publish_single(
            topic=topic,
            payload=payload,
            hostname=self._mqtt_broker,
            port=self._mqtt_port,
            auth=self._auth,
            retain=retain,
        )
