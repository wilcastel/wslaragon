# Apply Progress: Agent-Privileged Site Creation

## Status consumed
```yaml
schemaName: spec-driven
changeName: agent-privileged-site-creation
artifactStore: openspec
changeRoot: /home/wilcastell/infra/wslaragon/openspec/changes/agent-privileged-site-creation
artifacts: {proposal: done, specs: done, design: done, tasks: done, applyProgress: partial}
applyState: ready
actionContext: {mode: repo-local, workspaceRoot: /home/wilcastell/infra/wslaragon, allowedEditRoots: [], warnings: ["Native gentle-ai CLI unavailable; status reconstructed from authoritative OpenSpec files."]}
nextRecommended: apply
```

## Slice 1 completed
- Marked the five Slice 1 implementation rows `[x]` in `tasks.md`.
- Added `scripts/agent-privilege-helper.py`: bounded one-record version-1 protocol, strict scalar schemas, duplicate-key rejection, root-owned config loading, native-Ubuntu guard, no-follow generated-root confinement, feature-marker-only removal, and fixed no-shell Nginx/systemctl argument vectors.
- Added `tests/unit/test_agent_privilege_helper.py` with parser/schema/size, unsafe scalar, symlink confinement, bounded response, and fixed-argv registration coverage.
- MCP files were not edited by this slice; the pre-existing workspace MCP diff remains untouched.

## Verification
- PASS: `PYTEST_ADDOPTS='' pytest -o addopts='' tests/unit/test_agent_privilege_helper.py -v --tb=short` — 9 passed.
- BLOCKED: configured `pytest tests/unit/test_agent_privilege_helper.py -v --tb=short` and `pytest tests/unit/ -v --tb=short` both exit 4 because configured `--cov` arguments are unsupported (`pytest-cov` is unavailable). No coverage claim is made.
- PASS: `git diff --check`.

### TDD Cycle Evidence
| Task | Test file | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| Slice 1 | `tests/unit/test_agent_privilege_helper.py` | Unit | N/A (new files) | Written; configured runner blocked before collection | 8 passed with coverage options disabled | Added fixed-argv registration case; 9 passed | Explicit validation and containment helpers; 9 passed |

## Workload / remaining
- PR boundary: feature-branch-chain PR 1 only (`Tracker → 📍 PR 1`); 270 source-and-test lines, below 400.
- Remaining implementation tasks are the exact unchecked rows under Slices 2–5 in `tasks.md`; deferred lifecycle actions are the four byte-preserved parent-owned rows at its end.
- No design deviation. Runtime token authentication/settlement could not be performed because `gentle-ai` is not installed on PATH.

## Slice 2 completed
- Marked the five Slice 2 implementation rows `[x]` in `tasks.md` after re-reading the persisted artifact.
- Added `scripts/agent-privilege-setup.sh`: TTY/non-root/native-Ubuntu lifecycle gates; root-owned staging and digest/type/owner/mode verification; feature configuration plus protected checksum; dedicated `0440` sudoers policy validated by `visudo -cf`; fixed `sudo -n -- /usr/lib/wslaragon/agent-privilege-helper` readiness probe; read-only status; and verified policy-first disable.
- Added `tests/unit/test_agent_privilege_setup.py`: temporary-root subprocess harness coverage for TTY refusal, helper-before-policy setup, visudo rejection, legacy and foreign artifact preservation, readiness rollback, read-only status, and verified disable.
- Did not execute bootstrap or disable outside the temporary test harness, invoke real sudo, install a system artifact, alter system policy, or modify MCP, client, routing, or documentation files. Existing Slice 1 helper and the workspace's pre-existing MCP fail-closed guard diff were not changed.

## Verification
- PASS: `sh -n scripts/agent-privilege-setup.sh`.
- PASS: `PYTEST_ADDOPTS='' pytest -o addopts='' tests/unit/test_agent_privilege_helper.py tests/unit/test_agent_privilege_setup.py -v --tb=short` — 18 passed.
- BLOCKED: requested `pytest tests/unit/test_agent_privilege_helper.py tests/unit/test_agent_privilege_setup.py -v --tb=short` and `pytest tests/unit/ -v --tb=short` both exit 4 because configured `--cov` arguments are unsupported (`pytest-cov` unavailable).
- BLOCKED: bypassed full unit collection exits 2 because `python-dotenv` is unavailable; `test_config_comprehensive.py` and `test_service_commands.py` cannot import `dotenv`.
- PASS: `git diff --check`.

