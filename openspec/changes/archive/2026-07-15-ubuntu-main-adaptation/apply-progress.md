# Apply Progress: Ubuntu Native Support for origin/main

## PR 1: Foundation / Platform Detection (completed)

**What**: Implemented PR 1 (Phase 1: Foundation / platform detection) for ubuntu-main-adaptation on branch feature/ubuntu-evaluate-main.

**Why**: Establish runtime platform detection and Ubuntu-native config defaults while preserving WSL2 behavior, as the first slice of the chained stacked-to-main delivery.

**Where**:
- Created `src/wslaragon/core/platform.py`
- Modified `src/wslaragon/core/config.py`
- Modified `src/wslaragon/core/services.py`
- Created `tests/unit/test_platform.py`
- Modified `tests/unit/test_config.py`
- Modified `tests/unit/test_config_comprehensive.py`
- Modified `tests/unit/test_services.py`

**Learned**:
- Strict TDD mode active; all Phase 1 tasks followed RED → GREEN → TRIANGULATE → REFACTOR cycles.
- Full unit suite passes: `pytest tests/unit/ -v --tb=short` → 1327 passed, 100% coverage.
- Existing comprehensive config tests assume WSL2 defaults; added module-level `mock_wsl_platform` fixture to preserve them, plus `TestConfigUbuntuDefaults` for native Ubuntu assertions.
- Changed lines for PR 1 are ~257 (slightly above the ~200 estimate) due to additional triangulation tests and comprehensive test fixture coverage needed to keep the suite green.
- Pre-existing `.gitignore` change (`.atl/`) is not part of this PR.

### Phase 1 Completion

- [x] 1.1 Create platform.py
- [x] 1.2 Modify config.py
- [x] 1.3 Modify services.py
- [x] 1.4 RED tests
- [x] 1.5 GREEN tests

## PR 2: PHP-FPM & Nginx Wiring (completed)

**What**: Implemented PR 2 (Phase 2: PHP-FPM & Nginx Wiring) for ubuntu-main-adaptation on branch feature/ubuntu-evaluate-main.

**Why**: Make PHP version switching safer by verifying the target FPM package before stopping the current FPM, and make Nginx resilient to generic PHP-FPM socket paths on Ubuntu.

**Where**:
- Modified `src/wslaragon/services/php.py`
  - Added `_is_fpm_package_installed(version)` helper using `dpkg -l php{version}-fpm`
  - Added fail-fast check at the start of `switch_version()`
- Modified `src/wslaragon/services/nginx.py`
  - Added `_get_php_fpm_socket()` helper
  - Updated `create_site_config()` to use the discovered socket path
- Modified `tests/unit/test_php.py`
  - Added `test_switch_version_aborts_when_fpm_missing`
  - Added `TestPHPManagerIsFpmPackageInstalled` with installed / not-installed / error cases
  - Added class-scoped autouse fixture `assume_target_fpm_installed` so existing switch_version tests stay focused on switch logic
- Modified `tests/unit/test_nginx.py`
  - Added `TestNginxManagerGetPhpFpmSocket` with versioned path, generic fallback, and missing-socket error cases
  - Added autouse fixture `mock_versioned_fpm_socket` in `TestNginxManagerCreateSiteConfig` so PHP site-config tests see the versioned socket

**Learned**:
- `switch_version` now returns `False` and logs an error when the target `php{version}-fpm` package is not installed, leaving the current FPM untouched.
- `_get_php_fpm_socket` checks `/run/php/php{version}-fpm.sock` first, then falls back to `/run/php/php-fpm.sock`, raising `RuntimeError` if neither exists.
- Existing `create_site_config` tests were sensitive to real socket discovery because they ran without sockets on disk; mocking `_get_php_fpm_socket` keeps them deterministic.
- The original `nginx.py` had pre-existing whitespace / trailing-space lint issues. New code follows the same style, but a separate lint pass would touch many lines.
- Full unit suite after PR 2: `pytest tests/unit/ -v --tb=short` → 1334 passed, 100% coverage.

### Phase 2 Completion

