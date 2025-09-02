# Changelog

## [0.11.0] (2025-09-02)

* update pymodbus to 3.11 (via hoymiles-modbus package) to align with Home Assistant
* drop support for Python 3.9

## [0.10.0] (2025-01-19)

* add support for Python 3.13
* improve detection of inverter type (updated hoymiles_modbus library)
  (fixes #36)

## [0.9.0] (2024-12-08)

New feature:
- inverter type (MI or HM) is now automatically detected
- compatibility with pymodbus 3.7
- added parameter communication parameter `comm-reconnect-delay-max`

Breaking changes:
- removed parameter microinverter-type (no longer needed)
- due to support for pymodbus 3.7 removed parameters:
  - `comm-retry-on-empty`
  - `comm-close-comm-on-error`
  - `comm-strict`
- default value of `comm-reconnect-delay` changed to 0 (means reconnections are disabled).
  The previous value was big to achieve the same. However, the new value is the proper solution.

## [0.8.1] (2024-09-29)

* fix not graceful process termination - added support for system signals.
* rework logging to not log events from sub-dependencies (they were spamming logs)

## [0.8.0] (2024-08-26)

* add support for Python 3.12
* BREAKING CHANGE: drop support for Python 3.8
* Docker uses Python 3.12 image (3.9 previously)
* restore capability of logging to console (use `--log-to-console` switch)

## [0.7.0] (2024-08-10)

* improved logging capabilities (thanks to @HQJaTu)
  * Added switch --log-level
  * Added switch --log-file
* Separated retrieving data from DTU via M-bus and MQTT publishing with separate exception handling (thanks to @HQJaTu)
* Added handling for Ctrl-C keypress to stop execution (thanks to @HQJaTu)
* fixed spelling mistakes in readme.md (thanks to @weitheng)

## [0.6.0] (2024-02-13)

* do not send measurements when operating status is 0 (prevent sending zeros when inverter is off)
* do not send today_production and total_production when a new value is not greater than the previous
* add support for TLS communication with MQTT broker

## [0.5.1] (2023-11-23)

* stop sending all values as strings

## [0.5.0] (2023-08-29)

* Rename entity names to not include device name, this is to align with https://developers.home-assistant.io/blog/2023-057-21-change-naming-mqtt-entities/#naming-of-mqtt-entities
* DStarting from this version, usage with Home Assistant older than 2023.8 is not recommended

## [0.4.1] (2023-07-09)

*  Fix parsing MI_ENTITIES and PORT_ENTITIES env variables. Values specified in
   these variables were added to the default list of options instead of replacing them.

## [0.4.0] (2023-02-07)

* add support for Python 3.10 and 3.11
* remove support for Python 3.6 and 3.8

## [0.3.0] (2022-10-30)

* BREAKING CHANGE - add support for multiple ports (PV panels) in one micro-inverter. This required renaming of inverters'
  entities.
* BREAKING CHANGE - removed values from `mi-entities` option:
  * pv_power, today_production, total_production, pv_voltage, pv_current - moved to new `port-entities` option
  * port_option
* add support for low level modbus communication parameters, they can be used for instance to increase communication
  stability

## [0.2.0] (2022-06-29)

* add support for `expire-after` option which defines number of seconds after which DTU or microinverter entities
  expire, if updates are not received (for example due to communication issues). After expiry, entities become
  unavailable in Home Assistant. If the option is not specified, entities never expire.

## [0.1.0] (2022-05-09)

* First release on PyPI.