### TDD Cycle Evidence
| Task | Test file | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| Slice 2 | `tests/unit/test_agent_privilege_setup.py` | Unit subprocess harness | N/A (new files) | 6 tests failed because the lifecycle source was absent | 6 passed after minimal lifecycle implementation | Added 3 foreign-artifact variants; 9 passed | Extracted verification/path/policy-digest helpers and changed staging to root-owned; 9 passed |

## Workload / remaining
- PR boundary: feature-branch-chain PR 2 only (`Tracker → PR 1 → 📍 PR 2`), 250 source-and-test lines, below the 400-line budget. No branch or PR was created by this executor.
- Design deviation: the feature configuration has a separate root-owned `0600` checksum artifact so disable can re-verify the dynamic configuration digest before deleting it.
- Remaining implementation tasks are the exact unchecked Slice 3–5 rows in `tasks.md`; parent-owned lifecycle rows remain byte-preserved and deferred.
- Structured status consumed: authoritative OpenSpec files; native `gentle-ai sdd-status` was unavailable. Reconstructed action context is `repo-local`, workspace `/home/wilcastell/infra/wslaragon`, with no edit-root warning. The supplied runtime token was parent-owned; no local acquire/settle was attempted because the CLI is unavailable.

## Slice 3 completed
- Marked all five Slice 3 implementation rows `[x]` in `tasks.md`, then re-read them to confirm persisted completion.
- Added `src/wslaragon/services/agent_privilege.py` with immutable request/result models and `PrivilegeClient`; it invokes only `sudo -n -- /usr/lib/wslaragon/agent-privilege-helper` using one `communicate()` call, `shell=False`, no helper arguments, no `sudo -v`, no retry, and no prompt path.
- Added `tests/unit/test_agent_privilege.py` covering exact argv and newline framing, scalar registration serialization, valid finite result models, missing executable, denial, nonzero exit, timeout, malformed/multiple/oversize/invalid records, duplicate-safe parsing, and category/length-only stderr logging.
- No export was added because no existing service imports require one. No CLI, MCP, routing, documentation, bootstrap, sudo, or system-policy file was changed; the pre-existing MCP guard diff has the same `39b56c6ba725e022b353a7704a921bb081a75170def919c01aa5519ce483e2e6` SHA-256 before and after Slice 3.

## Verification
- PASS: `PYTEST_ADDOPTS='' pytest -o addopts='' tests/unit/test_agent_privilege.py -v --tb=short` — 5 passed.
- PASS: `python3 -m compileall -q src/wslaragon/services/agent_privilege.py` and `git diff --check`.
- BLOCKED: `pytest tests/unit/test_agent_privilege.py -v --tb=short` and `pytest tests/unit/ -v --tb=short` exit 4 because configured `--cov` arguments are unsupported (`pytest-cov` is unavailable); no configured-suite or coverage claim is made.
- BLOCKED: `python3 -m black --check src/wslaragon/services/agent_privilege.py tests/unit/test_agent_privilege.py` cannot run because Black is not installed. Formatting was kept within the repository's 100-column source limit manually.

### TDD Cycle Evidence
| Task | Test file | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| Slice 3 | `tests/unit/test_agent_privilege.py` | Unit | N/A (new files) | Exact-argv model test failed with missing module | 1 passed after minimal client | Added scalar request, transport, finite-schema, timeout, and redaction cases; initial new cases failed until generalized | Centralized request validation, record parsing, safe-code validation, and bounded category logging; 5 passed |

