# Changelog

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
