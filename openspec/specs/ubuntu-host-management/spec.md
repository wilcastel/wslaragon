# Ubuntu Host Management Specification

## Purpose
Manage local host entries on native Ubuntu by writing to `/etc/hosts` with elevated privileges.

## Requirements

### Requirement: Detect native Ubuntu hosts path
The system MUST detect a native Ubuntu runtime and use `/etc/hosts` as the hosts file path.

#### Scenario: Ubuntu runtime detection
- GIVEN the environment is native Ubuntu
- WHEN the system resolves the hosts file path
- THEN it MUST return `/etc/hosts`
- AND it MUST NOT target the Windows hosts file

### Requirement: Edit `/etc/hosts` via `sudo tee`
The system MUST append and remove host entries in `/etc/hosts` using `sudo tee` to avoid direct write permission failures.

#### Scenario: Add a site host entry
- GIVEN a site with local domain `myproject.test`
- WHEN the system adds the host entry
- THEN `sudo tee -a /etc/hosts` MUST receive `127.0.0.1 myproject.test`
- AND the file MUST remain readable by all users

#### Scenario: Remove a site host entry
- GIVEN an existing `/etc/hosts` entry for `myproject.test`
- WHEN the system removes the entry
- THEN `sudo tee /etc/hosts` MUST rewrite the file without that entry
- AND other entries MUST be preserved
