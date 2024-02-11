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
