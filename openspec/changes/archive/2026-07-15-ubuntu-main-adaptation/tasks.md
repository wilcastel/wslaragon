# Tasks: Ubuntu Native Support for origin/main

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1,500 |
| 800-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 → PR 5 → PR 6 |
| Delivery strategy | force-chained |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High
800-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Platform detection & config defaults | PR 1 | `pytest tests/unit/test_config.py tests/unit/test_platform.py -v` | `python -c "from wslaragon.core.platform import Platform; print(Platform.hosts_file(cfg))"` | Revert `src/wslaragon/core/platform.py`, `config.py`, `services.py` |
| 2 | PHP-FPM/Nginx wiring & safer switch | PR 2 | `pytest tests/unit/test_php.py tests/unit/test_nginx.py -v` | `wslaragon php switch 8.5` on Ubuntu VM | Revert `src/wslaragon/services/php.py`, `nginx.py`, `core/services.py` |
| 3 | Hosts, sudo keep-alive & site permissions | PR 3 | `pytest tests/unit/test_ssl.py tests/unit/test_sites.py tests/unit/test_site_commands.py -v` | `wslaragon site create ubu1 --html` with sudo timeout | Revert `ssl.py`, `sites.py`, `cli/site_commands.py` |
| 4 | Configurable DB user & site creators | PR 4 | `pytest tests/unit/test_mysql.py tests/unit/test_site_creators.py -v` | `wslaragon site create wp1 --wordpress --mysql` | Revert `mysql.py`, `site_creators.py` |
| 5 | Installer scripts & Ubuntu docs | PR 5 | `pytest tests/unit/test_main_cli.py -v && shellcheck scripts/*.sh` | `scripts/install.sh` on fresh Ubuntu VM | Revert `scripts/*`, `docs/UBUNTU.md`, `pyproject.toml`, `main.py` |
| 6 | MCP runtime alignment | PR 6 | `pytest tests/unit/test_mcp_server.py -v` | `wslaragon-mcp` status resource | Revert `src/wslaragon/mcp/server.py` |

## Phase 1: Foundation

- [x] 1.1 Create `src/wslaragon/core/platform.py` with `is_wsl()`, `is_native_ubuntu()`, `hosts_file()` (~40 lines).
- [x] 1.2 Modify `src/wslaragon/core/config.py` for platform-aware defaults and `hosts.hosts_file` (~30 lines).
- [x] 1.3 Modify `src/wslaragon/core/services.py` to derive `php-fpm` service name from config version (~15 lines).
- [x] 1.4 RED: add failing tests `test_hosts_file_native_ubuntu`, `test_hosts_file_wsl2`, `test_service_manager_uses_configured_php_version` (~60 lines).
- [x] 1.5 GREEN: update `tests/unit/test_config.py` and `tests/unit/test_services.py` with Ubuntu fixtures (~50 lines).

## Phase 2: PHP-FPM & Nginx Wiring

- [x] 2.1 RED: add failing `test_switch_version_aborts_when_fpm_missing` (~30 lines).
- [x] 2.2 Modify `src/wslaragon/services/php.py` to pre-check target FPM package before stopping current FPM (~40 lines).
- [x] 2.3 RED: add failing socket discovery tests for versioned + generic paths (~40 lines).
- [x] 2.4 Modify `src/wslaragon/services/nginx.py` to add `_get_php_fpm_socket()` with `/run/php/php{version}-fpm.sock` fallback to `php-fpm.sock` (~30 lines).
- [x] 2.5 Update `tests/unit/test_php.py` and `tests/unit/test_nginx.py` (~80 lines).

## Phase 3: Hosts, Sudo Keep-Alive & Permissions

