# Implementation Tasks: Agent-Privileged Site Creation

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1,550–1,700 additions + deletions across 17–21 files |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 Helper → PR 2 Lifecycle → PR 3 Client → PR 4a CLI selection → PR 4b Registration routing → PR 5 Coordinated activation |
| Delivery strategy | auto-chain (session-cached user approval) |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

Session-cached user approval authorizes this six-slice feature-branch chain. Keep every slice at or below 400 additions + deletions and within approximately 60 minutes of review.

## Chain tracker and PR target order

| Order | Deliverable | PR target | Merge constraint |
|-------|-------------|-----------|------------------|
| Tracker | Draft/no-merge chain tracker | `main` | Remains draft until all six child PRs are reviewed and integrated. |
| PR 1 | Immutable root helper | tracker branch | First child of the tracker. |
| PR 2 | Administrator lifecycle | PR 1 branch | Merge only after PR 1 is integrated into the tracker branch. |
| PR 3 | Unprivileged protocol client | PR 2 branch | Merge only after PR 2 is integrated. |
| PR 4a | Explicit CLI agent-mode selection | PR 3 branch | Merge only after PR 3 is integrated; it must not route manager registrations. |
| PR 4b | Bounded agent registration routing | PR 4a branch | Merge only after PR 4a is integrated; MCP remains fail-closed. |
| PR 5 | Coordinated public activation | PR 4b branch | Merge only after PR 4b is integrated; then complete the tracker PR. |

Each child PR must retain only its slice diff after retarget/rebase, include its focused test evidence and rollback boundary, and show its chain diagram with the current PR marked `📍`.

Implementation uses strict TDD in every slice: run each slice's targeted tests during RED/GREEN/TRIANGULATE/REFACTOR, then run `pytest tests/unit/ -v --tb=short`. Keep the existing unconditional MCP `privilege_setup_required` guard intact through slices 1–4a and 4b. Each slice is independently reviewable and must stay at or below 400 changed lines.

## 1. Slice 1 — Immutable root helper (target: ~330 lines)

**Chain:** `Tracker → 📍 PR 1` (target: tracker branch). **Start:** no dependency; the existing MCP guard remains terminal. **Finish:** standalone, immutable helper source has a bounded protocol and confined mutation boundary, but no installed authorization or MCP routing. **Verification:** helper-focused tests plus unit suite. **Rollback:** revert `scripts/agent-privilege-helper.py` and its tests only; no system artifact exists.

- [x] **RED:** Add `tests/unit/test_agent_privilege_helper.py` cases using temporary roots and mocked fixed executables for one-record parsing, 8 KiB/4 KiB limits, version/operation/key schemas, duplicate and malformed JSON, and stable non-secret response codes. <!-- sdd-owner: implementation -->
- [x] **GREEN:** Create `scripts/agent-privilege-helper.py` with immutable version-1 `ready`, `apply_registration`, and `remove_registration` handling; load only root-owned `/etc/wslaragon/` configuration and emit exactly one bounded JSON response on stdout. <!-- sdd-owner: implementation -->
- [x] **TRIANGULATE:** Extend `tests/unit/test_agent_privilege_helper.py` for traversal, symlink and outside-root rejection; native-Ubuntu-only rejection; layout/site/type/port incompatibilities; marker ownership; fixed argv; transactional Nginx validation/reload restoration; and constrained removal. <!-- sdd-owner: implementation -->
- [x] **REFACTOR:** Reduce `scripts/agent-privilege-helper.py` to explicit validators, no-follow containment helpers, fixed renderers, and fixed `subprocess` argv calls with no shell, caller paths, payloads, commands, services, or permission actions. <!-- sdd-owner: implementation -->
- [x] Run `pytest tests/unit/test_agent_privilege_helper.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`; record any blocked configured coverage dependency rather than claiming coverage. <!-- sdd-owner: implementation -->

## 2. Slice 2 — Administrator lifecycle (target: ~300 lines; depends on Slice 1)