- [x] 2.1 RED: add failing `test_switch_version_aborts_when_fpm_missing`
- [x] 2.2 Modify `src/wslaragon/services/php.py` to pre-check target FPM package before stopping current FPM
- [x] 2.3 RED: add failing socket discovery tests for versioned + generic paths
- [x] 2.4 Modify `src/wslaragon/services/nginx.py` to add `_get_php_fpm_socket()` with `/run/php/php{version}-fpm.sock` fallback to `php-fpm.sock`
- [x] 2.5 Update `tests/unit/test_php.py` and `tests/unit/test_nginx.py`

## PR 3: Hosts, Sudo Keep-Alive & Permissions (completed)

**What**: Implemented PR 3 (Phase 3: Hosts, Sudo Keep-Alive & Permissions) for ubuntu-main-adaptation on branch feature/ubuntu-evaluate-main.

**Why**: Keep sudo credentials alive during long site creation, manage `/etc/hosts` safely on native Ubuntu via `sudo tee`, and grant `www-data` read access using POSIX ACLs with a chmod fallback.

**Where**:
- Modified `src/wslaragon/services/sites.py`
  - Added `SudoKeepAlive` context manager (daemon thread running `sudo -n -v` every 15s)
  - Modified `fix_permissions()` to try `sudo setfacl -R -m u:www-data:rx` and fall back to `sudo chmod -R o+rx` when `setfacl` is unavailable
- Modified `src/wslaragon/services/ssl.py`
  - Added `hosts_file` config support defaulting to `/etc/hosts`
  - Added platform-aware `add_to_hosts()` / `remove_from_hosts()` methods
  - Native Ubuntu path uses `sudo tee -a /etc/hosts` (add) and `sudo tee /etc/hosts` (remove)
  - WSL path keeps existing PowerShell-based Windows hosts handling
  - Updated `generate_cert()`, `setup_ssl_for_site()`, and `revoke_certificate()` to call the new hosts helpers
- Modified `src/wslaragon/cli/site_commands.py`
  - Imported `SudoKeepAlive` from `services.sites`
  - Wrapped `site_mgr.create_site()` and `site_mgr.create_headless_site()` calls with `SudoKeepAlive()`
- Modified `tests/unit/test_sites.py`
  - Added `TestSudoKeepAlive` with refresh-emission and context-manager tests
  - Added `TestSiteManagerFixPermissions` with setfacl-available, chmod-fallback, and failure-path tests
- Modified `tests/unit/test_ssl.py`
  - Added `TestSSLManagerHostsUbuntu` covering `sudo tee` add/remove on Ubuntu, skip-on-existing-entry, and WSL fallback
  - Updated existing revoke/generate tests to mock `add_to_hosts` / `remove_from_hosts`
- Modified `tests/unit/test_site_commands.py`
  - Added tests asserting `create_site` and `create_headless_site` are wrapped in `SudoKeepAlive`

**Learned**:
- `SudoKeepAlive` must swallow refresh failures so a transient `sudo -n -v` failure does not crash site creation; failures are logged at debug level.
- The WSL code path must remain untouched; `Platform.is_wsl()` gates the Windows-hosts behavior.
- Existing `fix_permissions` comprehensive tests still pass because chown and g+s steps are preserved; the chmod 775 step is replaced by setfacl/chmod fallback.
- Full unit suite after PR 3: `pytest tests/unit/ -q --tb=short` → 1345 passed, 99.70% coverage.

### Phase 3 Completion

