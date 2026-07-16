# Ubuntu Site Creation Specification

## Purpose
Enable site creation on native Ubuntu with persistent sudo credentials and correct web-server file permissions.

## Requirements

### Requirement: Sudo keep-alive during site creation
The system MUST keep sudo credentials alive while site creation performs multiple elevated operations.

#### Scenario: Long-running site creation
- GIVEN site creation invokes `sudo` for hosts, Nginx, and PHP-FPM changes
- WHEN the operation exceeds the sudo timeout window
- THEN the system MUST refresh sudo credentials before expiration
- AND the operation MUST complete without interactive prompts

### Requirement: ACL-based `www-data` permissions
The system MUST grant `www-data` read access to site files using POSIX ACLs, falling back to `chmod` when ACL tools are unavailable.

#### Scenario: ACL tools available
- GIVEN `setfacl` is installed
- WHEN a new site directory is created
- THEN the system MUST run `setfacl -R -m u:www-data:rx` on the directory
- AND `www-data` MUST be able to read site files

#### Scenario: ACL tools unavailable
- GIVEN `setfacl` is not installed
- WHEN a new site directory is created
- THEN the system MUST fall back to `chmod -R o+rx` on the directory
- AND the site MUST remain accessible by the web server
