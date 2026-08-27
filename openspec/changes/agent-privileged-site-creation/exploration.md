# Exploration: Agent-Privileged Site Creation

## Context and successor boundary

- Successor change: `agent-privileged-site-creation`.
- This exploration reuses the prior `agent-safe-privilege-setup` records as evidence and does not alter them.
- The prior authorized slice implemented only a fail-closed MCP readiness probe in `src/wslaragon/mcp/server.py`. Both `create_site` and `create_headless_site` invoke `sudo -n -- /usr/lib/wslaragon/agent-privilege-helper` with one fixed `{"version":1,"op":"ready"}` record, then always return `privilege_setup_required`, including when the probe succeeds. Therefore neither MCP creation path presently creates a site.
- Delivery remains OpenSpec, ask-on-risk, automatic session preflight, and a 400-line review budget. No implementation was performed.

## Current route and gap

```text
MCP create tool
  -> fixed non-interactive readiness probe
  -> unconditional privilege_setup_required (current terminal state)

Needed successor route
MCP create tool
  -> PrivilegeClient ready (sudo -n, fixed helper)
  -> wslaragon site create ... --privilege-mode=agent
  -> unprivileged CLI/SiteManager scaffolding, certificates, database, user state
  -> PrivilegeClient apply_registration (one request per normal/headless site)
  -> root-owned helper validates and updates derived hosts/Nginx/access policy
  -> persist state only after registration success; bounded registration cleanup on failure
```

The legacy CLI route in `src/wslaragon/cli/site_commands.py` runs interactive `sudo -v`, wraps create work in `SudoKeepAlive`, and delegates to `SiteManager`. Its downstream `SiteManager`, `NginxManager`, and `SSLManager` perform scattered direct `sudo` calls for Nginx configuration, hosts, cleanup, ownership, ACLs, and modes. Calling that route from stdio MCP would reintroduce an interactive password path, so the agent route must be explicit and must not fall back to it.

## Work map

| Component | Required successor work | Current evidence |
|---|---|---|
| Root helper | Add immutable `scripts/agent-privilege-helper.py`, installed at `/usr/lib/wslaragon/agent-privilege-helper` as root-owned `0755`; accept exactly one version-1 JSON request and only `ready`, `apply_registration`, and `remove_registration`. Derive all destinations/configuration and reject raw commands, payloads, paths, unknown fields, traversal, symlinks, invalid names/types/ports, non-native platform, and outside-root layouts. Fixed actions are managed native hosts mutation, Nginx config/link, constrained access policy, `nginx -t`, and `systemctl reload nginx`. | No helper source or privilege tests exist. Existing readiness probe assumes this fixed path. |
| Bootstrap lifecycle | Add `scripts/agent-privilege-setup.sh` with TTY-only `bootstrap`, `status`, and `disable`. Stage and verify helper ownership/mode/digest before installing a dedicated `0440` sudoers fragment, validate staged policy with `visudo -cf`, then test non-interactive ready. Disable must remove only verified feature artifacts. | `scripts/install.sh` and `scripts/setup-env.sh` write incompatible broad legacy `/etc/sudoers.d/wslaragon` rules. Preserve them by default; ask before migration, overwrite, foreign-path replacement, or other ownership conflict. |
| Unprivileged client | Add `src/wslaragon/services/agent_privilege.py` to invoke only `sudo -n -- /usr/lib/wslaragon/agent-privilege-helper`, send/receive one bounded newline JSON record, validate response schema, redact stderr, and map setup/authorization/helper failures to stable safe codes. It must never use a shell or `sudo -v`. | MCP duplicates a boolean readiness probe; no reusable client/models exist. |
| CLI agent-mode selection | Add hidden `--privilege-mode=interactive|agent` to `site create`, defaulting to interactive. Interactive preserves the `sudo -v` and `SudoKeepAlive` behavior. Agent mode requires an injected ready client, constructs neither `sudo -v` nor `SudoKeepAlive`, and reports safe failures without downgrade. | `site_commands.create` always creates ordinary managers then calls `sudo -v` before normal/headless validation and creation. |
| Site/SSL/Nginx routing | Inject/use the client only in agent mode. Keep scaffolds, certificates, database work, and `~/.wslaragon` state unprivileged. Replace agent-mode calls to `SSLManager.add_to_hosts`, `NginxManager.add_site/remove_site`, and `SiteManager.fix_permissions` with generated scalar registration/access requests. Normal creation submits one registration. Headless creation submits backend then frontend registrations; second-registration failure removes only successful derived registration, while preserving user scaffold/certificates/database for repair and delaying registry commit. | `sites.py` directly invokes sudo `rm`, `chown`, `setfacl`, `find`, and `chmod`; `nginx.py` directly uses sudo tee/ln/rm/nginx/systemctl; `ssl.py` directly changes native `/etc/hosts`. WSL hosts elevation is not safely covered by this boundary, so the initial agent flow should return `platform_unsupported` there. |
| MCP continuation | Replace unconditional setup-required behavior only after helper/client/CLI routing is covered. On ready, construct the historical normal/headless CLI argument sets plus `--privilege-mode=agent`; on not-ready/denied/malformed results, return stable JSON-string safe errors and do not call `_run_interactive`. Other MCP tools remain outside this authorization scope. | Current guard is fail-closed and correctly prevents the legacy route, but ignores a successful probe. |