- [x] 3.1 RED: add failing `test_sudo_keep_alive_emits_refresh` and `test_apply_permissions_chmod_fallback`
- [x] 3.2 Create `SudoKeepAlive` context manager in `src/wslaragon/services/sites.py`
- [x] 3.3 Modify `src/wslaragon/services/ssl.py` `add_to_hosts`/`remove_from_hosts` to use `sudo tee` on `/etc/hosts` for native Ubuntu
- [x] 3.4 Modify `src/wslaragon/services/sites.py` `fix_permissions()` to try `setfacl -R -m u:www-data:rx` and fall back to `chmod`
- [x] 3.5 Modify `src/wslaragon/cli/site_commands.py` to wrap `create_site`/`create_headless_site` with `SudoKeepAlive`
- [x] 3.6 Update `tests/unit/test_ssl.py`, `tests/unit/test_sites.py`, `tests/unit/test_site_commands.py`

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 3.1 | `tests/unit/test_sites.py` | Unit | ✅ 196/196 affected tests passing | ✅ Written | ✅ Passed | ✅ Context + failure path | ✅ Clean loop helper |
| 3.2 | `tests/unit/test_sites.py` | Unit | ✅ see above | ✅ Refresh test | ✅ Passed | ✅ Daemon thread test | ✅ Removed unused `time` import |
| 3.3 | `tests/unit/test_ssl.py` | Unit | ✅ see above | ✅ Ubuntu hosts tests | ✅ Passed | ✅ WSL fallback + skip-existing | ✅ Reused existing Windows helpers |
| 3.4 | `tests/unit/test_sites.py` | Unit | ✅ see above | ✅ setfacl/chmod tests | ✅ Passed | ✅ Failure path | ✅ Used `shutil.which` |
| 3.5 | `tests/unit/test_site_commands.py` | Unit | ✅ see above | ✅ Wrap tests | ✅ Passed | ✅ Headless + normal | ✅ Minimal context nesting |
| 3.6 | `tests/unit/test_ssl.py`, `tests/unit/test_sites.py`, `tests/unit/test_site_commands.py` | Unit | ✅ see above | ✅ Updated mocks | ✅ Passed | ✅ Existing tests adjusted | ✅ Renamed helpers |

## Test Summary

- **Total tests written**: 14 new (2 sudo + 3 permissions + 4 hosts + 2 CLI wraps + 3 updated)
- **Total tests passing**: 1345 unit tests
- **Coverage**: 99.70% (required 90%)
- **Layers used**: Unit only
- **Approval tests**: None — no refactoring tasks
- **Pure functions created**: None (behavior is I/O/threading bound)

## Work Unit Evidence

| Evidence | Value |
|----------|-------|
| Focused test command | `pytest tests/unit/test_ssl.py tests/unit/test_sites.py tests/unit/test_site_commands.py -v --tb=short` |
| Focused test result | 207 passed |
| Full unit suite command | `pytest tests/unit/ -q --tb=short` |
| Full unit suite result | 1345 passed, 99.70% coverage |
| Runtime harness | `wslaragon site create ubu1 --html` on Ubuntu VM (manual integration, not executed in unit test environment) |
| Rollback boundary | Revert `src/wslaragon/services/ssl.py`, `src/wslaragon/services/sites.py`, `src/wslaragon/cli/site_commands.py`, plus test changes in `tests/unit/test_ssl.py`, `tests/unit/test_sites.py`, `tests/unit/test_site_commands.py` |

## PR 4: Configurable DB User & Site Creators (completed)

**What**: Implemented PR 4 (Phase 4: MySQL User & Site Creators) for ubuntu-main-adaptation on branch feature/ubuntu-evaluate-main.

**Why**: Allow WordPress and Laravel site creators to use a configurable MariaDB/MySQL user instead of hard-coded `root`, aligning with the Ubuntu-native installer that creates a `wslaragon` user.

**Where**:
- Modified `src/wslaragon/services/site_creators.py`
  - `WordPressSiteCreator.create()` now reads `mysql.user` from config and writes `DB_USER` into `wp-config.php`
  - `LaravelSiteCreator.create()` MySQL branch now reads `mysql.user` from config and writes `DB_USERNAME` into `.env`
- Modified `tests/conftest.py`
  - Extracted `_make_mock_config` helper
  - Added `mock_config_ubuntu` fixture with `mysql.user=wslaragon` and `mysql.password=wslaragon_pass`
- Modified `tests/unit/test_site_creators.py`
  - Added `test_site_creator_uses_configured_db_user` (WordPress)
  - Added `test_laravel_creator_uses_configured_db_user`
- Modified `tests/unit/test_mysql.py`
  - Added `test_init_uses_configured_mysql_user` using `mock_config_ubuntu`

**Learned**:
- `src/wslaragon/services/mysql.py` already sourced `default_user` from `config.get('mysql.user', 'root')`, so no source change was required for 4.2; the new test confirms the contract.
- The default `root` fallback is preserved for backward compatibility per the spec.
- Full unit suite after PR 4: `pytest tests/unit/ -v --tb=short` → 1348 passed, 99.70% coverage.

### Phase 4 Completion

