# Ubuntu Installer Specification

## Purpose
Provide install and uninstall scripts that provision the full Ubuntu runtime stack for the project.

## Requirements

### Requirement: Install the Ubuntu stack
The system MUST provide `scripts/install.sh` that installs PHP 8.5, MariaDB, Nginx, Composer, NVM, pnpm, mkcert, and phpMyAdmin on native Ubuntu.

#### Scenario: Clean Ubuntu installation
- GIVEN a fresh Ubuntu system with `sudo`, internet access, and configured sudoers
- WHEN `scripts/install.sh` executes
- THEN it MUST install all required packages and tools
- AND it MUST enable MariaDB, Nginx, and PHP-FPM to start on boot

#### Scenario: PHP 8.5 PPA fallback
- GIVEN PHP 8.5 is not available in the default Ubuntu repositories
- WHEN the install script reaches the PHP step
- THEN it MUST add the required PPA or pin an alternative version
- AND it MUST fail gracefully with instructions if no version can be installed

### Requirement: Uninstall the Ubuntu stack
The system MUST provide `scripts/uninstall.sh` that removes installed packages while preserving site data by default.

#### Scenario: Default uninstall preserves data
- GIVEN the stack was installed by `scripts/install.sh`
- WHEN `scripts/uninstall.sh` runs without flags
- THEN it MUST remove packages and configuration
- AND it MUST preserve site directories and databases

#### Scenario: Purge uninstall removes data
- GIVEN the stack was installed by `scripts/install.sh`
- WHEN `scripts/uninstall.sh --purge` runs
- THEN it MUST remove packages, configuration, site directories, and databases
- AND it MUST require explicit confirmation
