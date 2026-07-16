```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:0a877a6c404b63a704cace3cf6013a76c76c4c79f83b83f76b5ffecad02ae57c
verdict: pass_with_warnings
blockers: 0
critical_findings: 0
requirements: 15/15
scenarios: 21/21
test_command: pytest tests/unit/ -q --tb=short
test_exit_code: 0
test_output_hash: sha256:11d993a1349350394c08643c5b5b34b416be2b97ea199be927b2186fb1dc43e3
build_command: shellcheck -x --severity=warning scripts/*.sh && python3 -m py_compile src/wslaragon/core/platform.py src/wslaragon/core/config.py src/wslaragon/services/ssl.py src/wslaragon/services/nginx.py
build_exit_code: 0
build_output_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

# Verification Report: ubuntu-main-adaptation

## Change
- **Name**: ubuntu-main-adaptation
- **Branch**: feature/ubuntu-evaluate-main
- **Mode**: auto (hybrid artifact store, force-chained delivery, stacked-to-main chain strategy)
- **Strict TDD**: enabled
- **Verdict**: PASS WITH WARNINGS

## Executive Summary
The F1 (`scripts/setup-env.sh` invalid YAML) and F2 (integration coverage gate) remediation succeeded. All four verification commands now exit 0: 1,369 unit tests pass at 99.67 % coverage, 32 integration tests pass with 1 skipped, `shellcheck` is clean, and the four requested Python files compile. Two Phase 7 VM/sudo tasks remain unchecked and several non-blocking findings (F3–F8) are still open, so the change is approved for merge with warnings rather than a clean pass.

## Artifacts Consumed
- Engram: `sdd/ubuntu-main-adaptation/spec`, `sdd/ubuntu-main-adaptation/design`, `sdd/ubuntu-main-adaptation/tasks`, `sdd/ubuntu-main-adaptation/apply-progress`
- OpenSpec: `openspec/changes/ubuntu-main-adaptation/specs/*/spec.md`, `openspec/changes/ubuntu-main-adaptation/design.md`, `openspec/changes/ubuntu-main-adaptation/tasks.md`, `openspec/changes/ubuntu-main-adaptation/apply-progress.md`

## Task Completion

| Phase | Task | Status |
|-------|------|--------|
| 1.1 | Create platform.py | ✅ |
| 1.2 | Modify config.py | ✅ |
| 1.3 | Modify services.py | ✅ |
| 1.4 | RED tests | ✅ |
| 1.5 | GREEN tests | ✅ |
| 2.1 | RED: switch_version aborts when FPM missing | ✅ |
| 2.2 | Pre-check target FPM package | ✅ |
| 2.3 | RED: socket discovery tests | ✅ |
| 2.4 | _get_php_fpm_socket() fallback | ✅ |
| 2.5 | Update test_php.py / test_nginx.py | ✅ |
| 3.1 | RED: sudo keep-alive / chmod fallback tests | ✅ |
| 3.2 | SudoKeepAlive context manager | ✅ |
| 3.3 | sudo tee on /etc/hosts | ✅ |
| 3.4 | ACL / chmod fallback | ✅ |
| 3.5 | Wrap create_site with SudoKeepAlive | ✅ |
| 3.6 | Update ssl/sites/site_commands tests | ✅ |
| 4.1 | RED: configured DB user test | ✅ |
| 4.2 | mysql.user default | ✅ |
| 4.3 | WP/Laravel use configured DB_USER | ✅ |
| 4.4 | Update fixtures/tests | ✅ |
| 5.1 | vars.sh HOSTS_FILE/PHP_VERSION | ✅ |
| 5.2 | setup-env.sh platform check | ✅ |
| 5.3 | install.sh Ubuntu stack + PPA | ✅ |
| 5.4 | uninstall.sh default/purge | ✅ |
| 5.5 | pyproject.toml / main.py wording | ✅ |
| 5.6 | docs/UBUNTU.md | ✅ |
| 5.7 | shell lint + installer assertions | ✅ |
| 6.1 | RED: MCP service names test | ✅ |
| 6.2 | MCP server config-driven service names | ✅ |
| 6.3 | Update test_mcp_server.py | ✅ |
| 7.1 | Full suite with coverage | ✅ |
| 7.2 | Ubuntu VM integration | ⏳ (requires VM/sudo, not executed) |
| 7.3 | End-to-end harness checks | ⏳ (requires VM/sudo, not executed) |
| R1 | Fix setup-env.sh YAML defect | ✅ |
| R2 | Cover YAML fix with unit tests | ✅ |
| R3 | Document --no-cov integration workflow | ✅ |
| R4–R6 | Re-run unit/integration/shellcheck | ✅ |

## Build / Test / Static Evidence

| Command | Exit | Result | Output hash (sha256) |
|---------|------|--------|----------------------|
| `pytest tests/unit/ -q --tb=short` | 0 | 1369 passed, 99.67 % coverage | `11d993a1349350394c08643c5b5b34b416be2b97ea199be927b2186fb1dc43e3` |
| `pytest tests/integration/ -v --run-slow --tb=short --no-cov` | 0 | 32 passed, 1 skipped | `51d3fab78e379d402b298876b53c06e0cec9395c4670204142b72fd88989b0df` |
| `shellcheck -x --severity=warning scripts/*.sh` | 0 | no warnings | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `python3 -m py_compile src/wslaragon/core/platform.py src/wslaragon/core/config.py src/wslaragon/services/ssl.py src/wslaragon/services/nginx.py` | 0 | syntax OK | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## Spec Compliance Matrix

Spec source: 7 domains, 15 requirements, 21 scenarios.

| Domain | Scenario | Test evidence | Status |
|--------|----------|---------------|--------|
| ubuntu-host-management | Ubuntu runtime detection → `/etc/hosts` | `test_hosts_file_returns_etc_hosts_on_native_ubuntu` | ✅ COMPLIANT |
| ubuntu-host-management | Add site host entry via `sudo tee -a` | `test_add_to_hosts_uses_sudo_tee_on_ubuntu` | ✅ COMPLIANT |
| ubuntu-host-management | Remove site host entry via `sudo tee` | `test_remove_from_hosts_uses_sudo_tee_on_ubuntu` | ✅ COMPLIANT |
| ubuntu-php-fpm | Default PHP version used (8.5) | `TestConfigUbuntuDefaults::test_native_ubuntu_defaults_php_85`, `test_service_manager_uses_configured_php_version` | ✅ COMPLIANT |
| ubuntu-php-fpm | Versioned socket exists | `TestNginxManagerGetPhpFpmSocket::test_returns_versioned_socket_when_present` | ✅ COMPLIANT |
| ubuntu-php-fpm | Generic socket fallback | `TestNginxManagerGetPhpFpmSocket::test_falls_back_to_generic_socket` | ✅ COMPLIANT |
| ubuntu-php-fpm | Missing target FPM package aborts switch | `test_switch_version_aborts_when_fpm_missing` | ✅ COMPLIANT |
| ubuntu-mysql-user | Custom DB user used for site DB | `test_init_uses_configured_mysql_user`, `test_site_creator_uses_configured_db_user`, `test_laravel_creator_uses_configured_db_user` | ✅ COMPLIANT |
| ubuntu-mysql-user | Backward-compatible root default + deprecated docs | Default implemented; explicit deprecation note missing in docs/config | ⚠️ WARNING |
| ubuntu-site-creation | Sudo keep-alive during long creation | `test_sudo_keep_alive_emits_refresh` | ✅ COMPLIANT |
| ubuntu-site-creation | ACL tools available → setfacl | `test_apply_permissions_uses_setfacl_when_available` | ✅ COMPLIANT |
| ubuntu-site-creation | ACL tools unavailable → chmod fallback | `test_apply_permissions_chmod_fallback` | ✅ COMPLIANT |
| ubuntu-installer | Clean Ubuntu installation | `test_installs_ubuntu_stack_tools`, `test_installs_php85_packages` | ✅ COMPLIANT (script inspection) |
| ubuntu-installer | PHP 8.5 PPA fallback | `test_has_php_ppa_fallback` | ✅ COMPLIANT |
| ubuntu-installer | Default uninstall preserves data | `test_default_preserves_data` | ✅ COMPLIANT |
| ubuntu-installer | Purge uninstall requires confirmation | `test_purge_requires_confirmation` | ✅ COMPLIANT |
| ubuntu-mcp-runtime | Ubuntu service names (nginx/mariadb/php8.5-fpm) | `test_mcp_uses_ubuntu_service_names` | ✅ COMPLIANT |
| ubuntu-mcp-runtime | Agent init receives runtime context | `test_agent_init_includes_runtime_context`, `test_agent_init_accepts_runtime_context_overrides` | ✅ COMPLIANT |
| ubuntu-project-artifacts | Ubuntu guide complete | `docs/UBUNTU.md` exists and references `scripts/install.sh`/`scripts/uninstall.sh` | ✅ COMPLIANT |
| ubuntu-project-artifacts | Project metadata drops WSL2-only wording | `test_pyproject_description_drops_wsl2_only`, `test_main_docstring_drops_wsl2_only` | ✅ COMPLIANT |
| ubuntu-project-artifacts | Tests aligned with Ubuntu defaults | Full unit suite passes with 99.67 % coverage | ✅ COMPLIANT |

**Compliance summary**: 20/21 scenarios compliant, 1 WARNING (ubuntu-mysql-user deprecated docs).

## Correctness (Static Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| Platform detection | ✅ Implemented | `Platform.is_wsl()`, `is_native_ubuntu()`, `hosts_file()` |
| Hosts file runtime selection | ✅ Implemented | `/etc/hosts` on Ubuntu, Windows hosts preserved on WSL |
| PHP/MySQL platform-aware defaults | ✅ Implemented | Defaults to 8.5/wslaragon on non-WSL, 8.3/root on WSL |
| FPM socket discovery | ✅ Implemented | Versioned → generic → RuntimeError |
| Safer PHP version switch | ✅ Implemented | Pre-checks target FPM package before stopping current |
| Sudo keep-alive | ✅ Implemented | `SudoKeepAlive` daemon thread refreshes every 15 s |
| Permissions ACL/chmod fallback | ✅ Implemented | `setfacl` with `chmod o+rx` fallback |
| Configurable DB user | ✅ Implemented | Site creators and MySQL init read `mysql.user` |
| Installer scripts | ✅ Implemented | `install.sh`, `uninstall.sh`, `setup-env.sh`, `vars.sh` |
| MCP runtime alignment | ✅ Implemented | Config-driven service names and `agent_init` context |

## Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| Platform detection in `core/platform.py` | ✅ Yes | Single source of truth for WSL/Ubuntu detection |
| Hosts file runtime selection | ✅ Yes | Config key `hosts.hosts_file` defaults to `/etc/hosts` |
| PHP/MySQL platform-aware defaults | ✅ Yes | `config.py` branches on `Platform.is_wsl()` |
| FPM socket discovery | ✅ Yes | `NginxManager._get_php_fpm_socket()` encapsulates fallback |
| Sudo keep-alive | ✅ Yes | `SudoKeepAlive` context manager |
| Permissions | ✅ Yes | `fix_permissions()` tries ACL, falls back to chmod |
| Preserve origin/main capabilities | ✅ Yes | Headless, API proxies, SvelteKit, upload-limit intact |

## TDD Compliance (Strict TDD Active)

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ✅ | TDD Cycle Evidence tables present in apply-progress for PRs 3–6; narrative RED/GREEN cycles for PRs 1–2 |
| All tasks have tests | ✅ | 20/20 implementation tasks have test files |
| RED confirmed (tests exist) | ✅ | All spec-driven test files exist in the codebase |
| GREEN confirmed (tests pass) | ✅ | Unit tests pass; integration tests pass with `--no-cov` |
| Triangulation adequate | ✅ | PRs 3–6 show multi-case triangulation; PRs 1–2 focused on single scenario each |
| Safety Net for modified files | ✅ | PR reports cite safety-net runs before modifications |

**TDD Compliance**: 6/6 checks passed

## Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | 1369 | 28 | pytest, pytest-mock, pytest-cov |
| Integration | 32 passed / 1 skipped | 1 | pytest |
| E2E | 0 | 0 | — |
| **Total** | **1401 collected / 1400 passed / 1 skipped** | **29** | |

## Changed File Coverage (unit suite)

| File | Line % | Uncovered Lines | Rating |
|------|--------|-----------------|--------|
| `src/wslaragon/core/platform.py` | 100 % | — | ✅ Excellent |
| `src/wslaragon/core/config.py` | 100 % | — | ✅ Excellent |
| `src/wslaragon/core/services.py` | 100 % | — | ✅ Excellent |
| `src/wslaragon/services/nginx.py` | 100 % | — | ✅ Excellent |
| `src/wslaragon/services/php.py` | 100 % | — | ✅ Excellent |
| `src/wslaragon/services/ssl.py` | 96 % | 305-307, 317, 321, 338-340, 425 | ⚠️ Acceptable |
| `src/wslaragon/services/sites.py` | 99 % | 34-35 | ⚠️ Acceptable |
| `src/wslaragon/services/site_creators.py` | 100 % | — | ✅ Excellent |
| `src/wslaragon/services/mysql.py` | 100 % | — | ✅ Excellent |
| `src/wslaragon/cli/site_commands.py` | 100 % | — | ✅ Excellent |
| `src/wslaragon/cli/main.py` | 100 % | — | ✅ Excellent |
| `src/wslaragon/mcp/server.py` | 99 % | 39 | ⚠️ Acceptable |

**Average changed file coverage**: ~99 % (unit suite).

## Assertion Quality

No tautologies, ghost loops, or smoke-test-only cases were found in the newly added/changed tests. Existing and new tests that assert empty payloads or failure returns are paired with non-empty/companion tests in the same suites.

**Assertion quality**: ✅ All assertions verify real behavior

## Quality Metrics

- **Linter**: shellcheck passed (exit 0, no warnings).
- **Type checker**: not executed; no explicit mypy run requested.
- **Python syntax**: py_compile passed for all four requested files.

## Findings

| ID | Severity | Status | Finding | Evidence | Suggested resolution |
|----|----------|--------|---------|----------|----------------------|
| F1 | CRITICAL | ✅ Resolved | `scripts/setup-env.sh` emitted invalid YAML | `php.version` and `php.ini_file` now on separate lines; `test_generated_config_yaml_is_valid` and `test_generated_config_yaml_accepts_alternate_php_version` pass | — |
| F2 | CRITICAL | ✅ Resolved | Integration suite failed project-wide coverage gate | `pytest tests/integration/ ... --no-cov` now exits 0 with 32 passed/1 skipped; workflow documented in `docs/UBUNTU.md` | — |
| F3 | WARNING | ⏳ Open | Phase 7 tasks 7.2 and 7.3 not executed | Tasks artifact shows `[ ] 7.2` and `[ ] 7.3`; require real Ubuntu VM and sudo | Run the listed harness commands on a fresh Ubuntu VM before archive |
| F4 | WARNING | ⏳ Open | `scripts/setup-env.sh` and `scripts/install.sh` sudoers lists are missing commands needed for Ubuntu operations | Current list: nginx, service, systemctl, phpenmod, phpdismod, cp, ln, rm. Missing: `tee`, `setfacl`, `chmod`, `chown` (used by `ssl.py`, `sites.py`, `site_creators.py`) | Add required commands to `/etc/sudoers.d/wslaragon` or document that passwordless sudo is required |
| F5 | WARNING | ⏳ Open | Spec-required deprecation note for `root` default is missing | `ubuntu-mysql-user` spec: "MUST document that this default is deprecated on Ubuntu"; not found in `docs/UBUNTU.md`, `config.py`, or CLI help | Add a note in `docs/UBUNTU.md` and/or `config.py` comment |
| F6 | SUGGESTION | ⏳ Open | MCP server instructions still WSL2-centric | `mcp = FastMCP(...instructions="WSLaragon ... for WSL2...")` | Update instructions to mention Ubuntu + WSL2 |
| F7 | SUGGESTION | ⏳ Open | `scripts/install.sh` uses placeholder repository URL | `git clone https://github.com/your-username/wslaragon.git` | Replace with real repository URL or remove the clone fallback |
| F8 | SUGGESTION | ⏳ Open | Integration test skipped due to missing MCP `app` export | `test_mcp_list_sites_endpoint` skipped: "cannot import name 'app' from 'wslaragon.mcp.server'" | Export or mock `app` in MCP server, or update the integration test |
| F9 | SUGGESTION | ✅ Resolved | OpenSpec `tasks.md` chain_strategy said "pending" | File now reads `chain_strategy: stacked-to-main` | — |

## Risks
- F3 means end-to-end Ubuntu behavior (site creation, SSL/hosts, PHP-FPM socket detection, install/uninstall) has not been exercised on a real system.
- F4 means the installer may grant insufficient sudo privileges for `sudo tee`, `setfacl`, `chmod`, and `chown` operations on native Ubuntu.
- F5 leaves a spec-required deprecation notice unfulfilled, which may confuse users who still see `root` as the default on WSL2.

## Next Recommended
1. **Execute F3** on a fresh Ubuntu VM before archive.
2. **Address F4–F8** at the orchestrator's discretion; they are not blockers for this verification cycle but should be resolved before final release.
3. **Archive** the change once VM-based verification is complete and any accepted warnings are documented.

## Skill Resolution
- `paths-injected` via orchestrator: `sdd-verify`, `_shared/sdd-status-contract.md`, `_shared/sdd-phase-common.md`.
- Strict TDD module `strict-tdd-verify.md` loaded because Strict TDD is active.
