## Exploration: Ubuntu native adaptation of origin/main

### Current State

`feature/ubuntu-evaluate-main` is a clean checkout of `origin/main`. It targets WSL2/Windows: it writes to the Windows hosts file via PowerShell, assumes PHP 8.3, defaults MySQL to `root`, and uses hard-coded PHP-FPM socket paths.

`feature/ubuntu-native-support` is a working Ubuntu adaptation, but it diverged from an **older** snapshot of main (before headless sites, Astro SSG, API proxies, `php upload-limit`, expanded MCP tools, and many tests). The branch therefore contains two kinds of changes:

1. **Real Ubuntu fixes** we need to port.
2. **Feature removals** we must NOT port; those features should stay in main and be made Ubuntu-compatible instead.

The raw diff is 2,370 insertions / 5,435 deletions across 55 files, but the actual Ubuntu-specific footprint is much smaller and focused.

### Affected Areas

- `src/wslaragon/core/config.py` — PHP version/ini/extensions defaults; MySQL user default; `windows.hosts_file` → `hosts.hosts_file`.
- `src/wslaragon/core/services.py` — `php-fpm` service name hard-coded to `php8.3-fpm`.
- `src/wslaragon/services/nginx.py` — PHP-FPM socket path is hard-coded; needs detection/fallback for `/run/php/php{version}-fpm.sock` and generic `php-fpm.sock`.
- `src/wslaragon/services/php.py` — `switch_version` enables/starts target FPM unconditionally and updates config; Ubuntu needs safer behavior when target FPM is not installed.
- `src/wslaragon/services/ssl.py` — `add_to_windows_hosts`/`remove_from_windows_hosts` must become `/etc/hosts` operations via `sudo tee`.
- `src/wslaragon/services/sites.py` — site creation/permissions use plain `sudo` and can timeout during long Composer/npm runs; needs sudo refresh helper and ACL-based permission fixes for `www-data`.
- `src/wslaragon/services/site_creators.py` — WordPress/Laravel/phpMyAdmin write `DB_USER = root`; must use configured MySQL user.
- `src/wslaragon/services/mysql.py` — default user fallback is `root`; should be configurable.
- `src/wslaragon/cli/site_commands.py` — add `SudoKeepAlive` during `site create`; keep `--headless` but ensure it works on Ubuntu.
- `src/wslaragon/cli/php_commands.py` — `php upload-limit` couples to `update_client_max_body_size` in nginx; ensure both stay and work on Ubuntu.
- `src/wslaragon/mcp/server.py` — many tools removed in reference branch; keep them but update service name (`php8.5-fpm`) and agent init signature.
- `scripts/install.sh` — must install full Ubuntu stack (PHP 8.5, MariaDB, Nginx, Composer, NVM, pnpm, mkcert, phpMyAdmin) and configure sudoers.
- `scripts/uninstall.sh` — currently missing; needed for clean removal.
- `scripts/vars.sh` — `WINDOWS_HOSTS_FILE` → `HOSTS_FILE`.
- `scripts/setup-env.sh` — WSL detection should become Linux-distro detection.
- `pyproject.toml` / `src/wslaragon/cli/main.py` — description still says "for WSL2".
- `docs/` — add `docs/UBUNTU.md` and update references; do not overwrite Windows/WSL guidance completely.
- `tests/` — fixtures and expectations reference PHP 8.3, `root`, and Windows hosts; must be updated.

### Approaches

1. **Minimal port of Ubuntu fixes onto current main (recommended)**
   - Keep every main feature (headless, Astro, API proxies, upload-limit, MCP tools).
   - Apply only the Ubuntu-specific behavioral changes from `feature/ubuntu-native-support`.
   - Add runtime detection where feasible (hosts file path, PHP-FPM socket discovery).
   - Pros: main remains the source of truth; no feature regression; future merges are simple.
   - Cons: More careful work than a big diff apply; some tests need updating; must verify each adapted feature on Ubuntu.
   - Effort: High

2. **Replay reference branch and re-add main features**
   - Reset main to the reference branch state, then re-implement headless sites, Astro, MCP expansion, etc.
   - Pros: starts from a known-working Ubuntu base.
   - Cons: massive feature regression and re-implementation risk; contradicts the user's intent to keep main updated; huge review surface.
   - Effort: Very High

3. **Compatibility layer (dual WSL + Ubuntu support)**
   - Make hosts file, PHP socket detection, and service names runtime-configurable so one codebase supports both WSL and native Ubuntu.
   - Pros: cleanest long-term; preserves Windows/WSL users.
   - Cons: more design work up front; may be overkill if the project is now Ubuntu-first.
   - Effort: Medium-High

### Recommendation

Choose **Approach 1** with elements of **Approach 3** where cheap: detect the hosts file and PHP-FPM socket at runtime, but otherwise keep the current main architecture. This protects the investment in main's newer features and matches the user's stated goal of updating main, not replacing it.

The work should be delivered as **chained PRs** because the total change will exceed the 400-line review budget.

### Risks

- **Feature regression**: blindly applying the reference-branch diff would delete headless sites, Astro SSG, API proxies, `php upload-limit`, and ~30 MCP tools.
- **PHP 8.5 availability**: Ubuntu's default repos may not ship 8.5 on all LTS versions; install script needs a PPA fallback or version pinning.
- **MariaDB authentication**: switching default user from `root` to `wslaragon` requires creating that user and granting privileges; existing sites may break if their `.env` still uses `root`.
- **Sudo timeout**: long Composer/npm runs during site creation can expire sudo credentials, causing later Nginx/SSL/permission steps to fail.
- **Permissions/ACLs**: `setfacl` may not be installed; fallback to `chmod o+x` is coarser and less secure.
- **Nginx sockets**: `/run/php/php8.5-fpm.sock` may not exist on all systems; socket discovery must be robust.
- **Test churn**: many tests hard-code PHP 8.3 / `root` / Windows paths; updating them is necessary but increases the apparent diff size.
- **Review size**: even a minimal port will likely exceed 400 changed lines, so chained PRs are required per project rules.

### Ready for Proposal

Yes. The next phase should produce a proposal that:
1. Names the change `ubuntu-main-adaptation`.
2. Commits to Approach 1 (minimal port + runtime detection).
3. Defines a chained-PR delivery plan (e.g., slice 1: config/hosts/SSL; slice 2: PHP-FPM/socket; slice 3: permissions/sudo; slice 4: install/uninstall scripts; slice 5: docs + tests).
4. Explicitly states that no main features will be removed.