## Legacy MCP test reconciliation

`tests/unit/test_mcp_server.py` still contains the previous wrapper contract: normal-create success/failure and flag-construction tests around lines 599–1289, plus headless success/failure/argument tests around lines 1293–1360. These expect `_run` calls, legacy command arguments, and success text, while the current implementation correctly bypasses them. The prior verify report recorded 25 resulting creation-behavior failures in the module-level run.

The successor must replace/reconcile those expectations rather than merely restoring them:

1. Keep readiness-denied tests asserting the exact setup-required contract and no `_run`/`_run_interactive` call.
2. Add ready-path normal and headless cases asserting the complete legacy argument permutations plus `--privilege-mode=agent`.
3. Assert ready mode never triggers interactive sudo, stdin password flow, or `SudoKeepAlive` downstream.
4. Cover authorization denial, missing helper, malformed/multiple helper records, timeout, and helper operation failures with stable safe MCP responses.
5. Retain unrelated MCP tool expectations to prove the dedicated helper privilege does not spread to delete, services, PHP, MySQL, Nginx, SSL, or agent tools.

`tests/unit/test_site_commands.py` likewise expects `sudo -v` and `SudoKeepAlive` for ordinary and headless creates. Those become explicit interactive-mode regression tests, supplemented with agent-mode tests that assert neither occurs and that selected managers receive an agent client.

## Missing test dependencies and validation limitation

The configured pytest options in `pyproject.toml` require `pytest-cov`, but it is absent in the recorded environment; thus `pytest tests/unit/ -v --tb=short` stops at argument parsing. `pytest-cov>=4.1.0` is declared only in the `dev` optional dependency group. Five unrelated MCP module tests also fail at runtime because `dotenv` is unavailable, although the project declares `python-dotenv>=1.0.0` as a runtime dependency. The successor needs a provisioned project/dev environment before it can claim the configured unit suite or 90% coverage result; dependency installation is environment setup, not a production-code change.

## Test scope and rollout risks

Required focused coverage spans client protocol parsing/redaction, helper validation and confined filesystem effects, bootstrap ordering/conflicts/disable guard, Click mode separation, normal/headless adapter and rollback behavior, MCP ready/denied mapping, and legacy MCP argument regression reconciliation. Native-Ubuntu integration should additionally prove bootstrap, `sudo -n` readiness, normal creation, headless second-registration rollback, and disable with a dedicated test user.

This is not safely one 400-line implementation review. The prior design estimated roughly 900 changed lines across non-overlapping helper, bootstrap, client/routing, adapter, and test work. A safe successor plan should split by independently secure deliverable boundaries, while retaining the current unconditional fail-closed guard until helper/bootstrap and agent-mode routing land together. Do not install any authorization whose companion agent route is absent, and do not activate routing that can call a missing or untested helper.

## Risk gates and rollback

Ask before bootstrap replaces a foreign-owned helper, overwrites/migrates legacy `/etc/sudoers.d/wslaragon`, or changes an existing dedicated artifact. Default to a new dedicated fragment and preserve legacy policy. Rollback removes the verified dedicated sudoers fragment before the verified helper; it does not remove legacy sudoers rules, user project files, certificates, databases, or state.
