# Design: Agent-Privileged Site Creation

## Status and activation rule

This change extends the predecessor's readiness-only, fail-closed implementation. `create_site` and `create_headless_site` continue to call the current fixed readiness probe and always return `privilege_setup_required` through every preparatory slice. The MCP guard is changed **only in the final activation slice**, after the helper, administrator lifecycle, client, agent-only adapters, and their focused tests are merged and pass together. A ready probe alone is never an activation signal for the legacy route.

The repository has `src/wslaragon/`, not `packages/coding-agent`; this change is necessarily centered there.

## Architecture and ownership

```text
TTY administrator
  -> agent-privilege-setup.sh
  -> root-owned helper + root-owned feature configuration
  -> validated dedicated sudoers rule (only no-argument helper)

MCP stdio -> PrivilegeClient.ready() -> wslaragon site create --privilege-mode=agent
                                      -> CLI agent branch (second ready check)
                                      -> SiteManager unprivileged scaffold/cert/db
                                      -> PrivilegeClient.apply/remove_registration()
                                      -> sudo -n -- fixed root helper
                                      -> managed /etc/hosts, Nginx, access policy

Interactive CLI -> sudo -v + SudoKeepAlive -> existing direct privileged managers
```

| Boundary | Owns | Must not own |
| --- | --- | --- |
| `scripts/agent-privilege-setup.sh` | TTY gate, staging, feature config, dedicated sudoers lifecycle | MCP activation, legacy-policy migration, user assets |
| Installed helper | Protocol validation and all feature-owned root mutations | Arbitrary commands/paths/content, user scaffolding, certificates, database, state |
| `PrivilegeClient` | Fixed subprocess transport and safe error mapping | Shells, auth prompting/retry, privileged policy decisions |
| CLI mode selector | Explicit interactive versus agent construction | Silent fallback between modes |
| `SiteManager` agent adapter | Generate validated registration descriptors; commit/cleanup ordering | Direct sudo during agent creation |
| MCP server | Ready-first public result mapping and exact CLI argument construction | Interactive execution for either creation tool |

### Root-owned feature configuration

Bootstrap writes a root-owned regular configuration file under `/etc/wslaragon/` (mode `0644`, parent root-owned and non-writable by the enabled user). It records the bootstrapped Unix user, that user's resolved home, canonical project root, SSL directory, `.test` TLD, Nginx available/enabled directories, PHP-FPM socket/version, and the fixed feature artifact paths. It is the only configuration the helper reads; the helper never reads the caller's YAML, environment, current directory, or command-line paths.

Bootstrap derives these values from the administrator's explicit local installation and validates canonical absolute paths before writing. A bootstrap is single-user per feature configuration. A different user/root/layout is an ownership/configuration conflict requiring an explicit TTY disable/re-bootstrap decision, not a caller-selected helper parameter.

## Protocol contract

The client invokes exactly:

```text
sudo -n -- /usr/lib/wslaragon/agent-privilege-helper
```

with no helper argv and one UTF-8 JSON request terminated by one newline. The helper accepts at most one bounded record (design limit: 8 KiB request and 4 KiB response); EOF must immediately follow that newline. It writes one schema-valid response newline to stdout and only bounded, non-secret diagnostics to stderr.

Common response schema is exactly `{"version":1,"ok":boolean,"code":string}`; success has `code:"ok"`, failure uses a finite code set. No error includes a command, filesystem layout, subprocess stderr, secret, or caller payload.

| Operation | Exact request keys | Meaning |
| --- | --- | --- |
| `ready` | `version`, `op` | Read-only installation/platform/configuration readiness check. |
| `apply_registration` | `version`, `op`, `site`, `layout`, `ssl`, `php`, `proxy_port` | Create/update one derived registration. |
| `remove_registration` | `version`, `op`, `site`, `layout` | Remove only one verified feature-owned derived registration. |

