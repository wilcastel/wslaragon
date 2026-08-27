# Proposal: Agent-Privileged Site Creation

## Intent

Complete secure MCP normal and headless site creation after the predecessor's deliberately fail-closed readiness-only slice. The change will provide the root-owned helper, administrator bootstrap, unprivileged client, explicit CLI agent-mode routing, selected site-registration adapters, reconciled MCP regressions, and a provisioned test environment needed to create sites without interactive sudo on MCP stdio.

The current unconditional `privilege_setup_required` guard remains in place until the helper/bootstrap and complete agent routing are ready together. A successful readiness probe must not activate the legacy interactive route.

## Problem and outcome

MCP creation is currently safe but unavailable: both create tools issue a fixed non-interactive `ready` probe and then always return setup-required. The legacy CLI route uses `sudo -v`, `SudoKeepAlive`, and scattered direct sudo operations, so resuming it from stdio would reintroduce password prompts and broad caller-influenced privileged operations.

After this change, an administrator can explicitly enable a narrowly scoped site-registration capability. A ready MCP invocation creates normal or paired headless sites through an explicit agent route; unprivileged scaffolding, certificates, databases, and user state stay user-owned, while only fixed derived hosts, Nginx, and bounded access-policy work crosses the root boundary. Absent, denied, malformed, or failing setup remains a stable safe MCP result with no interactive fallback.

## Scope

### In scope

- Add an immutable Python helper at `scripts/agent-privilege-helper.py`, installed by bootstrap at `/usr/lib/wslaragon/agent-privilege-helper` as a root-owned regular `0755` file.
- Add TTY-only `bootstrap`, `status`, and `disable` operations in `scripts/agent-privilege-setup.sh`. Bootstrap stages and verifies the helper before installing a dedicated root-owned `0440` sudoers fragment, validates staged policy with `visudo -cf`, then proves non-interactive readiness.
- Authorize sudo only for `sudo -n -- /usr/lib/wslaragon/agent-privilege-helper`; neither sudoers nor the helper may expose a shell, generic command runner, arbitrary utility, caller-selected path, Nginx payload, service, or permission operation.
- Implement a newline-delimited, single-record JSON protocol with version `1` and only `ready`, `apply_registration`, and `remove_registration` operations. Bound request size and response shape, emit diagnostics only on stderr, and return stable non-secret error codes.
- Add `PrivilegeClient` in `src/wslaragon/services/agent_privilege.py` to use the fixed sudo invocation, one bounded request/response record, schema validation, timeout handling, stderr redaction, and safe error mapping. It must never use a shell, `sudo -v`, or prompt-capable retry.
- Add hidden `site create --privilege-mode=interactive|agent`, defaulting to interactive. Interactive behavior retains `sudo -v` and `SudoKeepAlive`; agent mode requires an injected ready client, constructs neither, and never silently downgrades.
- Route only agent-mode selected registration/access behavior in `SiteManager`, `NginxManager`, and `SSLManager` through generated scalar helper requests. Preserve unprivileged scaffolding, certificates, database creation, and `~/.wslaragon` state ownership.
- For normal creation, submit one registration and persist state only after it succeeds. For headless creation, submit backend and frontend registrations; if the second fails, remove only the completed derived registration, preserve scaffold/certificates/database for repair, and do not commit user state.
- Replace the MCP unconditional response only when the complete safe route is covered: readiness success invokes the existing normal/headless argument permutations plus `--privilege-mode=agent`; readiness failure remains a terminal stable JSON-string response and never calls `_run_interactive`.
- Reconcile legacy MCP and CLI tests with the explicit two-mode contract, and provision declared runtime/dev dependencies so configured pytest coverage options and `dotenv`-dependent MCP tests can run.
- Add focused unit tests for helper boundary validation, bootstrap ordering and ownership conflicts, client protocol handling, mode separation, normal/headless registration and cleanup, MCP mappings, and unrelated MCP-tool non-expansion. Add native-Ubuntu integration coverage with a dedicated test user.

### Safe privilege boundary

The helper accepts only validated scalar fields and reconstructs all privileged destinations and configuration from root-owned bootstrap configuration and fixed templates. It must reject unknown fields, multiple records, traversal, symlinks, invalid names/types/ports, outside-root layouts, non-native platforms, raw commands, paths, content, and service actions.

`apply_registration` may perform only derived Nginx configuration/link changes, exact managed native-hosts entries, the fixed access policy for the validated generated root, `nginx -t`, and `systemctl reload nginx`. `remove_registration` may remove only those derived, feature-managed artifacts. The initial MCP path supports native Ubuntu; WSL Windows-host elevation returns `platform_unsupported` until separately designed.

### Non-goals

- Do not run MCP, CLI, or a daemon as root, accept sudo passwords over stdio, or invoke bootstrap from MCP.
- Do not grant agent privileges to delete, service management, PHP, MySQL, SSL setup, generic Nginx configuration, backups, agent tools, or any other MCP operation.
- Do not replace the legacy interactive privilege path outside explicitly selected agent-mode site creation.
- Do not migrate, overwrite, or remove broad legacy `/etc/sudoers.d/wslaragon` rules by default.
- Do not remove user project files, certificates, databases, or user state during helper disable or registration rollback.
- Do not support WSL Windows-host mutations in this first agent boundary.

## Affected areas

