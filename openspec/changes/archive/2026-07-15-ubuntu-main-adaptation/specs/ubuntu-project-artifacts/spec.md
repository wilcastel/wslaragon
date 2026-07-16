# Ubuntu Project Artifacts Specification

## Purpose
Update project metadata, documentation, and tests to reflect native Ubuntu support.

## Requirements

### Requirement: Ubuntu documentation
The system MUST ship `docs/UBUNTU.md` with setup, usage, and uninstall instructions for native Ubuntu.

#### Scenario: Ubuntu guide is complete
- GIVEN a user on native Ubuntu
- WHEN they open `docs/UBUNTU.md`
- THEN it MUST describe installation, site creation, SSL, and uninstall steps
- AND it MUST reference `scripts/install.sh` and `scripts/uninstall.sh`

### Requirement: Project metadata reflects Ubuntu support
The system MUST update `pyproject.toml`, CLI description, and `main.py` to remove WSL2-only wording.

#### Scenario: CLI help text
- GIVEN the CLI help is displayed
- WHEN the description is read
- THEN it MUST NOT state that the tool is only for WSL2
- AND it MAY mention Ubuntu support

### Requirement: Tests aligned with Ubuntu defaults
The system MUST update tests and fixtures so the suite passes with Ubuntu-native defaults.

#### Scenario: Unit tests with Ubuntu fixtures
- GIVEN fixtures use `/etc/hosts` and PHP 8.5 defaults
- WHEN the unit test suite runs
- THEN all tests MUST pass
- AND coverage MUST remain above the 90% threshold