`site` is a bounded normalized site name matching the existing label rules; `layout` is a closed enum: `normal-root`, `normal-public`, `normal-dist`, `headless-backend-root`, `headless-backend-public`, `headless-frontend-root`, and `headless-frontend-dist`. The helper derives the web root from bootstrapped project root plus this enum; it accepts no root, directory, hosts file, Nginx file/content, certificate path, service, command, API proxy, database, or permission argument. `ssl` and `php` are booleans. `proxy_port` is either null or an integer in 1024–65535. Layout constraints reject incompatible names (including a non-`api.` backend), PHP/proxy combinations, and any derived root that does not exist as a real directory strictly beneath the canonical configured project root.

Before every mutation, the helper verifies native Ubuntu (not WSL), root-owned configuration/artifact expectations, component containment using resolved paths and no-follow directory traversal, and expected feature markers. It rejects unknown/missing fields, duplicate keys, non-object values, multiple/empty/oversize records, malformed UTF-8/JSON, versions other than 1, and unsafe types before changing anything. Proposed stable failures are `not_ready`, `authorization_denied`, `helper_missing`, `protocol_invalid`, `request_invalid`, `platform_unsupported`, `layout_invalid`, `operation_failed`, and `timeout` (client-originated only).

### Root operations and transaction behavior

The standalone installed Python helper contains immutable fixed renderers; it does not import code from the mutable checkout. From the validated scalar descriptor and root configuration it renders the Nginx server block, selected certificate references, and managed hosts entries. It may only:

1. add/remove exact `127.0.0.1`/`::1` hosts entries carrying an unambiguous feature marker;
2. atomically create/remove the expected feature-marked Nginx available file and expected enabled symlink;
3. apply the fixed `www-data` ACL-or-chmod policy only beneath the derived generated root;
4. run fixed `nginx -t`, then fixed `systemctl reload nginx`.

It uses fixed executable paths/argument vectors, private root-owned temporary files, `lstat`/containment checks, and atomic replacement. It never uses a shell. `apply_registration` snapshots only the feature-owned artifacts it changes, validates Nginx, and reloads. On validation or reload failure it restores that snapshot and attempts a reload of the prior valid configuration; it reports a phase-specific non-secret `operation_failed`. `remove_registration` removes only matching marker-owned artifacts for the calculated registration and validates/reloads the resulting configuration; it never touches project trees, certificates, databases, or `sites.json`.

## Bootstrap, status, disable, and rollback

`agent-privilege-setup.sh bootstrap|status|disable` refuses non-TTY stdin/stdout, root-shell misuse, unsupported platform, and unapproved ownership conflicts. It requires an administrator-authenticated terminal; MCP neither invokes nor exposes it.

Bootstrap sequence:

```text
TTY preflight/conflict inspection
 -> create private root staging area
 -> install source as root:root regular 0755 staged helper
 -> verify lstat owner/mode/type and SHA-256 against source
 -> atomically install final helper; verify again
 -> atomically write/verify root feature configuration
 -> write dedicated staged sudoers fragment, root:root 0440
 -> visudo -cf staged fragment
 -> atomically install fragment; verify owner/mode/type/digest
 -> sudo -n -- helper < ready record
 -> report enabled only on schema-valid ready success
```

The dedicated fragment is separate from `/etc/sudoers.d/wslaragon` and matches only the bootstrapped user running the no-argument helper. A foreign helper, feature config, dedicated fragment, or legacy broad policy is never overwritten, migrated, or replaced implicitly. Bootstrap stops and presents the conflict and explicit choices in the TTY; default is abort. Failure before policy installation removes only newly staged/install artifacts. Failure after installation removes the verified dedicated fragment first, then the verified helper/config, and reports rollback failure if verification prevents removal.

`status` is read-only and reports verification state without secrets. `disable` re-verifies feature markers, owner, regular-file type, modes, and expected digest before removing the dedicated sudoers fragment, then helper/config. It refuses deletion on mismatch and never removes legacy rules or user files/certificates/databases/state. Operational rollback uses `disable` first; reverting client/MCP code thereafter remains fail closed because the dedicated authorization is gone.

## Client, CLI, and service design

