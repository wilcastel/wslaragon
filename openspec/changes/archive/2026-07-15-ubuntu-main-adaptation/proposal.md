# Proposal: Ubuntu Native Support for origin/main

## Intent

Adapt `origin/main` to run natively on Ubuntu while preserving every feature currently in main. The project currently targets WSL2/Windows (writes the Windows hosts file via PowerShell, hard-codes PHP 8.3, assumes MySQL `root`). The goal is to port only the Ubuntu-specific fixes from `feature/ubuntu-native-support` and add runtime detection so the same codebase works on Ubuntu without regressing headless sites, Astro SSG, API proxies, `php upload-limit`, or expanded MCP tools.

## Scope

### In Scope
- Runtime detection for the hosts file path (`/etc/hosts`) and the PHP-FPM socket.
- Configurable PHP version, MySQL user, and FPM service name defaults.
- Ubuntu hosts file operations via `sudo tee`.
- PHP-FPM socket discovery with fallback for `/run/php/php{version}-fpm.sock` and generic `php-fpm.sock`.
- Safer `php switch_version` when the target FPM package is not installed.
- Sudo keep-alive helper for long site-creation runs.
- ACL-based `www-data` permissions with a `chmod` fallback.
- Site creators use the configured MySQL user instead of hard-coded `root`.
- Ubuntu install/uninstall scripts for PHP 8.5, MariaDB, Nginx, Composer, NVM, pnpm, mkcert, phpMyAdmin.
- Update `pyproject.toml`, CLI description, and docs (`docs/UBUNTU.md`).
- Update tests and fixtures to match Ubuntu defaults.

### Out of Scope
- Replaying `feature/ubuntu-native-support` and re-adding main features.
- Removing any existing main feature.
- Windows/WSL-specific user guides (keep existing ones).
- Full dual WSL+Ubuntu compatibility layer beyond cheap runtime detection.

## Capabilities

### New Capabilities
- `ubuntu-host-management`: Edit `/etc/hosts` with `sudo tee` on native Ubuntu.
- `ubuntu-php-fpm`: Detect and configure PHP-FPM service name and socket on Ubuntu.
- `ubuntu-mysql-user`: Use a configurable MariaDB user instead of `root`.
- `ubuntu-site-creation`: Create sites with sudo keep-alive and `www-data` ACL permissions.
- `ubuntu-installer`: Install and uninstall the full Ubuntu stack.
- `ubuntu-mcp-runtime`: Keep all MCP tools but update Ubuntu service names and agent init signatures.

### Modified Capabilities
None — existing main capabilities are only being adapted for Ubuntu; no behavioral requirements are removed.

## Approach

Use Approach 1 from exploration: minimal port of Ubuntu fixes onto current main with cheap runtime detection. Keep the main architecture and all features intact. Apply changes file-by-file from the reference branch, rejecting any deletion of main features. Deliver as chained PRs because the total change will exceed the 400-line review budget.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/wslaragon/core/config.py` | Modified | PHP/MySQL/hosts defaults |
| `src/wslaragon/core/services.py` | Modified | FPM service name |
| `src/wslaragon/services/nginx.py` | Modified | Socket discovery |
| `src/wslaragon/services/php.py` | Modified | Safer `switch_version` |
| `src/wslaragon/services/ssl.py` | Modified | `/etc/hosts` operations |
| `src/wslaragon/services/sites.py` | Modified | Sudo keep-alive, ACLs |
| `src/wslaragon/services/site_creators.py` | Modified | Configurable `DB_USER` |
| `src/wslaragon/services/mysql.py` | Modified | Configurable default user |
| `src/wslaragon/cli/site_commands.py` | Modified | `SudoKeepAlive` integration |
| `src/wslaragon/cli/php_commands.py` | Modified | Ensure `upload-limit` stays |
| `src/wslaragon/mcp/server.py` | Modified | Service names, agent init |
| `scripts/install.sh` | Modified | Ubuntu stack |
| `scripts/uninstall.sh` | New | Clean removal |
| `scripts/vars.sh` | Modified | `HOSTS_FILE` |
| `scripts/setup-env.sh` | Modified | Linux detection |
| `pyproject.toml` / `main.py` | Modified | Drop "for WSL2" |
| `docs/UBUNTU.md` | New | Ubuntu guide |
| `tests/` | Modified | Fixtures/expectations |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Feature regression | Med | Reject any deletion from reference branch; verify each feature |
| PHP 8.5 unavailable | Med | PPA fallback or version pinning |
| MariaDB user migration | Med | Create user/grants in install script; document env updates |
| Sudo timeout | High | `SudoKeepAlive` helper |
| Missing ACL tools | Low | `chmod` fallback |
| Socket discovery fails | Med | Test multiple fallback paths |
| Review exceeds budget | High | Chained PRs per slice |

## Rollback Plan

1. Revert the offending PR/branch. Most changes are additive or config-driven; core logic remains intact.
2. For install script changes, use `scripts/uninstall.sh` to remove packages.
3. If the default user change breaks existing sites, restore `root` via a config override.

## Dependencies

- Ubuntu test environment (native or VM).
- sudo access and configured sudoers.
- Internet access for PPA/Composer/NVM.

## Success Criteria

- [ ] All existing tests pass with updated fixtures.
- [ ] `site create` works on Ubuntu for WordPress, Laravel, and headless sites.
- [ ] SSL/hosts file updates apply via `/etc/hosts`.
- [ ] PHP-FPM socket detection works for PHP 8.5.
- [ ] `php upload-limit` updates both PHP and Nginx.
- [ ] Install script provisions a clean Ubuntu system end-to-end.
- [ ] No main feature removed or disabled.
