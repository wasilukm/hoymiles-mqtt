"""Top-level package for Hoymiles MQTT."""

__author__ = """Foo Bar"""
__email__ = 'foo@bar.com'
__version__ = '0.8.0'

MI_ENTITIES = [
    'grid_voltage',
    'grid_frequency',
    'temperature',
    'operating_status',
    'alarm_code',
    'alarm_count',
    'link_status',
]

PORT_ENTITIES = ['pv_voltage', 'pv_current', 'pv_power', 'today_production', 'total_production']