`src/wslaragon/services/agent_privilege.py` provides immutable request/result models and `PrivilegeClient`. A single `communicate()` call uses the exact argument vector, a bounded timeout, `shell=False`, and bounded stdout/stderr capture. It validates return code and exactly one response record; stderr is logged only as redacted category/length, never returned to MCP/CLI. It maps OS missing executable, sudo denial, malformed/multiple output, timeout, and helper failures into the finite result codes and performs no retry, `sudo -v`, or password-capable call.

The hidden Click option `--privilege-mode=interactive|agent` defaults to `interactive`.

* Interactive branch keeps today's `sudo -v`, `SudoKeepAlive`, direct `SSLManager`/`NginxManager` behavior, and compatibility tests.
* Agent branch creates/receives a test-injectable `PrivilegeClient`, requires a successful ready result before manager construction, injects it into `SiteManager` and selected adapter calls, and constructs neither `SudoKeepAlive` nor `sudo -v`. It returns a safe error on unavailable client/readiness failure and cannot downgrade.
* In agent mode, certificate creation remains user-owned but `SSLManager.setup_ssl_for_site` gets a no-host-registration path. SiteManager converts its computed, validated site metadata to the scalar registration request; it never passes raw Nginx configuration or a path. Nginx direct methods remain used only by interactive/non-agent commands.

Normal agent creation performs existing unprivileged validation, scaffolding, certificate generation, and database work; then submits exactly one `apply_registration`, including the derived layout/profile. It calls the helper access policy as part of that single operation and writes `sites.json` only after success. Agent-mode failure preserves scaffold/certificate/database and returns repairable failure; it must not use `_cleanup_failed_site_directory` because that currently can call sudo.

Headless agent creation performs unprivileged root/back/front scaffolding, certificates, and database creation. It submits backend registration first and frontend registration second. If the second fails, it submits `remove_registration` for the successfully registered backend only; it does not remove frontend (which was never registered), project files, certificates, or database, and it leaves both state entries uncommitted. If cleanup also fails, return the original registration failure plus a non-secret cleanup status for administrator repair. Successful state persistence happens once after both registrations succeed.

## MCP activation and sequences

The final server implementation replaces `_agent_privilege_ready()` with an injected/testable `PrivilegeClient` readiness result. It serializes all denied/malformed/missing/timeout/platform failures as the existing stable JSON-string shape, using `privilege_setup_required` for absent/unconfigured setup and a finite mapped safe code otherwise. It never includes client stderr. It calls `_run`, not `_run_interactive`, only after ready and only with the historical exact normal/headless arguments plus `--privilege-mode=agent`.

### Normal creation

```text
MCP -> Client: ready
Client -> helper: sudo -n, ready JSON
helper --> Client: validated ready
MCP -> CLI: site create NAME <legacy flags> --privilege-mode=agent
CLI -> Client: ready (TOCTOU check)
CLI -> SiteManager: scaffold/cert/db (user-owned)
SiteManager -> Client -> helper: apply_registration(descriptor)
helper -> hosts/Nginx/access: validate, apply, nginx -t, reload
helper --> SiteManager: ok
SiteManager -> sites.json: commit
```

### Headless creation and bounded rollback

```text
MCP -> CLI(agent): headless historical flags + privilege mode
CLI/SiteManager: scaffold back/front, certs, database (user-owned)
SiteManager -> helper: apply backend
helper --> SiteManager: ok
SiteManager -> helper: apply frontend
helper --> SiteManager: operation_failed
SiteManager -> helper: remove backend only
SiteManager --> CLI/MCP: safe failed result; no sites.json commit
```

WSL and all non-native platforms fail at ready/registration with `platform_unsupported`; Windows host elevation is not attempted. The server leaves all unrelated MCP tools unchanged, including delete, services, PHP, MySQL, arbitrary Nginx configuration, SSL management, and agent tools.

## Tests and environment remediation

Provision the declared project environment before suite/coverage claims: create/use the project venv and install `-e '.[dev]'`, which supplies both `pytest-cov` and runtime `python-dotenv`. This is test-environment remediation, not a runtime dependency change because both are already declared in `pyproject.toml`.