- [x] 4.1 RED: add failing `test_site_creator_uses_configured_db_user`
- [x] 4.2 Modify `src/wslaragon/services/mysql.py` to use `config.get('mysql.user')` as default user
- [x] 4.3 Modify `src/wslaragon/services/site_creators.py` `WordPressSiteCreator` and `LaravelSiteCreator` to use configured `DB_USER`/`DB_PASSWORD`
- [x] 4.4 Update `tests/unit/test_mysql.py`, `tests/unit/test_site_creators.py`, and `tests/conftest.py` fixtures

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 4.1 | `tests/unit/test_site_creators.py` | Unit | ✅ 220/220 focused tests passing | ✅ WP + Laravel fail as expected | ✅ Pass after site_creators fix | ✅ Both creators covered | ✅ Reused config.get pattern |
| 4.2 | `tests/unit/test_mysql.py` | Unit | ✅ see above | ✅ New init test fails if default_user not from config | ✅ Passes (mysql.py already compliant) | ✅ Ubuntu fixture asserts wslaragon | ✅ No source change needed |
| 4.3 | `src/wslaragon/services/site_creators.py` | Unit | ✅ see above | ✅ RED tests above | ✅ WP/Laravel read mysql.user | ✅ Default root preserved | ✅ Minimal variable insertion |
| 4.4 | `tests/conftest.py`, `tests/unit/test_mysql.py`, `tests/unit/test_site_creators.py` | Unit | ✅ see above | ✅ New fixtures/tests | ✅ Pass | ✅ WSL + Ubuntu fixture parity | ✅ Extracted `_make_mock_config` helper |

## Test Summary

- **Total tests written**: 3 new (1 MySQL init + 2 site creators)
- **Total tests passing**: 1348 unit tests
- **Coverage**: 99.70% (required 90%)
- **Layers used**: Unit only
- **Approval tests**: None

## Work Unit Evidence

| Evidence | Value |
|----------|-------|
| Focused test command | `pytest tests/unit/test_mysql.py tests/unit/test_site_creators.py -v --tb=short` |
| Focused test result | 220 passed |
| Full unit suite command | `pytest tests/unit/ -v --tb=short` |
| Full unit suite result | 1348 passed, 99.70% coverage |
| Runtime harness | `wslaragon site create wp1 --wordpress --mysql` on Ubuntu VM (manual integration, not executed in unit test environment) |
| Rollback boundary | Revert `src/wslaragon/services/site_creators.py`, `tests/conftest.py`, `tests/unit/test_mysql.py`, `tests/unit/test_site_creators.py` |

## PR 5: Installer Scripts & Ubuntu Docs (completed)

**What**: Implemented PR 5 (Phase 5: Installer Scripts & Ubuntu Docs) for ubuntu-main-adaptation on branch feature/ubuntu-evaluate-main.

**Why**: Provide native Ubuntu install/uninstall scripts, project metadata that no longer claims WSL2-only support, and user-facing documentation for the Ubuntu stack.

**Where**:
- Modified `scripts/vars.sh`
  - Added `HOSTS_FILE="/etc/hosts"` for native Ubuntu hosts management
  - `PHP_VERSION` already set to `8.5`
- Modified `scripts/setup-env.sh`
  - Removed WSL2-only warning
  - Added `detect_platform()` helper that reports `wsl2`, `ubuntu`, or `unknown`
  - Fixed pre-existing line-34 bug where `PHP_INSTALLED_VERSION` and `echo` were on the same line
- Modified `scripts/install.sh`
  - Added `install_php()` helper with PPA fallback to `ppa:ondrej/php` when `php8.5-fpm` is unavailable
  - Added installation of Composer, NVM, Node.js LTS, pnpm, and phpMyAdmin
  - Added MariaDB step that creates the `wslaragon`@`localhost` user with full grants
  - Refactored shell completion `.bashrc` append to pass `shellcheck`
  - Added `shellcheck` directives for intentional non-constant `source ~/.bashrc`
- Created `scripts/uninstall.sh`
  - Default mode stops/disables services and removes packages while preserving `~/.wslaragon` and `~/web`
  - `--purge` flag requires typing `yes` and removes site data, config, and the `wslaragon` database user
- Modified `pyproject.toml`
  - Changed description to "Laragon-style development environment manager for Ubuntu and WSL2"
