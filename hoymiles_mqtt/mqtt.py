"""MQTT related interfaces."""
from paho.mqtt.publish import single as publish_single


class MqttPublisher:
    """MQTT Publisher."""

    def __init__(self, mqtt_broker: str, mqtt_port: int, mqtt_user: str = None, mqtt_password: str = None):
        """Initialize the object.

        Arguments:
            mqtt_broker: address of MQTT broker
            mqtt_port: port of MQTT broker
            mqtt_user: MQTT username
            mqtt_password: password

        """
        self._mqtt_broker = mqtt_broker
        self._mqtt_port = mqtt_port
        self._auth = None
        if mqtt_user and mqtt_password:
            self._auth = {'username': mqtt_user, 'password': mqtt_password}

    def publish(self, topic: str, message: str, retain: bool = False) -> None:
        """Publish a message to the given MQTT topic.

        Arguments:
            topic: MQTT topic
            message: a message to publish
            retain: if the message shall be retained by MQTT broker

        """
        publish_single(
            topic=topic,
            payload=message,
            hostname=self._mqtt_broker,
            port=self._mqtt_port,
            auth=self._auth,
            retain=retain,
        )