Add helper unit tests using temporary roots and mocked fixed executables: exactly-one-record parsing, duplicate/unknown/unsafe fields, size bounds, traversal/symlink/outside-root rejection, non-native rejection, fixed argv only, marker ownership, transactional Nginx failure restoration, and constrained removal. Add bootstrap shell tests (or subprocess harness) for TTY refusal, stage/verify-before-policy ordering, `visudo` failure, foreign/legacy conflicts, readiness failure rollback, and sudoers-first disable.

Add client tests for exact invocation, one valid record, all malformed/multiple/timeout/missing/denied mappings, and stderr redaction. Rework `test_site_commands.py` fixtures so ordinary cases explicitly assert the interactive default (`sudo -v` and `SudoKeepAlive`), while agent cases assert injected client, no interactive calls, normal delayed state commit, headless second-registration backend-only cleanup, and preserved user assets.

Replace obsolete create assertions in `test_mcp_server.py` (currently expecting `_run` success despite the predecessor guard) with: denied setup exact JSON/no execution; ready normal/headless exact legacy permutations plus `--privilege-mode=agent`; mappings for denied/missing/malformed/multiple/timeout/operation failure; and no `_run_interactive`. Preserve unrelated-tool tests to demonstrate privilege non-expansion. Add a `requires_sudo` native-Ubuntu dedicated-user integration harness that bootstraps, verifies `sudo -n` ready, creates normal, forces headless second-registration rollback, disables, and confirms policy-first removal. It must be opt-in and never run against the developer's normal account/system paths.

## Reviewable delivery chain

All estimates include production and focused tests; each implementation PR stays below the 400 changed-line review budget. The predecessor MCP guard remains unchanged in slices 1–4.

| Slice | Boundary and files | Estimate | Gate |
| --- | --- | ---: | --- |
| 1 | Standalone helper, root-config format, helper unit harness/tests (`scripts/agent-privilege-helper.py`, new helper tests) | 330 lines / 3 files | Parser and confinement tests; no bootstrap or MCP change. |
| 2 | TTY lifecycle and bootstrap/disable tests (`scripts/agent-privilege-setup.sh`, shell/subprocess tests) | 300 lines / 2–3 files | Ordering/conflict/rollback tests; helper source is present, but MCP still terminally fails closed. |
| 3 | Client models/transport and tests (`services/agent_privilege.py`, exports, client tests) | 280 lines / 3 files | Exact sudo protocol and redaction tests; no CLI routing. |
| 4 | Hidden CLI mode, agent adapters in site/SSL/Nginx boundaries, lifecycle tests | 390 lines / 5–6 files | Both mode contracts and normal/headless cleanup pass; MCP guard unchanged. |
| 5 | MCP activation, legacy MCP-test migration, environment/integration runner/docs | 350 lines / 4–6 files | Re-run slices 1–4 focused tests, MCP ready/denied tests, provisioned unit suite, and native integration prerequisite; this is the only slice that removes unconditional terminal behavior. |

Total forecast: approximately 1,650 changed lines across 17–21 files, delivered as a dependency-ordered chained review. Slice 5 must not merge if any preceding slice is absent, has failing boundary tests, or the CLI agent path can reach a direct sudo call. If slice 5 is reverted independently, the predecessor unconditional guard is restored in the same revert before any helper authorization is relied upon.

## Rollout and acceptance

1. Ship source/tests through slices 1–4 with MCP creation still returning setup-required.
2. After final code review and test-environment provisioning, merge slice 5 as the atomic public activation boundary.
3. An administrator explicitly runs TTY bootstrap on native Ubuntu; rollout checks `status` and a non-interactive ready probe before use.
4. Monitor only stable codes and redacted categories; do not collect request payloads or stderr.
5. On defect, run TTY disable (sudoers first), then revert activation/routing. Existing user artifacts and legacy policy remain intact.

Acceptance requires the focused tests, provisioned configured unit/coverage command, and dedicated-user native Ubuntu integration to pass. A coverage percentage is not claimed until `pytest-cov` and `python-dotenv` are installed and pytest loads its configured options.