- Modified `src/wslaragon/cli/main.py`
  - Updated `cli` callback docstring to mention Ubuntu and WSL2
- Created `docs/UBUNTU.md`
  - Covers prerequisites, installation, site creation, SSL, service management, database access, uninstall, and troubleshooting
- Created `tests/unit/test_installer.py`
  - 15 unit assertions covering `vars.sh`, `setup-env.sh`, `install.sh`, `uninstall.sh`, project metadata, and `shellcheck` linting
  - `shellcheck` was not installed in the apply environment; installed via `pip install shellcheck-py` and scripts pass `shellcheck -x --severity=warning`

**Learned**:
- Static shell-script content can be unit-tested in Python by reading scripts and asserting expected strings/commands; this keeps the TDD cycle fast and CI-friendly.
- `shellcheck` warnings about unused variables in `vars.sh` are expected because the file is sourced; adding `# shellcheck disable=SC2034` is the cleanest fix.
- `shellcheck` cannot follow dynamic `source` paths; use `-x` plus explicit directives for known non-constant sources like `~/.bashrc`.
- Full unit suite after PR 5: `pytest tests/unit/ -v --tb=short` → 1363 passed, 1 skipped (shellcheck not present until installed), 99.70% coverage.

### Phase 5 Completion

- [x] 5.1 Modify `scripts/vars.sh`: set `HOSTS_FILE=/etc/hosts`, `PHP_VERSION=8.5`
- [x] 5.2 Modify `scripts/setup-env.sh`: remove WSL-only warning, add platform check
- [x] 5.3 Modify `scripts/install.sh`: Ubuntu stack, PHP 8.5 PPA fallback, create `wslaragon` MariaDB user/grants
- [x] 5.4 Create `scripts/uninstall.sh`: default preserves data, `--purge` requires confirmation
- [x] 5.5 Update `pyproject.toml` description and `src/wslaragon/cli/main.py` docstring to drop WSL2-only wording
- [x] 5.6 Create `docs/UBUNTU.md` with install, site creation, SSL, and uninstall steps
- [x] 5.7 Add shell script linting and installer unit assertions

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.1 | `tests/unit/test_installer.py` | Unit | ✅ 1348/1348 passing | ✅ HOSTS_FILE assertion fails | ✅ Pass after vars.sh update | ✅ PHP_VERSION assertion also covers default | ✅ Single HOSTS_FILE addition |
| 5.2 | `tests/unit/test_installer.py` | Unit | ✅ see above | ✅ WSL-only warning detected | ✅ Pass after removal + platform check | ✅ Platform check asserts `/proc/version` | ✅ Fixed pre-existing line-34 bug |
| 5.3 | `tests/unit/test_installer.py` | Unit | ✅ see above | ✅ PPA + wslaragon assertions fail | ✅ Pass after install.sh update | ✅ Ubuntu stack tools (composer, nvm, pnpm, phpMyAdmin) covered | ✅ shellcheck directives + grouped bashrc append |
| 5.4 | `tests/unit/test_installer.py` | Unit | ✅ see above | ✅ uninstall.sh missing | ✅ Created and passes | ✅ Default preserve + purge confirmation + service/package removal | ✅ Extracted reusable `scripts_dir` fixture |
| 5.5 | `tests/unit/test_installer.py` | Unit | ✅ see above | ✅ WSL2-only wording detected | ✅ Pass after metadata update | ✅ Asserts Ubuntu mention | ✅ Kept existing WSL2 compatibility wording |
| 5.6 | `docs/UBUNTU.md` | N/A (docs) | ✅ see above | ✅ N/A structural | ✅ Document created | ✅ N/A | ✅ Clear sections matching spec |
| 5.7 | `tests/unit/test_installer.py` | Unit | ✅ see above | ✅ shellcheck test skipped initially | ✅ shellcheck-py installed; scripts pass | ✅ 15 installer assertions | ✅ Used `-x --severity=warning` for practical CI |

## Test Summary

- **Total tests written**: 15 new installer/script assertions
- **Total tests passing**: 1363 unit tests
- **Coverage**: 99.70% (required 90%)
- **Layers used**: Unit only
- **Approval tests**: None
- **Pure functions created**: None (script inspection tests)

## Work Unit Evidence

