#!/usr/bin/env python
"""Tests for __main__ module."""

from unittest.mock import patch

from hoymiles_mqtt.__main__ import main


def test_main_happy_path(monkeypatch):
    """Happy path verification for main() function."""
    monkeypatch.setattr('sys.argv', ['hoymiles_mqtt', '--mqtt-broker', 'some_broker', '--dtu-host', 'some_dtu_host'])
    with patch('hoymiles_mqtt.__main__.run_periodic_job') as mock_run_periodic_job:
        main()
    mock_run_periodic_job.assert_called_once()


def test_main_cache_file(monkeypatch):
    """Verify that the cache file option is passed to the MQTT builder."""
    monkeypatch.setattr(
        'sys.argv',
        ['hoymiles_mqtt', '--mqtt-broker', 'some_broker', '--dtu-host', 'some_dtu_host', '--cache-file', 'cache.json'],
    )
    with patch('hoymiles_mqtt.__main__.run_periodic_job'), patch('hoymiles_mqtt.__main__.HassMqtt') as mock_hass_mqtt:
        main()
    assert mock_hass_mqtt.call_args.kwargs['cache_file'] == 'cache.json'