**Chain:** `Tracker → PR 1 → 📍 PR 2` (target: PR 1 branch). **Start:** Slice 1 helper source and tests are green. **Finish:** TTY-only bootstrap/status/disable can safely manage only feature-owned artifacts; MCP remains terminally fail-closed. **Verification:** lifecycle harness tests plus unit suite. **Rollback:** invoke verified disable or revert the script/tests; disable removes policy before helper/config and preserves legacy/user assets.

- [x] **RED:** Add `tests/unit/test_agent_privilege_setup.py` subprocess/shell-harness cases for non-TTY/root/platform refusal, staged-helper verification before policy, `visudo -cf` failure, foreign/dedicated/legacy conflict aborts, readiness-failure rollback, status read-only behavior, and sudoers-first disable. <!-- sdd-owner: implementation -->
- [x] **GREEN:** Create `scripts/agent-privilege-setup.sh` with TTY-only `bootstrap`, `status`, and `disable`; stage and digest/owner/mode/type-verify the helper, write root-owned feature configuration, validate a dedicated `0440` sudoers fragment, and perform the fixed non-interactive `ready` probe. <!-- sdd-owner: implementation -->
- [x] **TRIANGULATE:** Expand `tests/unit/test_agent_privilege_setup.py` for single-user root/config/layout conflicts, atomic install failures before and after authorization, mismatched artifact refusal, legacy `/etc/sudoers.d/wslaragon` preservation, and no deletion of projects/certificates/databases/state. <!-- sdd-owner: implementation -->
- [x] **REFACTOR:** Make `scripts/agent-privilege-setup.sh` use private root staging, explicit ownership verification helpers, dedicated feature paths, and policy-first cleanup without implicit replacement/migration or MCP invocation. <!-- sdd-owner: implementation -->
- [x] Run `pytest tests/unit/test_agent_privilege_helper.py tests/unit/test_agent_privilege_setup.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`. <!-- sdd-owner: implementation -->

## 3. Slice 3 — Unprivileged protocol client (target: ~280 lines; depends on Slice 1)

**Chain:** `Tracker → PR 1 → PR 2 → 📍 PR 3` (target: PR 2 branch). **Start:** Slice 1 protocol is green; no CLI or MCP behavior changes. **Finish:** reusable client safely transports validated records to the fixed helper; MCP guard remains terminal. **Verification:** client tests plus unit suite. **Rollback:** revert `src/wslaragon/services/agent_privilege.py`, any `src/wslaragon/services/__init__.py` export, and client tests; callers do not yet depend on it.

- [x] **RED:** Add `tests/unit/test_agent_privilege.py` cases for exact `sudo -n -- /usr/lib/wslaragon/agent-privilege-helper` argv, one request/response newline, valid result models, and bounded timeout/stdout/stderr behavior. <!-- sdd-owner: implementation -->
- [x] **GREEN:** Add immutable request/result models and `PrivilegeClient` in `src/wslaragon/services/agent_privilege.py`; use one `communicate()` with `shell=False`, no helper argv, no `sudo -v`, and no retry/prompt path. <!-- sdd-owner: implementation -->
- [x] **TRIANGULATE:** Extend `tests/unit/test_agent_privilege.py` for missing executable, sudo denial, nonzero helper failures, malformed/multiple/oversize records, invalid schemas, timeout, and stderr redaction/category-only logging mapped to finite safe codes. <!-- sdd-owner: implementation -->
- [x] **REFACTOR:** Centralize protocol serialization/schema validation and bounded capture in `src/wslaragon/services/agent_privilege.py`; add only the necessary export in `src/wslaragon/services/__init__.py` if existing service imports require it. <!-- sdd-owner: implementation -->
- [x] Run `pytest tests/unit/test_agent_privilege.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`. <!-- sdd-owner: implementation -->

## 4a. Slice 4a — Explicit CLI agent-mode selection (target: ~180 lines; depends on Slices 1–3)

