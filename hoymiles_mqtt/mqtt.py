"""MQTT related interfaces."""

import logging
import ssl
from typing import TYPE_CHECKING, Optional

from paho.mqtt.publish import single as publish_single

if TYPE_CHECKING:
    from paho.mqtt.publish import AuthParameter, TLSParameter

logger = logging.getLogger(__name__)


class MqttPublisher:
    """MQTT Publisher."""

    def __init__(
        self,
        mqtt_broker: str,
        mqtt_port: int,
        mqtt_user: Optional[str] = None,
        mqtt_password: Optional[str] = None,
        mqtt_tls: Optional[bool] = False,
        mqtt_tls_insecure: Optional[bool] = False,
    ):
        """Initialize the object.

        Arguments:
            mqtt_broker: address of MQTT broker
            mqtt_port: port of MQTT broker
            mqtt_user: MQTT username
            mqtt_password: password
            mqtt_tls: TLS connection
            mqtt_tls_insecure: TLS insecure connection

        """
        self._mqtt_broker = mqtt_broker
        self._mqtt_port = mqtt_port
        self._auth: Optional[AuthParameter] = None
        if mqtt_user and mqtt_password:
            self._auth = {'username': mqtt_user, 'password': mqtt_password}
        self._tls: Optional[TLSParameter] = None
        if mqtt_tls:
            self._tls = {
                'ca_certs': None,  # type: ignore[typeddict-item]
                'tls_version': ssl.PROTOCOL_TLS_CLIENT,
                'insecure': False,
            }
            if mqtt_tls_insecure:
                self._tls['insecure'] = True

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
            tls=self._tls,
        )