- [x] 3.1 RED: add failing `test_sudo_keep_alive_emits_refresh` and `test_apply_permissions_chmod_fallback` (~50 lines).
- [x] 3.2 Create `SudoKeepAlive` context manager in `src/wslaragon/services/sites.py` (daemon thread `sudo -n -v` every 15s) (~35 lines).
- [x] 3.3 Modify `src/wslaragon/services/ssl.py` `add_to_hosts`/`remove_from_hosts` to use `sudo tee` on `/etc/hosts` for native Ubuntu (~80 lines).
- [x] 3.4 Modify `src/wslaragon/services/sites.py` `fix_permissions()` to try `setfacl -R -m u:www-data:rx` and fall back to `chmod` (~40 lines).
- [x] 3.5 Modify `src/wslaragon/cli/site_commands.py` to wrap `create_site`/`create_headless_site` with `SudoKeepAlive` (~20 lines).
- [x] 3.6 Update `tests/unit/test_ssl.py`, `tests/unit/test_sites.py`, `tests/unit/test_site_commands.py` (~100 lines).

## Phase 4: MySQL User & Site Creators

- [x] 4.1 RED: add failing `test_site_creator_uses_configured_db_user` (~30 lines).
- [x] 4.2 Modify `src/wslaragon/services/mysql.py` to use `config.get('mysql.user')` as default user (~10 lines).
- [x] 4.3 Modify `src/wslaragon/services/site_creators.py` `WordPressSiteCreator` and `LaravelSiteCreator` to use configured `DB_USER`/`DB_PASSWORD` (~30 lines).
- [x] 4.4 Update `tests/unit/test_mysql.py`, `tests/unit/test_site_creators.py`, and `tests/conftest.py` fixtures (~80 lines).

## Phase 5: Installer Scripts & Docs

- [x] 5.1 Modify `scripts/vars.sh`: set `HOSTS_FILE=/etc/hosts`, `PHP_VERSION=8.5` (~10 lines).
- [x] 5.2 Modify `scripts/setup-env.sh`: remove WSL-only warning, add platform check (~20 lines).
- [x] 5.3 Modify `scripts/install.sh`: Ubuntu stack, PHP 8.5 PPA fallback, create `wslaragon` MariaDB user/grants (~120 lines).
- [x] 5.4 Create `scripts/uninstall.sh`: default preserves data, `--purge` requires confirmation (~100 lines).
- [x] 5.5 Update `pyproject.toml` description and `src/wslaragon/cli/main.py` docstring to drop WSL2-only wording (~10 lines).
- [x] 5.6 Create `docs/UBUNTU.md` with install, site creation, SSL, and uninstall steps (~150 lines).
- [x] 5.7 Add shell script linting and installer unit assertions (~30 lines).

## Phase 6: MCP Runtime Alignment

- [x] 6.1 RED: add failing `test_mcp_uses_ubuntu_service_names` (~30 lines).
- [x] 6.2 Modify `src/wslaragon/mcp/server.py` to resolve service names from config and update `agent_init` runtime context signature (~50 lines).
- [x] 6.3 Update `tests/unit/test_mcp_server.py` (~40 lines).

## Phase 7: Integration & Verification

- [x] 7.1 Run unit suite with coverage: `pytest tests/unit/ -q --tb=short` and integration suite with `--no-cov`: `pytest tests/integration/ -v --run-slow --tb=short --no-cov`.
- [ ] 7.2 Integration on Ubuntu VM: `wslaragon site create` for WordPress, Laravel, and headless (marked `requires_sudo`).
- [ ] 7.3 Verify SSL/hosts via `/etc/hosts`, PHP-FPM socket detection, `php upload-limit`, and `scripts/install.sh` end-to-end.

## Remediation (post-verify findings)

- [x] R1 Fix `scripts/setup-env.sh` line 75 so `php.version` and `php.ini_file` are emitted as separate YAML keys.
- [x] R2 Cover the YAML fix in `tests/unit/test_installer.py` (parse the generated heredoc with `yaml.safe_load` for default and alternate PHP versions).
- [x] R3 Document the `--no-cov` integration-test workflow in `docs/UBUNTU.md` and `tests/integration/test_integration.py` without removing the unit-test `--cov-fail-under=90` gate.
- [x] R4 Run unit suite: `pytest tests/unit/ -q --tb=short` → 1369 passed, 99.67% coverage.
- [x] R5 Run integration suite: `pytest tests/integration/ -v --run-slow --tb=short --no-cov` → 32 passed, 1 skipped.
- [x] R6 Run shell lint: `shellcheck -x --severity=warning scripts/*.sh` → clean.
