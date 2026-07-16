# Design: Ubuntu Native Support for origin/main

## Technical Approach

Add runtime platform detection and Ubuntu-native defaults while preserving every origin/main feature. Changes are additive/config-driven; no main capability (headless sites, API proxies, MCP tool surface, multi-version PHP config, `update_client_max_body_size`, SvelteKit) is removed. WSL2 keeps the existing Windows-hosts/PowerShell path.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Platform detection | New `core/platform.py` helper | Inline checks in `Config` | Testable, single source of truth |
| Hosts file | Add `hosts.hosts_file` + runtime selection | Keep only `windows.hosts_file` | Native Ubuntu uses `/etc/hosts`; WSL2 unchanged |
| PHP/MySQL defaults | Platform-aware defaults with env override | Hard-code 8.5 / `wslaragon` | Native Ubuntu: 8.5 / `wslaragon`; WSL2: 8.3 / `root` |
| FPM socket | `NginxManager._get_php_fpm_socket()` with fallback | Hard-coded versioned socket | Resilient to generic `php-fpm.sock` |
| Sudo keep-alive | Daemon thread `sudo -n -v` every 15s | Repeated prompts | Non-intrusive, works for long scaffolding |
| Permissions | POSIX ACLs for `www-data` + chmod fallback | Always chmod 775 | Fine-grained; works without `setfacl` |

## Data Flow

```
Config._load_config()
   ▼
Platform.is_wsl()
   ├─ No  → defaults: hosts=/etc/hosts, php=8.5, mysql.user=wslaragon
   └─ Yes → WSL2 defaults: windows.hosts_file, php=8.3, mysql.user=root

SiteManager.create_site()
   ▼
SudoKeepAlive ──► creators ──► SSLManager.add_to_hosts()
   │                              └─ sudo tee -a /etc/hosts
   ▼
fix_permissions() ──► _apply_www_data_permissions() ──► setfacl or chmod
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/wslaragon/core/platform.py` | Create | `is_wsl()`, `is_native_ubuntu()`, `hosts_file()` |
| `src/wslaragon/core/config.py` | Modify | Platform-aware defaults; add `hosts.hosts_file` |
| `src/wslaragon/core/services.py` | Modify | `php-fpm` service from config version |
| `src/wslaragon/services/nginx.py` | Modify | `_get_php_fpm_socket()`; keep `update_client_max_body_size` |
| `src/wslaragon/services/php.py` | Modify | Pre-flight FPM package check; keep multi-version helpers |
| `src/wslaragon/services/ssl.py` | Modify | `add_to_hosts`/`remove_from_hosts` via `sudo tee`; keep WSL2 path |
| `src/wslaragon/services/sites.py` | Modify | ACL helpers; preserve headless/API-proxy/cleanup |
| `src/wslaragon/services/site_creators.py` | Modify | Configurable `DB_USER`; sudo refresh helper; preserve SvelteKit |
| `src/wslaragon/services/mysql.py` | Modify | Default user from config |
| `src/wslaragon/cli/site_commands.py` | Modify | `SudoKeepAlive` around `create_site` |
| `src/wslaragon/mcp/server.py` | Modify | Dynamic service names; keep full tool surface |
| `scripts/install.sh` | Modify | Ubuntu stack, PHP 8.5 PPA fallback, create MariaDB user |
| `scripts/uninstall.sh` | Create | Default preserves data; `--purge` with confirmation |
| `scripts/vars.sh` | Modify | `HOSTS_FILE=/etc/hosts`, `PHP_VERSION=8.5` |
| `scripts/setup-env.sh` | Modify | Remove WSL-only warning |
| `pyproject.toml`, `src/wslaragon/cli/main.py` | Modify | Drop WSL2-only wording |
| `docs/UBUNTU.md` | Create | Setup, usage, SSL, uninstall |
| `tests/` | Modify | Ubuntu fixtures; platform/socket/ACL/keep-alive tests |

## Interfaces / Contracts

```python
class Platform:
    @staticmethod
    def is_wsl() -> bool: ...
    @staticmethod
    def hosts_file(config: Config) -> Path: ...

class NginxManager:
    def _get_php_fpm_socket(self) -> str: ...

class SudoKeepAlive:
    def __enter__(self) -> "SudoKeepAlive": ...
    def __exit__(self, *args) -> None: ...
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | Platform detection | Mock `/proc/version` and `WSL_DISTRO_NAME` |
| Unit | Socket discovery | Mock `Path.exists()` / `glob` |
| Unit | Hosts write | Assert `sudo tee` call |
| Unit | Sudo keep-alive | Mock thread, assert `sudo -n -v` |
| Unit | ACL fallback | Mock `shutil.which('setfacl')` as `None` |
| Unit | PHP switch safety | Mock missing package, assert abort |
| Unit | Service name | Assert `php{version}-fpm` follows config |
| Integration | `site create` on Ubuntu | Mark `requires_sudo` |

## Threat Matrix

`references/threat-matrix.md` is absent. The change touches subprocess/sudo/service boundaries:

| Threat | Applicable | Safe Behavior | RED Test |
|--------|------------|---------------|----------|
| Shell injection via site name | Yes | Validate `^[a-zA-Z0-9_.-]+$` | `test_create_site_validates_name` |
| Sudo timeout | Yes | `SudoKeepAlive` every 15s | `test_sudo_keep_alive_emits_refresh` |
| Wrong hosts file edited | Yes | `Platform.hosts_file()` selects path | `test_hosts_file_native_ubuntu`, `test_hosts_file_wsl2` |
| FPM switch leaves no FPM | Yes | Pre-check package before stopping | `test_switch_version_aborts_when_fpm_missing` |
| ACL tools missing | Yes | Fallback to chmod | `test_apply_permissions_chmod_fallback` |
| Service name mismatch | Yes | Derive from config version | `test_service_manager_uses_configured_php_version` |

## Migration / Rollout

- New config keys are added automatically on next `Config` init.
- WSL2 users keep current behavior unless `config.yaml` is deleted.
- `install.sh` creates the `wslaragon` MariaDB user.
- `uninstall.sh` default preserves data; `--purge` requires confirmation.

## Open Questions

- Keep `windows.hosts_file` key or rename to `hosts.wsl_hosts_file`?
- Verify PHP 8.5 package availability and PPA fallback on the target Ubuntu LTS.