## Workload / remaining
- PR boundary: feature-branch-chain PR 3 only (`Tracker → PR 1 → PR 2 → 📍 PR 3`), 242 added source-and-test lines, below the 400-line budget. No branch, PR, review, bootstrap, sudo invocation, or system-policy change was made.
- No design deviation. The only verification limitation is unavailable declared test tooling (`pytest-cov` and Black).
- Remaining implementation rows are exactly:
  - [ ] **RED:** Update `tests/unit/test_site_commands.py` to make the default interactive contract explicit (`sudo -v` and `SudoKeepAlive`) and add agent-mode tests proving injected ready client use, safe unavailable/not-ready failure, and no interactive construction or downgrade. <!-- sdd-owner: implementation -->
  - [ ] **GREEN:** Add hidden `--privilege-mode=interactive|agent` to `src/wslaragon/cli/site_commands.py`; preserve the current interactive manager path while agent mode requires a ready test-injectable `PrivilegeClient` before constructing selected managers. <!-- sdd-owner: implementation -->
  - [ ] **TRIANGULATE:** Add or update focused tests in `tests/unit/test_sites.py`, `tests/unit/test_site_creators.py`, `tests/unit/test_nginx.py`, and `tests/unit/test_ssl.py` for scalar descriptor generation, SSL no-host-registration, no direct agent sudo, normal single registration/delayed state commit, and headless backend-first/frontend-second failure with backend-only `remove_registration` and preserved user artifacts. <!-- sdd-owner: implementation -->
  - [ ] **REFACTOR:** Adapt `src/wslaragon/services/sites.py`, `src/wslaragon/services/nginx.py`, and `src/wslaragon/services/ssl.py` so only agent-mode derived hosts/Nginx/access actions use the client; retain unprivileged scaffolding/certificates/database/state ownership and legacy direct managers for interactive commands. <!-- sdd-owner: implementation -->
  - [ ] Run `pytest tests/unit/test_site_commands.py tests/unit/test_sites.py tests/unit/test_site_creators.py tests/unit/test_nginx.py tests/unit/test_ssl.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`; confirm the MCP guard diff is empty. <!-- sdd-owner: implementation -->
  - [ ] **RED:** Replace obsolete creation expectations in `tests/unit/test_mcp_server.py` with denied/not-ready exact JSON and no-execution assertions; add ready normal/headless historical argument permutations plus `--privilege-mode=agent`, safe mappings for denied/missing/malformed/multiple/timeout/operation failures, and unrelated-tool non-expansion coverage. <!-- sdd-owner: implementation -->
  - [ ] **GREEN:** Update `src/wslaragon/mcp/server.py` to inject/use `PrivilegeClient` readiness, map finite safe results to the existing JSON-string contract, and call `_run`—never `_run_interactive`—only for ready normal/headless agent-mode commands. <!-- sdd-owner: implementation -->
  - [ ] **TRIANGULATE:** Add opt-in `tests/integration/test_agent_privilege_native.py`, marked `integration` and `requires_sudo`, using an isolated native-Ubuntu dedicated user/root to prove bootstrap, `sudo -n` readiness, normal creation, forced second-registration rollback, and disable; update `README.md` with invocation, prerequisites, and explicit opt-in safety boundary. <!-- sdd-owner: implementation -->
  - [ ] **REFACTOR:** Provision the declared environment with `-e '.[dev]'` before asserting suite/coverage results, then simplify MCP client injection and test fixtures while preserving stable response shape, stderr redaction, and the atomic activation guard. <!-- sdd-owner: implementation -->
  - [ ] Run `pytest tests/unit/test_mcp_server.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`; after dependency provisioning, run the configured coverage command and the opt-in `requires_sudo` harness only against its dedicated isolated account. <!-- sdd-owner: implementation -->
- Deferred parent lifecycle actions remain byte-preserved in `tasks.md`: tracker/child PR creation, bounded reviews, pre-activation Slice 1–4 confirmation, and final activation review.
- Structured status: authoritative OpenSpec artifact files were consumed; native status and runtime-attempt commands were unavailable (`gentle-ai` not on PATH). Reconstructed `actionContext` is `repo-local`, workspace `/home/wilcastell/infra/wslaragon`, `allowedEditRoots: []`, with warning that native status/attempt authority could not be invoked.

## Slice 4 blocked before RED