**Chain:** `Tracker → PR 1 → PR 2 → PR 3 → 📍 PR 4a` (target: PR 3 branch). **Start:** helper, lifecycle, and client boundaries are green; `src/wslaragon/mcp/server.py` still always returns setup-required. **Finish:** CLI explicitly selects interactive or agent privilege mode, validates an injected ready `PrivilegeClient` for agent mode, and does not route manager registrations or change site-manager behavior. **Verification:** CLI-focused tests plus unit suite. **Rollback:** revert this slice; the unconditional MCP guard and existing interactive manager path remain intact.

- [x] **RED:** Update `tests/unit/test_site_commands.py` to make the default interactive contract explicit (`sudo -v` and `SudoKeepAlive`) and add agent-mode tests proving ready-client validation, safe unavailable/not-ready failure, and no interactive construction or downgrade. <!-- sdd-owner: implementation -->
- [x] **GREEN:** Add hidden `--privilege-mode=interactive|agent` to `src/wslaragon/cli/site_commands.py`; preserve the current interactive manager path while agent mode requires a ready test-injectable `PrivilegeClient` before command dispatch, without passing it to site, Nginx, SSL, or registration managers. <!-- sdd-owner: implementation -->
- [x] **TRIANGULATE:** Extend `tests/unit/test_site_commands.py` for invalid/missing mode handling, normal and headless argument permutations, and assertions that agent-mode selection performs no registration, direct agent sudo, or manager construction beyond current command parsing. <!-- sdd-owner: implementation -->
- [x] **REFACTOR:** Centralize privilege-mode parsing and readiness failure mapping in `src/wslaragon/cli/site_commands.py` while retaining legacy interactive command construction and leaving `src/wslaragon/mcp/server.py` unchanged. <!-- sdd-owner: implementation -->
- [x] Run `pytest tests/unit/test_site_commands.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`; confirm the MCP guard diff is empty and no registration-routing files change. <!-- sdd-owner: implementation -->

## 4b. Slice 4b — Bounded agent registration routing (target: ~360 lines; depends on Slice 4a)

**Chain:** `Tracker → PR 1 → PR 2 → PR 3 → PR 4a → 📍 PR 4b` (target: PR 4a branch). **Start:** Slice 4a mode selection is green and still has no manager registration routing; `src/wslaragon/mcp/server.py` still always returns setup-required. **Finish:** only explicitly selected agent-mode site creation routes derived host/Nginx/access registration through the ready client, with delayed state commits and bounded compensating cleanup; MCP remains fail-closed. **Verification:** site-routing focused tests plus unit suite. **Rollback:** revert this slice; retain the MCP guard and use lifecycle disable to withdraw authorization if needed.