| Evidence | Value |
|----------|-------|
| Focused test command | `pytest tests/unit/test_main_cli.py tests/unit/test_installer.py -v --tb=short && shellcheck -x --severity=warning scripts/*.sh` |
| Focused test result | 15 installer tests passed; shellcheck returned 0 |
| Full unit suite command | `pytest tests/unit/ -v --tb=short` |
| Full unit suite result | 1363 passed, 1 skipped, 99.70% coverage |
| Runtime harness | `scripts/install.sh` and `scripts/uninstall.sh` on fresh Ubuntu VM (manual integration, not executed in unit test environment) |
| Rollback boundary | Revert `scripts/vars.sh`, `scripts/setup-env.sh`, `scripts/install.sh`, delete `scripts/uninstall.sh`, delete `docs/UBUNTU.md`, revert `pyproject.toml`, `src/wslaragon/cli/main.py`, `tests/unit/test_installer.py` |

## PR 6: MCP Runtime Alignment (completed)

**What**: Implemented PR 6 (Phase 6: MCP Runtime Alignment) for ubuntu-main-adaptation on branch feature/ubuntu-evaluate-main.

**Why**: Keep the MCP server functional on native Ubuntu by resolving service names from config and exposing runtime context (hosts file, PHP version, FPM socket, DB user) through the `agent_init` tool signature.

**Where**:
- Modified `src/wslaragon/mcp/server.py`
  - Added `_get_config()` lazy helper so tests can mock config without forcing module-level instantiation
  - Added `_runtime_context(config)` helper returning hosts_file, php_version, fpm_socket, db_user
  - Modified `resource_services()` to read `php.version` from config and build `php{version}-fpm` service name
  - Updated `agent_init()` signature with optional `hosts_file`, `php_version`, `fpm_socket`, `db_user` parameters
  - `agent_init()` derives context from config when parameters are omitted and returns the runtime context in its success response
- Modified `tests/unit/test_mcp_server.py`
  - Added `TestMcpUbuntuRuntime::test_mcp_uses_ubuntu_service_names` RED/GREEN test for config-driven PHP-FPM service name
  - Updated `TestResourceServices::test_resource_services_mixed_status` to mock `_get_config` with a specific PHP version
  - Added `TestAgentInit::test_agent_init_includes_runtime_context` and `test_agent_init_accepts_runtime_context_overrides`

**Learned**:
- Strict TDD active; followed RED → GREEN → TRIANGULATE → REFACTOR for both service-name resolution and agent-init runtime context.
- Lazy-loading `Config` inside `_get_config()` avoids instantiating it at module import time, which keeps the existing `mock_mcp_module` fixture working without side effects.
- `resource_services()` is now config-driven; tests must mock `_get_config()` or they will pick up the real platform defaults.
- Full unit suite after PR 6: `pytest tests/unit/ -v --tb=short` → 1366 passed, 99.67% coverage.

### Phase 6 Completion

- [x] 6.1 RED: add failing `test_mcp_uses_ubuntu_service_names`
- [x] 6.2 Modify `src/wslaragon/mcp/server.py` to resolve service names from config and update `agent_init` runtime context signature
- [x] 6.3 Update `tests/unit/test_mcp_server.py`

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 6.1 | `tests/unit/test_mcp_server.py` | Unit | ✅ 156/156 passing | ✅ Written | ✅ Passed | ✅ Config-driven 8.3 + 8.5 | ✅ Lazy `_get_config` helper |
| 6.2 | `src/wslaragon/mcp/server.py` | Unit | ✅ see above | ✅ service + signature tests fail | ✅ Pass after server.py update | ✅ Ubuntu default + WSL fallback via config | ✅ Extracted `_runtime_context` |
| 6.3 | `tests/unit/test_mcp_server.py` | Unit | ✅ see above | ✅ Updated mixed-status test fails | ✅ Pass after config mock | ✅ Runtime context default + override | ✅ Minimal test additions |

## Test Summary

- **Total tests written**: 3 new (1 service name + 2 agent_init context)
- **Total tests passing**: 1366 unit tests
- **Coverage**: 99.67% (required 90%)
- **Layers used**: Unit only
- **Approval tests**: None
- **Pure functions created**: 1 (`_runtime_context`)

## Work Unit Evidence

