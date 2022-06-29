# Changelog

## [0.2.0] (2022-06-29)

* add support for `expire-after` option which defines number of seconds after which DTU or microinverter entities
  expire, if updates are not received (for example due to communication issues). After expiry, entities become
  unavailable in Home Assistant. If the option is not specified, entities never expire.

## [0.1.0] (2022-05-09)

* First release on PyPI.