### Status consumed
```yaml
schemaName: spec-driven
changeName: agent-privileged-site-creation
artifactStore: openspec
planningHome: {root: /home/wilcastell/infra/wslaragon/openspec, changesDir: /home/wilcastell/infra/wslaragon/openspec/changes}
changeRoot: /home/wilcastell/infra/wslaragon/openspec/changes/agent-privileged-site-creation
artifacts: {proposal: done, specs: done, design: done, tasks: done, applyProgress: partial}
taskProgress: {total: 25, complete: 15, remaining: 10}
applyState: ready
dependencies: {apply: ready, verify: blocked, sync: blocked, archive: blocked}
actionContext: {mode: repo-local, workspaceRoot: /home/wilcastell/infra/wslaragon, allowedEditRoots: [], warnings: ["Native gentle-ai CLI unavailable; status reconstructed from authoritative OpenSpec files."]}
nextRecommended: apply
```

- Delivery path consumed: `auto-chain`, `feature-branch-chain`; assigned boundary is `Tracker → PR 1 → PR 2 → PR 3 → 📍 PR 4`.
- Strict-TDD safety-net command was run before any Slice 4 test or production edit: `PYTEST_ADDOPTS='' pytest -o addopts='' tests/unit/test_site_commands.py tests/unit/test_sites.py tests/unit/test_site_creators.py tests/unit/test_nginx.py tests/unit/test_ssl.py -v --tb=short`.
- BLOCKED: the pre-existing focused suite failed before Slice 4 work (4 failed, 304 passed, 76 errors). `python-dotenv` is unavailable, causing `ModuleNotFoundError: No module named 'dotenv'`; test patch resolution consequently also reports `AttributeError: module 'wslaragon' has no attribute 'cli'`. Per strict TDD, no RED test, production code, task checkbox, MCP change, bootstrap, sudo invocation, or system-policy action was performed.
- Runtime status/acquire could not authenticate the supplied parent token because `gentle-ai` is not installed on PATH. No runtime ledger mutation occurred.

### TDD Cycle Evidence
| Task | Test file | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| Slice 4 | focused CLI/site service files | Unit | BLOCKED: 4 failed, 304 passed, 76 errors from missing `dotenv` before changes | Not started | Not started | Not started | Not started |

## Workload / remaining
- PR boundary remains Slice 4 only; no implementation diff was created, so the 400-line budget remains intact.
- No design deviation; the MCP unconditional fail-closed guard was not edited.
- Remaining Slice 4 implementation rows remain unchecked in `tasks.md`:
  - [ ] **RED:** Update `tests/unit/test_site_commands.py` to make the default interactive contract explicit (`sudo -v` and `SudoKeepAlive`) and add agent-mode tests proving injected ready client use, safe unavailable/not-ready failure, and no interactive construction or downgrade. <!-- sdd-owner: implementation -->
  - [ ] **GREEN:** Add hidden `--privilege-mode=interactive|agent` to `src/wslaragon/cli/site_commands.py`; preserve the current interactive manager path while agent mode requires a ready test-injectable `PrivilegeClient` before constructing selected managers. <!-- sdd-owner: implementation -->
  - [ ] **TRIANGULATE:** Add or update focused tests in `tests/unit/test_sites.py`, `tests/unit/test_site_creators.py`, `tests/unit/test_nginx.py`, and `tests/unit/test_ssl.py` for scalar descriptor generation, SSL no-host-registration, no direct agent sudo, normal single registration/delayed state commit, and headless backend-first/frontend-second failure with backend-only `remove_registration` and preserved user artifacts. <!-- sdd-owner: implementation -->
  - [ ] **REFACTOR:** Adapt `src/wslaragon/services/sites.py`, `src/wslaragon/services/nginx.py`, and `src/wslaragon/services/ssl.py` so only agent-mode derived hosts/Nginx/access actions use the client; retain unprivileged scaffolding/certificates/database/state ownership and legacy direct managers for interactive commands. <!-- sdd-owner: implementation -->
  - [ ] Run `pytest tests/unit/test_site_commands.py tests/unit/test_sites.py tests/unit/test_site_creators.py tests/unit/test_nginx.py tests/unit/test_ssl.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`; confirm the MCP guard diff is empty. <!-- sdd-owner: implementation -->
