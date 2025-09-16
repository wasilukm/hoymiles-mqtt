"""MQTT related interfaces."""

import ssl
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator, Optional

from paho.mqtt.publish import multiple as publish_multiple

if TYPE_CHECKING:
    from paho.mqtt.publish import AuthParameter, MessagesList, TLSParameter


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
            mqtt_broker: address/name of MQTT broker
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

    @property
    def broker(self) -> str:
        """Address/name of the MQTT broker."""
        return self._mqtt_broker

    @property
    def broker_port(self) -> int:
        """Port of the MQTT broker."""
        return self._mqtt_port

    @contextmanager
    def schedule_publish(self) -> Generator["MessagesList", Any, None]:
        """Schedule and send messages in a group.

        Context manager to collect messages and send them all
        together within the same MQTT connection session at exit.

        """
        messages: MessagesList = []

        yield messages

        publish_multiple(
            msgs=messages,
            hostname=self.broker,
            port=self.broker_port,
            auth=self._auth,
            tls=self._tls,
        )
