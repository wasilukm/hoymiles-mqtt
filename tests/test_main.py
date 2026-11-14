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


def test_main_comm_parameters(monkeypatch):
    """Verify that communication parameters are passed to the Modbus client."""
    monkeypatch.setattr(
        'sys.argv',
        ['hoymiles_mqtt', '--mqtt-broker', 'some_broker', '--dtu-host', 'some_dtu_host']
        + ['--comm-timeout', '5', '--comm-retries', '4']
        + ['--comm-reconnect-delay', '1.5', '--comm-reconnect-delay-max', '60'],
    )
    with patch('hoymiles_mqtt.__main__.run_periodic_job'), patch('hoymiles_mqtt.__main__.HoymilesQueryJob') as job:
        main()
    comm_params = job.call_args.kwargs['modbus_client'].comm_params
    assert comm_params.timeout == 5
    assert comm_params.retries == 4
    assert comm_params.reconnect_delay == 1.5
    assert comm_params.reconnect_delay_max == 60
