# Ubuntu MySQL User Specification

## Purpose
Allow site creation and database operations to use a configurable MariaDB/MySQL user instead of the hard-coded `root` account.

## Requirements

### Requirement: Configurable database user
The system MUST use a configurable `DB_USER` value for all database connections and site creator operations.

#### Scenario: Custom user used for site database
- GIVEN `DB_USER` is set to `wslaragon` and `DB_PASSWORD` is configured
- WHEN a site creator provisions a database
- THEN it MUST connect as `wslaragon`
- AND it MUST NOT connect as `root`

#### Scenario: Backward-compatible default
- GIVEN `DB_USER` is not explicitly configured
- WHEN the system resolves the database user
- THEN it SHOULD default to `root`
- AND it MUST document that this default is deprecated on Ubuntu
