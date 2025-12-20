# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2023-12-20
### Added
 - Multi-gateway service and characteristics

### Changed
 - Backend service and characteristics renamed to app
 - Volatile logs in stead of persistent

### Fixed
 - Handle daemon communication errors

## [1.1.0] - 2023-11-10
### Added
 - Save backups when modifying backend configuration
 - Gpio managed by gpio module

### Changed
 - Update cryptography module version
 - Use nmcli to get and set network configuration

### Fixed
 - Connectivity check not returning error when it fails

## [1.0.0] - 2023-01-27
### Added
 - First stable version

[Unreleased]: https://bitbucket.org/tychetools/ble_config_server/branches/compare/devel..master
[1.0.0]: https://bitbucket.org/tychetools/ble_config_server/src/v1.0.0/
[1.1.0]: https://bitbucket.org/tychetools/ble_config_server/branches/compare/v1.1.0..v1.0.0
[1.2.0]: https://bitbucket.org/tychetools/ble_config_server/branches/compare/v1.2.0..v1.1.0