| Area | Change |
| --- | --- |
| `scripts/agent-privilege-helper.py` | New root-side allowlisted protocol, validation, derived mutations, and stable results. |
| `scripts/agent-privilege-setup.sh` | New administrator-only install/status/disable lifecycle and conflict gates. |
| `src/wslaragon/services/agent_privilege.py` | New unprivileged fixed-invocation client and protocol models. |
| `src/wslaragon/mcp/server.py` | Ready-path creation routing and stable denied/failure mapping while preserving the fail-closed guard until activation is safe. |
| `src/wslaragon/cli/site_commands.py` | Explicit privilege-mode selection with strict interactive/agent separation. |
| Site, Nginx, and SSL services | Agent-only adapter injection, helper registration, and bounded headless rollback. |
| `tests/unit/` and native integration tests | Reconciled legacy expectations plus protocol, isolation, cleanup, and regression coverage. |
| Project environment/dependency setup | Install declared `.[dev]` dependencies, including `pytest-cov`, and runtime dependency `python-dotenv` before claiming configured suite/coverage results. |

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| The helper becomes indirect generic-root access. | Use a finite versioned schema, fixed executables/templates, root-owned configuration, strict scalar validation, containment/no-follow checks, and no caller-provided commands or content. |
| MCP reaches interactive sudo before all routing is safe. | Keep the existing unconditional fail-closed guard until helper, bootstrap, client, and agent mode are delivered and covered as one activation boundary. |
| Bootstrap overwrites foreign or legacy authorization. | Default to a new dedicated fragment; stop for a TTY decision before replacing a foreign helper, dedicated artifact, or migrating/overwriting legacy policy. |
| Partial registration leaves a confusing site state. | Roll back only known completed derived registration, delay state commit, preserve unprivileged artifacts for repair, and return phase-specific safe failures. |
| Legacy tests mask a regression or environment failures mask suite status. | Replace obsolete creation expectations with ready/denied mode tests and restore declared dev/runtime dependencies before full-suite and coverage claims. |
| Platform behavior crosses an unsafe Windows hosts boundary. | Fail closed with `platform_unsupported` outside native Ubuntu and defer a Windows-host privilege design. |

## Rollback

1. Use the TTY-only disable operation to remove the verified feature-owned sudoers fragment before the verified helper.
2. Revert agent client/routing code if required; without the dedicated sudoers authorization, MCP creation safely returns setup-required rather than falling back to interactive sudo.
3. Preserve legacy sudoers rules, foreign-owned artifacts, user project files, certificates, databases, and user state.
4. For an individual failed registration, use `remove_registration` only for derived feature artifacts; leave scaffold repair to the invoking user or administrator.

## Success criteria

- [ ] The existing MCP guard remains unconditional and fail-closed until the full helper/bootstrap/client/agent-routing activation path is present and tested together.
- [ ] A TTY-only bootstrap installs and verifies the root-owned fixed helper before a dedicated `0440` sudoers rule, validates the rule with `visudo -cf`, proves `sudo -n` readiness, and refuses implicit foreign/legacy replacement or migration.
- [ ] Disable removes only verified feature-owned artifacts, in sudoers-first order, and preserves legacy policy and user assets.
- [ ] The helper accepts exactly one bounded version-1 JSON record for only `ready`, `apply_registration`, or `remove_registration`, rejects unsafe input/layouts, and cannot execute caller-selected commands, paths, content, utilities, or services.
- [ ] The client uses only `sudo -n -- /usr/lib/wslaragon/agent-privilege-helper`, validates one response record, redacts diagnostics, and exposes stable safe failures for denied, missing, malformed, timeout, and operation-failure cases.
- [ ] Interactive CLI creation retains `sudo -v` and `SudoKeepAlive`, while agent mode constructs neither, requires the client, and has no interactive downgrade.
- [ ] Ready MCP normal and headless creation pass the historical argument permutations plus `--privilege-mode=agent`; denied/not-ready paths return stable setup/authorization responses and do not call CLI or interactive execution.
- [ ] Normal creation registers once and commits user state after success; headless creation performs two registrations and removes only the successful derived registration if the second fails, preserving user-owned artifacts.
- [ ] Unrelated MCP tool privileges and their existing behavior remain unchanged, and WSL host elevation is rejected with `platform_unsupported`.
- [ ] Legacy MCP and CLI creation tests are reconciled to the mode contract, declared dev/runtime dependencies are installed, and the configured unit suite and 90% coverage command can complete before release.
- [ ] A native-Ubuntu dedicated-user integration run proves bootstrap, non-interactive readiness, normal creation, headless second-registration rollback, and disable.

## Proposal question round

This delegated proposal was prepared without a live question round. These questions are intended to improve the PRD by clarifying business rules, user impact, edge cases, and product tradeoffs before design/apply:

1. Should `privilege_setup_required` be a recoverable MCP tool outcome that allows an automation workflow to continue, or a workflow-blocking error?
2. Is native Ubuntu-only agent creation acceptable for the first release while WSL Windows-host changes return `platform_unsupported`?
3. When registration fails after scaffolding, is preserving the scaffold, certificates, and database for repair the desired product behavior, or should users be offered an explicit cleanup choice?
4. Should the dedicated new sudoers fragment remain the default even when legacy broad rules continue to exist for interactive commands?

**Current assumptions:** setup-required is actionable and non-interactive; native Ubuntu is the supported initial platform; repairable user artifacts are preserved after registration failure; and legacy policy is preserved by default.
