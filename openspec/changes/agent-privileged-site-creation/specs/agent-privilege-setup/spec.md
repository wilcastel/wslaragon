# Agent Privilege Setup Specification

## Purpose

Provide an administrator-enabled, narrowly bounded privilege protocol for agent-driven site registration without granting general root access.

## Requirements

### Requirement: TTY-only feature lifecycle

The system MUST provide TTY-only `bootstrap`, `status`, and `disable` operations for the agent privilege feature. Bootstrap MUST install the helper at `/usr/lib/wslaragon/agent-privilege-helper` as a root-owned regular `0755` file, verify its ownership, mode, and digest before enabling authorization, validate a dedicated root-owned `0440` sudoers fragment with `visudo -cf`, and prove non-interactive readiness after activation. Disable MUST remove the verified feature-owned sudoers fragment before the verified helper and MUST preserve legacy policy and user-owned project files, certificates, databases, and state.

#### Scenario: Administrator bootstraps the feature

- GIVEN an administrator invokes `bootstrap` from a TTY and no ownership conflict exists
- WHEN helper staging, verification, and sudoers validation succeed
- THEN the system MUST install the verified helper before the dedicated authorization
- AND it MUST prove readiness using non-interactive sudo

#### Scenario: Bootstrap finds a conflicting artifact

- GIVEN bootstrap encounters a foreign helper, dedicated artifact, or legacy `/etc/sudoers.d/wslaragon` policy
- WHEN completing setup would replace, overwrite, or migrate it
- THEN the system MUST stop for an explicit TTY administrator decision
- AND it MUST NOT replace or migrate the artifact implicitly

#### Scenario: Administrator disables the feature

- GIVEN the dedicated sudoers fragment and helper are verified as feature-owned
- WHEN an administrator invokes `disable` from a TTY
- THEN the system MUST remove the sudoers fragment before the helper
- AND it MUST NOT remove legacy policy or user-owned assets

### Requirement: Fixed sudo authorization

The system MUST authorize passwordless elevation only as `sudo -n -- /usr/lib/wslaragon/agent-privilege-helper`. Neither the sudoers policy nor the helper MUST authorize a shell, generic command runner, caller-selected command, path, content, utility, service, permission operation, or Nginx payload.

#### Scenario: Dedicated policy is installed

- GIVEN bootstrap is ready to activate the dedicated policy
- WHEN it writes the validated sudoers fragment
- THEN the fragment MUST authorize only the fixed helper invocation
- AND it MUST NOT directly authorize unrestricted privileged utilities or service actions

### Requirement: Bounded registration protocol

The helper MUST accept exactly one bounded newline-delimited JSON request record with version `1` and only `ready`, `apply_registration`, or `remove_registration` operations. It MUST emit diagnostics only to stderr, return bounded schema-valid responses with stable non-secret error codes, and reject multiple records, malformed input, unknown fields, raw commands, paths, content, service actions, traversal, symlinks, invalid site names, types, ports, outside-root layouts, and non-native platforms.

#### Scenario: Valid registration is applied

- GIVEN a request contains valid scalar registration fields for a generated site within a configured project root on native Ubuntu
- WHEN the helper receives `apply_registration`
- THEN it MUST reconstruct all privileged destinations and configuration from root-owned configuration and fixed templates
- AND it MUST perform only managed hosts, derived Nginx configuration or links, the fixed generated-root access policy, `nginx -t`, and `systemctl reload nginx` actions

#### Scenario: Unsafe request is received

- GIVEN a helper request contains an unsupported field or unsafe boundary value
- WHEN the helper validates the single request record
- THEN it MUST return a stable machine-readable failure without secrets
- AND it MUST NOT modify privileged system configuration

#### Scenario: Registration is removed

- GIVEN a valid `remove_registration` request identifies feature-managed derived artifacts
- WHEN the helper processes the request
- THEN it MUST remove only those derived registration and managed-host artifacts
- AND it MUST NOT remove user project files, certificates, databases, or user state

#### Scenario: Windows-host elevation is requested

- GIVEN a request requires WSL Windows-host mutation or another non-native platform action
- WHEN the helper validates the platform
- THEN it MUST return `platform_unsupported`
- AND it MUST NOT attempt host elevation

### Requirement: Unprivileged privilege client

The system MUST provide an unprivileged client that uses only the fixed non-interactive sudo invocation, sends and receives one bounded JSON record, validates the response schema, enforces a timeout, redacts stderr diagnostics, and maps missing setup, denied authorization, malformed protocol, timeout, and helper operation failures to stable safe results. The client MUST NOT use a shell, `sudo -v`, password prompts, or prompt-capable retry.

#### Scenario: Helper response is valid

- GIVEN the fixed helper returns one schema-valid response before the timeout
- WHEN the client processes the response
- THEN the client MUST return the corresponding validated result
- AND it MUST NOT expose helper stderr in that result

#### Scenario: Helper cannot provide a valid response

- GIVEN the fixed invocation is denied, missing, times out, or returns malformed or multiple records
- WHEN the client processes the invocation outcome
- THEN it MUST return the applicable stable safe failure
- AND it MUST NOT retry with interactive authentication
