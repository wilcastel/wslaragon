# Test Environment Specification

## Purpose

Ensure the declared project test environment can execute the configured coverage and MCP test contracts for the agent privilege feature.

## Requirements

### Requirement: Declared test dependency availability

The project test environment MUST provide declared development dependencies required by configured pytest coverage options, including `pytest-cov`, and runtime dependencies required by dotenv-dependent MCP tests, including `python-dotenv`, before it claims configured unit-suite or 90% coverage results.

#### Scenario: Configured unit suite is run
- GIVEN the project environment has been provisioned for the declared development and runtime dependencies
- WHEN the configured unit-suite or coverage command is run
- THEN pytest MUST be able to load its configured coverage options and dotenv-dependent MCP tests
- AND coverage results MUST NOT be claimed before those dependencies are available

### Requirement: Privilege boundary test coverage

The test suite MUST cover helper request validation and confinement, bootstrap ordering and ownership conflicts, client protocol and redaction behavior, interactive and agent-mode separation, normal and headless registration cleanup, MCP result mappings, unrelated MCP non-expansion, and native-Ubuntu dedicated-user bootstrap, readiness, creation, rollback, and disable behavior.

#### Scenario: Agent privilege change is validated
- GIVEN the agent privilege feature is ready for release validation
- WHEN its focused unit and native-Ubuntu integration coverage runs
- THEN the tests MUST exercise the defined boundary and lifecycle failure cases
- AND they MUST verify that unrelated MCP privileges remain unchanged
