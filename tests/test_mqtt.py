"""Tests for MqttPublisher."""

from unittest.mock import Mock, patch

from hoymiles_mqtt.mqtt import MqttPublisher


@patch("hoymiles_mqtt.mqtt.publish_multiple")
def test_publish(publish_multiple_mock: Mock):
    """Verify messages publishing."""
    mqtt_broker = "some broker"
    mqtt_port = 1234

    publisher = MqttPublisher(mqtt_broker=mqtt_broker, mqtt_port=mqtt_port)
    with publisher.schedule_publish() as queue:
        queue.add("some topic 1", "some payload 1")
        queue.add("some topic 2", "some payload 2")

    publish_multiple_mock.assert_called_with(
        msgs=[('some topic 1', 'some payload 1', 0, False), ('some topic 2', 'some payload 2', 0, False)],
        hostname=mqtt_broker,
        port=mqtt_port,
        auth=None,
        tls=None,
    )
