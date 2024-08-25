# Hoymiles MQTT


[![pypi](https://img.shields.io/pypi/v/hoymiles-mqtt.svg)](https://pypi.org/project/hoymiles-mqtt/)
[![python](https://img.shields.io/pypi/pyversions/hoymiles-mqtt.svg)](https://pypi.org/project/hoymiles-mqtt/)
[![Build Status](https://github.com/wasilukm/hoymiles-mqtt/actions/workflows/dev.yml/badge.svg)](https://github.com/wasilukm/hoymiles-mqtt/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/wasilukm/hoymiles-mqtt/branch/main/graphs/badge.svg)](https://codecov.io/github/wasilukm/hoymiles-mqtt)



Send data from Hoymiles photovoltaic installation to Home Assistant through MQTT broker.

* GitHub: <https://github.com/wasilukm/hoymiles-mqtt>
* PyPI: <https://pypi.org/project/hoymiles-mqtt/>
* Free software: MIT

The tool periodically communicates with Hoymiles DTU (Pro) through ModbusTCP and sends gathered data to MQTT broker.
Data to MQTT broker are sent with topics that can be recognized by Home Assistant.
In a result DTU and each micro-inverter can be represented in Home Assistant as separate device with a set of entities. Example:

![MQTT Devices](/docs/mqtt_devices.png)

![MQTT Entities](/docs/mqtt_entities.png)

DTU device represents overall data for the installation:
- pv_power - current power - sum from all micro-inverters
- today_production - today energy production - sum from all micro-inverters, for each micro-inverter last known
  good value is cached to prevent disturbances in statistics when part of the installation is temporarily off
  or off-line. This entity can be used in Home Assistant energy panel as a production from solar panels.
  An example chart:

  ![Solar production](/docs/solar%20production.png)
- total_production - lifetime energy production - sum from all micro-inverters

Each micro-inverter has the following entities:
- grid_voltage
- grid_frequency
- temperature
- operating_status
- alarm_code
- alarm_count
- link_status

Depending on the installation (number of micro-inverter), the tool may create many entities. One may limit the entities
or with the option _--mi-entities_.

A micro-inverter can support multiple ports (PV panels), their states are represented by:
- pv_voltage
- pv_current
- pv_power
- today_production
- total_production

Publishing of these entities can be controlled with _--port-entities_.

The following entities are sent only when the inverter's operating status is greater
than 0: grid_voltage, grid_frequency, temperature, pv_voltage, pv_current, pv_power.

Additionally, today_production and total_production are updated only when the inverter's
operating status is greater than 0 and the new value is greater than the previous one.
This is to prevent drops in measurements which shall be only increasing.

## Usage

### Prerequisites
- DTUs' _Ethernet_ port connected to a network
- DTU has assigned IP address by DHCP server. IP address shall be reserved for the device
- running MQTT broker, for example https://mosquitto.org/
- MQTT integration enabled in Home Assistant, https://www.home-assistant.io/integrations/mqtt/

### From command line
    usage: python3 -m hoymiles_mqtt [-h] [-c CONFIG] --mqtt-broker MQTT_BROKER [--mqtt-port MQTT_PORT]
                                    [--mqtt-user MQTT_USER] [--mqtt-password MQTT_PASSWORD] [--mqtt-tls]
                                    [--mqtt-tls-insecure] --dtu-host DTU_HOST [--dtu-port DTU_PORT]
                                    [--modbus-unit-id MODBUS_UNIT_ID] [--query-period QUERY_PERIOD]
                                    [--microinverter-type {MI,HM}]
                                    [--mi-entities MI_ENTITIES [MI_ENTITIES ...]]
                                    [--port-entities PORT_ENTITIES [PORT_ENTITIES ...]]
                                    [--expire-after EXPIRE_AFTER] [--comm-timeout COMM_TIMEOUT]
                                    [--comm-retries COMM_RETRIES]
                                    [--comm-retry-on-empty COMM_RETRY_ON_EMPTY]
                                    [--comm-close-comm-on-error COMM_CLOSE_COMM_ON_ERROR]
                                    [--comm-strict COMM_STRICT]
                                    [--comm-reconnect-delay COMM_RECONNECT_DELAY]
                                    [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--log-file LOG_FILE]
                                    [--log-to-console]

    options:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            Config file path (default: None)
      --mqtt-broker MQTT_BROKER
                            Address of MQTT broker [env var: MQTT_BROKER] (default: None)
      --mqtt-port MQTT_PORT
                            MQTT broker port. Note that when using TLS connection you may need to specify
                            port 8883 [env var: MQTT_PORT] (default: 1883)
      --mqtt-user MQTT_USER
                            User name for MQTT broker [env var: MQTT_USER] (default: None)
      --mqtt-password MQTT_PASSWORD
                            Password to MQTT broker [env var: MQTT_PASSWORD] (default: None)
      --mqtt-tls            MQTT TLS connection [env var: MQTT_TLS] (default: False)
      --mqtt-tls-insecure   MQTT TLS insecure connection (only relevant when using with the --mqtt-tls
                            option). Do not use in production environments. [env var: MQTT_TLS_INSECURE]
                            (default: False)
      --dtu-host DTU_HOST   Address of Hoymiles DTU [env var: DTU_HOST] (default: None)
      --dtu-port DTU_PORT   DTU modbus port [env var: DTU_PORT] (default: 502)
      --modbus-unit-id MODBUS_UNIT_ID
                            Modbus Unit ID [env var: MODBUS_UNIT_ID] (default: 1)
      --query-period QUERY_PERIOD
                            How often (in seconds) DTU shall be queried. [env var: QUERY_PERIOD] (default:
                            60)
      --microinverter-type {MI,HM}
                            Type od microinverters in the installation. Mixed types are not supported. [env
                            var: MICROINVERTER_TYPE] (default: MI)
      --mi-entities MI_ENTITIES [MI_ENTITIES ...]
                            Microinverter entities that will be sent to MQTT. By default all entities are
                            presented. [env var: MI_ENTITIES] (default: ['grid_voltage', 'grid_frequency',
                            'temperature', 'operating_status', 'alarm_code', 'alarm_count', 'link_status'])
      --port-entities PORT_ENTITIES [PORT_ENTITIES ...]
                            Microinverters' port entities (in fact PV panel entities) that will be sent to
                            MQTT. By default all entities are presented. [env var: PORT_ENTITIES] (default:
                            ['pv_voltage', 'pv_current', 'pv_power', 'today_production',
                            'total_production'])
      --expire-after EXPIRE_AFTER
                            Defines number of seconds after which DTU or microinverter entities expire, if
                            updates are not received (for example due to communication issues). After
                            expiry, entities become unavailable in Home Assistant.By default it is 0, which
                            means that entities never expire. When different than 0, the value shallbe
                            greater than the query period. This setting does not apply to entities that
                            represent a total amount such as daily energy production (they never expire).
                            [env var: EXPIRE_AFTER] (default: 0)
      --comm-timeout COMM_TIMEOUT
                            Additional low level modbus communication parameter - request timeout. [env var:
                            COMM_TIMEOUT] (default: 3)
      --comm-retries COMM_RETRIES
                            Additional low level modbus communication parameter - max number of retries per
                            request. [env var: COMM_RETRIES] (default: 3)
      --comm-retry-on-empty COMM_RETRY_ON_EMPTY
                            Additional low level modbus communication parameter - retry if received an empty
                            response. [env var: COMM_RETRY_ON_EMPTY] (default: False)
      --comm-close-comm-on-error COMM_CLOSE_COMM_ON_ERROR
                            Additional low level modbus communication parameter - close connection on error.
                            [env var: COMM_CLOSE_COMM_ON_ERROR] (default: False)
      --comm-strict COMM_STRICT
                            Additional low level modbus communication parameter - strict timing, 1.5
                            character between requests. [env var: COMM_STRICT] (default: True)
      --comm-reconnect-delay COMM_RECONNECT_DELAY
                            Additional low level modbus communication parameter - delay in milliseconds
                            before reconnecting. [env var: COMM_RECONNECT_DELAY] (default: 300000)
      --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                            Python logger log level. Default: WARNING [env var: LOG_LEVEL] (default:
                            WARNING)
      --log-file LOG_FILE   Python logger log file. Default: not writing into a file [env var: LOG_FILE]
                            (default: None)
      --log-to-console      Enable logging to console. [env var: LOG_TO_CONSOLE] (default: False)

    Args that start with '--' can also be set in a config file (specified via -c). Config file syntax
    allows: key=value, flag=true, stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi). In
    general, command-line values override environment variables which override config file values which
    override defaults.


### Docker

Build an image

    docker build https://github.com/wasilukm/hoymiles-mqtt.git#v0.8s.0 -t hoymiles_mqtt

Run (change IP addresses)

    docker run -d -e MQTT_BROKER=192.168.1.101 -e DTU_HOST=192.168.1.100 hoymiles_mqtt

Please note, depending on the needs more options can be specified with _-e_. See above for all possible options.
For example to enable logging to console with DEBUG logging level:

    docker run -d -e MQTT_BROKER=192.168.1.101 -e DTU_HOST=192.168.1.100 -e LOG_LEVEL=DEBUG -e LOG_TO_CONSOLE=true hoymiles_mqtt

> **_NOTE:_**  DEBUG level is very verbose, so should be used only for troubleshooting.

## Troubleshooting

- Hoymiles DTUs are not the most stable devices. Therefore, from time to time the tool may not be able
  to connect to DTU and will print the following exception:

  >Modbus Error: [Invalid Message] No response received, expected at least 8 bytes (0 received)

  The tool will continue its operation and try to communicate with DTU in the next period.

  If the exception is constantly repeating and data is not refreshed in Home Assistant:
    - power cycle DTU
    - try to update DTU's firmware

- `libseccomp2` library may be missing on some operating systems, ensure the library is installed


## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [waynerv/cookiecutter-pypackage](https://github.com/waynerv/cookiecutter-pypackage) project template.