- Deferred parent lifecycle actions remain byte-preserved and were not edited.

## Slice 4a blocked before RED (rescaled task boundary)

### Status consumed
```yaml
schemaName: spec-driven
changeName: agent-privileged-site-creation
artifactStore: openspec
planningHome: {root: /home/wilcastell/infra/wslaragon/openspec, changesDir: /home/wilcastell/infra/wslaragon/openspec/changes}
changeRoot: /home/wilcastell/infra/wslaragon/openspec/changes/agent-privileged-site-creation
artifacts: {proposal: done, specs: done, design: done, tasks: done, applyProgress: partial}
taskProgress: {total: 25, complete: 15, remaining: 10}
deferredParentActions: {total: 5, complete: 0, remaining: 5}
applyState: ready
dependencies: {apply: ready, verify: blocked, sync: blocked, archive: blocked}
actionContext: {mode: repo-local, workspaceRoot: /home/wilcastell/infra/wslaragon, allowedEditRoots: [], warnings: ["Native gentle-ai CLI unavailable; status reconstructed from authoritative OpenSpec files."]}
nextRecommended: apply
```

- Delivery path consumed: `auto-chain`, `feature-branch-chain`; assigned boundary is `Tracker → PR 1 → PR 2 → PR 3 → 📍 PR 4a`, limited to hidden CLI mode selection and its focused tests.
- Strict-TDD safety net was attempted before any source or test edit: `pytest tests/unit/test_site_commands.py -v --tb=short` exits 4 because configured `--cov` options require unavailable `pytest-cov`; a no-addopts focused retry exits 1 with 4 failures and 76 errors before Slice 4a work because `python-dotenv` is unavailable, which prevents `wslaragon.cli` import and mock patch resolution.
- Per strict TDD, no RED test, production code, task checkbox, MCP change, manager/registration routing, bootstrap, sudo invocation, system-policy action, documentation, branch, or commit was performed.
- Native runtime status/acquire could not authenticate the supplied parent token because `gentle-ai` is unavailable on PATH; no runtime ledger mutation occurred.

### TDD Cycle Evidence
| Task | Test file | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| Slice 4a | `tests/unit/test_site_commands.py` | Unit | BLOCKED: configured runner exit 4 (`pytest-cov` absent); no-addopts baseline 4 failed, 76 errors (`python-dotenv` absent) | Not started | Not started | Not started | Not started |

## Workload / remaining
- PR boundary remains Slice 4a only; no implementation diff was created, so the 400-line budget remains intact.
- No design deviation and the MCP unconditional fail-closed guard was not edited.
- Remaining Slice 4a implementation rows remain unchecked in `tasks.md`:
  - [ ] **RED:** Update `tests/unit/test_site_commands.py` to make the default interactive contract explicit (`sudo -v` and `SudoKeepAlive`) and add agent-mode tests proving ready-client validation, safe unavailable/not-ready failure, and no interactive construction or downgrade. <!-- sdd-owner: implementation -->
  - [ ] **GREEN:** Add hidden `--privilege-mode=interactive|agent` to `src/wslaragon/cli/site_commands.py`; preserve the current interactive manager path while agent mode requires a ready test-injectable `PrivilegeClient` before command dispatch, without passing it to site, Nginx, SSL, or registration managers. <!-- sdd-owner: implementation -->
  - [ ] **TRIANGULATE:** Extend `tests/unit/test_site_commands.py` for invalid/missing mode handling, normal and headless argument permutations, and assertions that agent-mode selection performs no registration, direct agent sudo, or manager construction beyond current command parsing. <!-- sdd-owner: implementation -->
  - [ ] **REFACTOR:** Centralize privilege-mode parsing and readiness failure mapping in `src/wslaragon/cli/site_commands.py` while retaining legacy interactive command construction and leaving `src/wslaragon/mcp/server.py` unchanged. <!-- sdd-owner: implementation -->
  - [ ] Run `pytest tests/unit/test_site_commands.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`; confirm the MCP guard diff is empty and no registration-routing files change. <!-- sdd-owner: implementation -->
