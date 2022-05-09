# Hoymiles MQTT


[![pypi](https://img.shields.io/pypi/v/hoymiles-mqtt.svg)](https://pypi.org/project/hoymiles-mqtt/)
[![python](https://img.shields.io/pypi/pyversions/hoymiles-mqtt.svg)](https://pypi.org/project/hoymiles-mqtt/)
[![Build Status](https://github.com/wasilukm/hoymiles-mqtt/actions/workflows/dev.yml/badge.svg)](https://github.com/wasilukm/hoymiles-mqtt/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/wasilukm/hoymiles-mqtt/branch/main/graphs/badge.svg)](https://codecov.io/github/wasilukm/hoymiles-mqtt)



Send data from Hoymiles photovoltaic installation to Home Assistant through MQTT broker.

* GitHub: <https://github.com/wasilukm/hoymiles-mqtt>
* PyPI: <https://pypi.org/project/hoymiles-mqtt/>
* Free software: MIT

The tool periodically communicates with Hoymiles DTU trough ModbusTCP and sends gathered data to MQTT broker.
Data to MQTT broker are sent with topics that can be recognized by Home Assistant.
In a result DTU and each micro-inverter can be represented in Home Assistant as a separate device with set of entities. Example:

![MQTT Devices](/docs/mqtt_devices.png)

![MQTT Entities](/docs/mqtt_entities.png)

DTU device represent overall data for the installation:
- pv_power - current power - sum from all micro-inverters
- today_production - today energy production - sum from all micro-inverters, for each micro-inverter last known
  good value is cached to prevent disturbances in statistics when part of the installation is temporarily off
  or off-line. This entity can be used in Home Assistant energy panel as a production from solar panels.
  An example chart:

  ![Solar production](/docs/solar%20production.png)
- total_production - lifetime energy production - sum from all micro-inverters

Each micro-inverter has the following entities:
- port_number
- pv_voltage
- pv_current
- grid_voltage
- grid_frequency
- pv_power
- today_production
- total_production
- temperature
- operating_status
- alarm_code
- alarm_count
- link_status

Depending on the installation (number of micro-inverter), the tool may create many entities. One may limit the entities
or with the option _--mi-entities_.

## Usage

### Prerequisites
- DTUs' _Ethernet_ port connected to a network
- DTU has assigned IP address by DHCP server. IP address shall be reserved for the device
- running MQTT broker, for example https://mosquitto.org/
- MQTT integration enabled in Home Assistant, https://www.home-assistant.io/integrations/mqtt/

### From command line
    usage: python3 -m hoymiles_mqtt [-h] [-c CONFIG] --mqtt-broker MQTT_BROKER [--mqtt-port MQTT_PORT] [--mqtt-user MQTT_USER] [--mqtt-password MQTT_PASSWORD] --dtu-host DTU_HOST [--dtu-port DTU_PORT]
                                    [--modbus-unit-id MODBUS_UNIT_ID] [--query-period QUERY_PERIOD] [--microinverter-type {MI,HM}] [--mi-entities MI_ENTITIES [MI_ENTITIES ...]]

    options:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            Config file path (default: None)
      --mqtt-broker MQTT_BROKER
                            Address of MQTT broker [env var: MQTT_BROKER] (default: None)
      --mqtt-port MQTT_PORT
                            MQTT broker port [env var: MQTT_PORT] (default: 1883)
      --mqtt-user MQTT_USER
                            User name for MQTT broker [env var: MQTT_USER] (default: None)
      --mqtt-password MQTT_PASSWORD
                            Password to MQTT broker [env var: MQTT_PASSWORD] (default: None)
      --dtu-host DTU_HOST   Address of Hoymiles DTU [env var: DTU_HOST] (default: None)
      --dtu-port DTU_PORT   DTU modbus port [env var: DTU_PORT] (default: 502)
      --modbus-unit-id MODBUS_UNIT_ID
                            Modbus Unit ID [env var: MODBUS_UNIT_ID] (default: 1)
      --query-period QUERY_PERIOD
                            How often (in seconds) DTU shall be queried. [env var: QUERY_PERIOD] (default: 60)
      --microinverter-type {MI,HM}
                            Type od microinverters in the installation. Mixed types are not supported. [env var: MICROINVERTER_TYPE] (default: MI)
      --mi-entities MI_ENTITIES [MI_ENTITIES ...]
                            Microinverter entities that will be sent to MQTT. By default all entities are presented. [env var: MI_ENTITIES] (default: ['port_number', 'pv_voltage', 'pv_current', 'grid_voltage',
                            'grid_frequency', 'pv_power', 'today_production', 'total_production', 'temperature', 'operating_status', 'alarm_code', 'alarm_count', 'link_status'])

    Args that start with '--' (eg. --mqtt-broker) can also be set in a config file (specified via -c). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi). If an
    arg is specified in more than one place, then commandline values override environment variables which override config file values which override defaults.

### Docker

Build an image

    docker build https://github.com/wasilukm/hoymiles-mqtt.git#v0.1.0 -t hoymiles_mqtt

Run (replace IP addresses)

    docker run -d -e MQTT_BROKER=192.168.1.101 -e DTU_HOST=192.168.1.100 hoymiles_mqtt

Please note, depending on the needs more options can be specified with _-e_. See above for all possible options.

## Known issues
Hoymiles DUTs are not the most stable devices. Therefore, from time to time the tool may not be able to connect to DTU
and will print the following exception:

    Modbus Error: [Invalid Message] No response received, expected at least 8 bytes (0 received)

The tool will continue its operation and try communication with DTU with the next period.

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [waynerv/cookiecutter-pypackage](https://github.com/waynerv/cookiecutter-pypackage) project template.
