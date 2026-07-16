# Ubuntu PHP-FPM Specification

## Purpose
Discover and configure the PHP-FPM service name and socket path for the active PHP version on Ubuntu.

## Requirements

### Requirement: Configurable PHP version default
The system MUST allow the default PHP version to be configured and MUST use it when no explicit version is supplied.

#### Scenario: Default PHP version used
- GIVEN `PHP_VERSION` is set to `8.5`
- WHEN the system generates FPM paths
- THEN it MUST use version `8.5`
- AND it MUST NOT assume `8.3`

### Requirement: Discover PHP-FPM socket path
The system MUST discover the PHP-FPM socket path by checking versioned paths before falling back to generic ones.

#### Scenario: Versioned socket exists
- GIVEN PHP 8.5 is installed
- WHEN the system looks up the FPM socket
- THEN it MUST return `/run/php/php8.5-fpm.sock`

#### Scenario: Generic socket fallback
- GIVEN the versioned socket does not exist
- WHEN the system looks up the FPM socket
- THEN it MUST fall back to `/run/php/php-fpm.sock`
- AND it MUST raise an error if neither socket exists

### Requirement: Safer PHP version switch
The system MUST verify the target PHP-FPM package is installed before switching versions.

#### Scenario: Missing target FPM package
- GIVEN PHP 8.5 FPM is not installed
- WHEN `php switch_version 8.5` is invoked
- THEN the command MUST abort with a clear error
- AND it MUST leave the current FPM configuration intact