- Deferred lifecycle actions remain byte-preserved and parent-owned: tracker/child PR creation, bounded reviews, Slice 4b prerequisite confirmation, Slice 5 activation prerequisite confirmation, and activation review.

## Slice 4a completed — explicit CLI agent-mode selection

### Status consumed
```yaml
schemaName: spec-driven
changeName: agent-privileged-site-creation
artifactStore: openspec
planningHome: {root: /home/wilcastell/infra/wslaragon/openspec, changesDir: /home/wilcastell/infra/wslaragon/openspec/changes}
changeRoot: /home/wilcastell/infra/wslaragon/openspec/changes/agent-privileged-site-creation
artifacts: {proposal: done, specs: done, design: done, tasks: done, applyProgress: partial}
taskProgress: {total: 30, complete: 20, remaining: 10}
deferredParentActions: {total: 5, complete: 0, remaining: 5}
applyState: ready
dependencies: {apply: ready, verify: blocked, sync: blocked, archive: blocked}
actionContext: {mode: repo-local, workspaceRoot: /home/wilcastell/infra/wslaragon, allowedEditRoots: [], warnings: ["Native gentle-ai CLI unavailable; status reconstructed from authoritative OpenSpec files."]}
nextRecommended: parent-lifecycle
```

- Delivery path consumed: `auto-chain`, `feature-branch-chain`; completed boundary is `Tracker → PR 1 → PR 2 → PR 3 → 📍 PR 4a`, with 100 production-and-test additions/deletions (under 400).
- Added a hidden `--privilege-mode=interactive|agent` selector to `site create`, defaulting to the legacy interactive path.
- The interactive path still performs `sudo -v` and uses `SudoKeepAlive` unchanged.
- Agent mode constructs a test-injectable `PrivilegeClient` and checks `ready()` before any manager construction; unavailable, not-ready, and construction-exception outcomes print a safe failure and return without interactive fallback.
- A ready agent mode deliberately reports that registration is unavailable and returns before any site, Nginx, SSL, or registration manager is constructed. This is the required Slice 4a fail-closed boundary, not activation or routing.
- Marked all five Slice 4a implementation rows `[x]` in `tasks.md`, then re-read the persisted rows to confirm completion.

### Files changed

- `src/wslaragon/cli/site_commands.py`
- `tests/unit/test_site_commands.py`
- `openspec/changes/agent-privileged-site-creation/tasks.md`
- `openspec/changes/agent-privileged-site-creation/apply-progress.md`

### Verification

- PASS: `/home/wilcastell/infra/wslaragon/venv/bin/pytest -o addopts='' tests/unit/test_site_commands.py::TestSiteCreateCommand -q --tb=short` — 32 passed (GREEN, TRIANGULATE, and REFACTOR confirmation).
- PARTIAL: `/home/wilcastell/infra/wslaragon/venv/bin/pytest tests/unit/test_site_commands.py -v --tb=short` — all 84 tests passed, but pytest exited 1 solely because the focused invocation cannot meet repository-wide `--cov-fail-under=90` (23.72% total coverage).
- BLOCKED (pre-existing MCP expectation mismatch): `/home/wilcastell/infra/wslaragon/venv/bin/pytest tests/unit/ -v --tb=short` — 1,381 passed, 1 skipped, 24 failed; every failure is a legacy `test_mcp_server.py` creation expectation that conflicts with the pre-existing unconditional fail-closed MCP guard. Slice 5 owns its reconciliation; MCP was not edited.
- PASS: `git diff --check`.
- PASS: the pre-existing MCP guard diff remains `39b56c6ba725e022b353a7704a921bb081a75170def919c01aa5519ce483e2e6`; no MCP or registration-routing file was edited by Slice 4a.

### TDD Cycle Evidence

| Task | Test file | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| Slice 4a | `tests/unit/test_site_commands.py` | Unit | 28 passed with `-o addopts=''` before edits | Two new agent-mode tests failed because `PrivilegeClient` was absent from the CLI module | 30 passed after hidden mode and fail-closed readiness handling | Added unavailable-client, hidden-option/invalid-value, and normal/headless cases; 32 passed | Extracted mode constant and safe readiness helper; 32 passed |