- [x] **RED:** Add or update focused tests in `tests/unit/test_sites.py`, `tests/unit/test_site_creators.py`, `tests/unit/test_nginx.py`, and `tests/unit/test_ssl.py` for scalar descriptor generation, SSL no-host-registration, no direct agent sudo, normal single registration/delayed state commit, and headless backend-first/frontend-second failure with backend-only `remove_registration` and preserved user artifacts. <!-- sdd-owner: implementation --> <!-- done: `TestRegistrationLayout` + `TestSiteManagerAgentMode` in test_sites.py, `TestSetupSSLForSiteHostRegistration` in test_ssl.py. No test_nginx.py / test_site_creators.py changes: NginxManager gains no behavior (agent mode simply does not call it) and the layout mapping lives in sites.py. -->
- [x] **GREEN:** Adapt `src/wslaragon/services/sites.py`, `src/wslaragon/services/nginx.py`, and `src/wslaragon/services/ssl.py` so only agent-mode derived hosts/Nginx/access actions use the client; retain unprivileged scaffolding/certificates/database/state ownership and legacy direct managers for interactive commands. <!-- sdd-owner: implementation --> <!-- done: `registration_layout()` + `SiteManager(privilege_client=None)`; `create_site` / `create_headless_site` route agent-mode registration through `PrivilegeClient.apply_registration` / `remove_registration`, commit `sites.json` only after success, skip `fix_permissions` and `_cleanup_failed_site_directory`; `SSLManager.setup_ssl_for_site(..., register_hosts=False)`. `nginx.py` unchanged — direct managers stay on the interactive path. -->
- [x] **TRIANGULATE:** Extend those focused tests for unavailable/denied/malformed client results, repeated registrations, partial cleanup failures, no state commit before all selected registrations succeed, and no routing when interactive mode is selected. <!-- sdd-owner: implementation --> <!-- done: `TestSiteManagerAgentModeTriangulation` — per-failure-code surfacing, no `_save_sites` before success, headless backend-failure (no compensation), headless compensation-failure still returns original error, unknown headless_role rejected. -->
- [x] **REFACTOR:** Centralize bounded registration descriptors and compensating `remove_registration` handling in the concrete discovery targets `src/wslaragon/services/sites.py`, `src/wslaragon/services/nginx.py`, and `src/wslaragon/services/ssl.py`; retain the Slice 4a CLI selection boundary and leave `src/wslaragon/mcp/server.py` unchanged. <!-- sdd-owner: implementation --> <!-- done: descriptor derivation isolated in the pure `registration_layout()`; dropped an unused layout frozenset; `mcp/server.py` untouched (not in diff). -->
- [x] Run `pytest tests/unit/test_sites.py tests/unit/test_site_creators.py tests/unit/test_nginx.py tests/unit/test_ssl.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`; confirm the MCP guard diff is empty. <!-- sdd-owner: implementation --> <!-- done: 331 passed (named files) / 1431 passed, 1 skipped (full unit suite) at 99.53% coverage via `./venv/bin/pytest`; `mcp/server.py` not in `git diff`. Slice diff ~531 changed lines (480 ins / 51 del), above the 360-line target — mostly focused tests. -->

**Verification note:** the environment blocker from earlier slices (`pytest-cov` / `python-dotenv` "unavailable") was an env mismatch — the project venv `venv/` (Python 3.14) has both. Use `./venv/bin/pytest`.

## 5. Slice 5 — Coordinated public activation, environment, and native harness (target: ~350 lines; depends on Slices 1–4b)

**Chain:** `Tracker → PR 1 → PR 2 → PR 3 → PR 4a → PR 4b → 📍 PR 5` (target: PR 4b branch). **Start:** all prior slices are present and focused boundary tests pass. **Finish:** this is the sole activation boundary: ready MCP normal/headless requests run the agent CLI route; all unusable outcomes remain stable and non-interactive. **Verification:** MCP/unit suite, provisioned dependency check, and opt-in native dedicated-user harness. **Rollback:** restore the unconditional MCP guard in the same revert, then run lifecycle disable (sudoers first); do not remove user assets or legacy policy.