| Evidence | Value |
|----------|-------|
| Focused test command | `pytest tests/unit/test_mcp_server.py -v --tb=short` |
| Focused test result | 159 passed |
| Full unit suite command | `pytest tests/unit/ -v --tb=short` |
| Full unit suite result | 1366 passed, 99.67% coverage |
| Runtime harness | `wslaragon-mcp` status resource on Ubuntu VM (manual integration, not executed in unit test environment) |
| Rollback boundary | Revert `src/wslaragon/mcp/server.py` and `tests/unit/test_mcp_server.py` |

## Remediation Batch 1: Verify findings F1/F2

**What**: Fixed the two CRITICAL findings reported by `sdd-verify` and re-ran the affected verification commands.

**Why**: `scripts/setup-env.sh` emitted invalid YAML that broke first-time config generation, and the integration suite failed the project-wide coverage gate even though all integration tests passed.

**Where**:
- `scripts/setup-env.sh`: split `version` and `ini_file` onto separate YAML lines.
- `tests/unit/test_installer.py`: added `_render_setup_env_config` helper, `test_generated_config_yaml_is_valid`, and `test_generated_config_yaml_accepts_alternate_php_version` to verify the heredoc parses as valid YAML for default and alternate PHP versions.
- `docs/UBUNTU.md`: added a **Testing** section documenting the unit, integration (`--no-cov`), and shellcheck commands.
- `tests/integration/test_integration.py`: updated module docstring to include `--no-cov`.

**Learned**:
- Strict TDD active; wrote RED tests before the production fix and docs update.
- The project-wide `--cov-fail-under=90` threshold must remain in `pyproject.toml` for unit tests; integration tests are run with `--no-cov` to bypass it.
- Unit suite: `pytest tests/unit/ -q --tb=short` → **1369 passed, 99.67% coverage**.
- Integration suite: `pytest tests/integration/ -v --run-slow --tb=short --no-cov` → **32 passed, 1 skipped**.
- Shell lint: `shellcheck -x --severity=warning scripts/*.sh` → clean.
- Remediation is focused on the failed verification transaction; VM-based tasks 7.2 and 7.3 remain pending.

### Remediation Completion

- [x] R1 Fix `scripts/setup-env.sh` line 75 YAML defect.
- [x] R2 Add unit-test coverage for the generated config YAML.
- [x] R3 Document `--no-cov` integration workflow.
- [x] R4 Run unit suite with coverage.
- [x] R5 Run integration suite with `--no-cov`.
- [x] R6 Run shell lint.

### TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| R1 | `tests/unit/test_installer.py` | Unit | ✅ 15/15 | ✅ YAML parse fails | ✅ Pass after line split | ✅ Default + alternate PHP version | ➖ None needed |
| R3 | `tests/unit/test_installer.py` | Unit | ✅ see above | ✅ Docs assertion fails | ✅ Pass after UBUNTU.md update | ➖ Single instruction | ➖ None needed |

### Test Summary

- **Total tests written**: 3 new (2 setup-env YAML + 1 docs instruction)
- **Total tests passing**: 1369 unit tests
- **Coverage**: 99.67% (required 90%)
- **Layers used**: Unit only
- **Approval tests**: None
- **Pure functions created**: 1 (`_render_setup_env_config` helper)

### Work Unit Evidence

| Evidence | Value |
|----------|-------|
| Focused test command | `pytest tests/unit/test_installer.py -v --tb=short --no-cov` |
| Focused test result | 18 passed |
| Full unit suite command | `pytest tests/unit/ -q --tb=short` |
| Full unit suite result | 1369 passed, 99.67% coverage |
| Runtime harness | `pytest tests/integration/ -v --run-slow --tb=short --no-cov` |
| Runtime harness result | 32 passed, 1 skipped |
| Static harness | `shellcheck -x --severity=warning scripts/*.sh` |
| Static harness result | clean |
| Rollback boundary | Revert `scripts/setup-env.sh`, `tests/unit/test_installer.py`, `docs/UBUNTU.md`, `tests/integration/test_integration.py` |

## Next Recommended

1. Re-run `sdd-verify` to confirm F1/F2 are resolved.
2. Execute VM-based tasks 7.2 and 7.3 on a fresh Ubuntu host before archive.