### Deviations and risks

- No design deviation: this slice intentionally stops ready agent requests before manager construction because registration routing belongs only to Slice 4b.
- No MCP, bootstrap, system-policy, documentation, branch, commit, or PR action was performed.
- The full unit suite remains blocked by legacy MCP tests that are explicitly deferred to Slice 5; this is not caused by the CLI-only Slice 4a diff.

### Remaining implementation tasks

- [ ] **RED:** Add or update focused tests in `tests/unit/test_sites.py`, `tests/unit/test_site_creators.py`, `tests/unit/test_nginx.py`, and `tests/unit/test_ssl.py` for scalar descriptor generation, SSL no-host-registration, no direct agent sudo, normal single registration/delayed state commit, and headless backend-first/frontend-second failure with backend-only `remove_registration` and preserved user artifacts. <!-- sdd-owner: implementation -->
- [ ] **GREEN:** Adapt `src/wslaragon/services/sites.py`, `src/wslaragon/services/nginx.py`, and `src/wslaragon/services/ssl.py` so only agent-mode derived hosts/Nginx/access actions use the client; retain unprivileged scaffolding/certificates/database/state ownership and legacy direct managers for interactive commands. <!-- sdd-owner: implementation -->
- [ ] **TRIANGULATE:** Extend those focused tests for unavailable/denied/malformed client results, repeated registrations, partial cleanup failures, no state commit before all selected registrations succeed, and no routing when interactive mode is selected. <!-- sdd-owner: implementation -->
- [ ] **REFACTOR:** Centralize bounded registration descriptors and compensating `remove_registration` handling in the concrete discovery targets `src/wslaragon/services/sites.py`, `src/wslaragon/services/nginx.py`, and `src/wslaragon/services/ssl.py`; retain the Slice 4a CLI selection boundary and leave `src/wslaragon/mcp/server.py` unchanged. <!-- sdd-owner: implementation -->
- [ ] Run `pytest tests/unit/test_sites.py tests/unit/test_site_creators.py tests/unit/test_nginx.py tests/unit/test_ssl.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`; confirm the MCP guard diff is empty. <!-- sdd-owner: implementation -->
- [ ] **RED:** Replace obsolete creation expectations in `tests/unit/test_mcp_server.py` with denied/not-ready exact JSON and no-execution assertions; add ready normal/headless historical argument permutations plus `--privilege-mode=agent`, safe mappings for denied/missing/malformed/multiple/timeout/operation failures, and unrelated-tool non-expansion coverage. <!-- sdd-owner: implementation -->
- [ ] **GREEN:** Update `src/wslaragon/mcp/server.py` to inject/use `PrivilegeClient` readiness, map finite safe results to the existing JSON-string contract, and call `_run`—never `_run_interactive`—only for ready normal/headless agent-mode commands. <!-- sdd-owner: implementation -->
- [ ] **TRIANGULATE:** Add opt-in `tests/integration/test_agent_privilege_native.py`, marked `integration` and `requires_sudo`, using an isolated native-Ubuntu dedicated user/root to prove bootstrap, `sudo -n` readiness, normal creation, forced second-registration rollback, and disable; update `README.md` with invocation, prerequisites, and explicit opt-in safety boundary. <!-- sdd-owner: implementation -->
- [ ] **REFACTOR:** Provision the declared environment with `-e '.[dev]'` before asserting suite/coverage results, then simplify MCP client injection and test fixtures while preserving stable response shape, stderr redaction, and the atomic activation guard. <!-- sdd-owner: implementation -->
- [ ] Run `pytest tests/unit/test_mcp_server.py -v --tb=short` and `pytest tests/unit/ -v --tb=short`; after dependency provisioning, run the configured coverage command and the opt-in `requires_sudo` harness only against its dedicated isolated account. <!-- sdd-owner: implementation -->

### Deferred lifecycle actions

The five parent-owned rows for chain PR creation, bounded review, Slice 4b prerequisite confirmation, Slice 5 prerequisite confirmation, and activation review remain byte-for-byte unchanged.