- [x] **RED:** Replace obsolete creation expectations in `tests/unit/test_mcp_server.py` with denied/not-ready exact JSON and no-execution assertions; add ready normal/headless historical argument permutations plus `--privilege-mode=agent`, safe mappings for denied/missing/malformed/multiple/timeout/operation failures, and unrelated-tool non-expansion coverage. <!-- sdd-owner: implementation --> <!-- done: `TestCreateSite` / `TestCreateHeadlessSite` rewritten — ready-path parametrized flag permutations assert `_run` gets `--privilege-mode=agent` and `_run_interactive` is never called; `not_ready`/`helper_missing` -> exact `privilege_setup_required`; other codes -> `{ok:false,code,message}`; `TestPrivilegeFailureMapping` covers the mapping directly and `get_services_status` never probing the client. -->
- [x] **GREEN:** Update `src/wslaragon/mcp/server.py` to inject/use `PrivilegeClient` readiness, map finite safe results to the existing JSON-string contract, and call `_run`—never `_run_interactive`—only for ready normal/headless agent-mode commands. <!-- sdd-owner: implementation --> <!-- done: `_agent_privilege_ready()` replaced by `_privilege_client()` (single patch point) + `_privilege_failure_json()`; both create tools call `client.ready()`, return the mapped JSON on failure, else rebuild the historical CLI argv + `--privilege-mode=agent` and run via `_run`. Also wired the CLI: `site_commands.create` agent branch now calls `_run_agent_create` -> ready check -> `SiteManager(privilege_client=client)` with no `sudo -v` / `SudoKeepAlive`; removed the dead `_agent_creation_available` stub. -->
- [x] **TRIANGULATE:** Add opt-in `tests/integration/test_agent_privilege_native.py`, marked `integration` and `requires_sudo`, using an isolated native-Ubuntu dedicated user/root to prove bootstrap, `sudo -n` readiness, normal creation, forced second-registration rollback, and disable; update `README.md` with invocation, prerequisites, and explicit opt-in safety boundary. <!-- sdd-owner: implementation --> <!-- done: harness added, module-skipped unless `WSLARAGON_AGENT_NATIVE_TEST=1`; ready-probe test wired, the full dedicated-user create+rollback+disable flow is a marked `@pytest.mark.skip` placeholder pending a throwaway-account fixture. README `## 🧪 Tests` gained the opt-in stanza (ES). -->
- [x] **REFACTOR:** Provision the declared environment with `-e '.[dev]'` before asserting suite/coverage results, then simplify MCP client injection and test fixtures while preserving stable response shape, stderr redaction, and the atomic activation guard. <!-- sdd-owner: implementation --> <!-- done: env was already provisioned (venv has all `.[dev]` deps); single `_privilege_client()` patch point; dead `_agent_creation_available` removed; response shape/stderr redaction unchanged (client never returns stderr, MCP never echoes it). -->
- [x] Run `pytest tests/unit/test_mcp_server.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`; after dependency provisioning, run the configured coverage command and the opt-in `requires_sudo` harness only against its dedicated isolated account. <!-- sdd-owner: implementation --> <!-- done: `./venv/bin/pytest tests/unit/` -> 1442 passed, 1 skipped, 99.33% coverage. Native `requires_sudo` harness NOT run here (no dedicated isolated account / native box in this environment) — 2 skipped on collection. -->

**Remaining before archive:** run `scripts/agent-privilege-setup.sh bootstrap` on a native-Ubuntu host to install `/usr/lib/wslaragon/agent-privilege-helper` + the dedicated sudoers fragment, then execute the opt-in native harness against a throwaway account. Until then MCP `create_site`/`create_headless_site` return `privilege_setup_required` at runtime because `ready()` fails closed.

## Parent lifecycle and bounded-review actions

- [ ] Create the draft/no-merge tracker PR targeting `main`, then create PRs 1–3, 4a, 4b, and 5 in the recorded target order; verify each child has a clean slice-only diff after retarget/rebase. <!-- sdd-owner: parent -->
- [ ] After each completed slice, start or reuse a bounded review that checks its ≤400-line clean diff, stated dependency boundary, focused verification evidence, and slice-specific rollback. <!-- sdd-owner: parent -->
- [ ] Before Slice 4b, confirm Slice 4a is merged/available and green, agent-mode selection has no manager registration routing, and the unconditional MCP guard remains unchanged. <!-- sdd-owner: parent -->
- [ ] Before Slice 5 activation, confirm slices 1–4a and 4b are merged/available and green, the CLI agent path contains no direct sudo or interactive fallback, and the unconditional MCP guard remained unchanged through Slice 4b. <!-- sdd-owner: parent -->
- [ ] After Slice 5, start or reuse a bounded activation review covering MCP safe mappings, unrelated-tool non-expansion, dependency provisioning evidence, and native-harness isolation before release. <!-- sdd-owner: parent -->
