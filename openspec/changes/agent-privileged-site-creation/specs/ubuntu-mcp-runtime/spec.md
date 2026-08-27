# Delta for Ubuntu MCP Runtime

## ADDED Requirements

### Requirement: Fail-closed MCP agent creation activation

The MCP runtime MUST retain the unconditional fail-closed `privilege_setup_required` guard until the helper, bootstrap, client, and complete agent-mode site route are available and covered together. After that activation boundary, normal and headless creation MUST use the privilege client readiness result before execution. A ready result MUST invoke the existing respective CLI argument permutation with `--privilege-mode=agent`; a missing, denied, malformed, timed-out, or failed result MUST return a stable safe JSON-string response and MUST NOT call CLI creation or `_run_interactive`.

#### Scenario: Activation boundary is incomplete
- GIVEN the complete helper and agent-mode routing activation boundary is not available
- WHEN an MCP client requests normal or headless site creation
- THEN the runtime MUST return `privilege_setup_required`
- AND it MUST NOT invoke the legacy interactive route

#### Scenario: Privilege client is ready
- GIVEN the complete activation boundary is available and the privilege client reports ready
- WHEN an MCP client requests normal or headless site creation
- THEN the runtime MUST invoke the historical matching CLI argument permutation with `--privilege-mode=agent`
- AND it MUST NOT invoke `_run_interactive`

#### Scenario: Privilege client is not usable
- GIVEN an MCP client requests normal or headless site creation
- WHEN readiness is absent, denied, malformed, timed out, or otherwise fails
- THEN the runtime MUST return the mapped stable safe JSON-string response
- AND it MUST NOT invoke CLI creation, `_run_interactive`, or password authentication

### Requirement: Scoped MCP regression contract

The system MUST reconcile legacy MCP and CLI creation tests to the explicit interactive and agent-mode contract. Tests MUST verify normal and headless ready routing, denied and failed readiness mappings, no interactive execution in agent mode, and historical argument permutations. The system MUST preserve the existing behavior and privilege scope of unrelated MCP tools.

#### Scenario: Unrelated MCP tool is invoked
- GIVEN an MCP tool outside normal or headless site creation is invoked
- WHEN this feature is enabled
- THEN the tool MUST retain its existing behavior
- AND it MUST NOT receive authorization through the agent helper boundary
