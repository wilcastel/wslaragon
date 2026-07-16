# WSLaragon on Native Ubuntu

This guide covers installing, using, and uninstalling WSLaragon on a native Ubuntu (or Debian) host.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Site Creation](#site-creation)
- [SSL Certificates](#ssl-certificates)
- [Service Management](#service-management)
- [Database Access](#database-access)
- [Uninstall](#uninstall)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Ubuntu 22.04 LTS or newer (Debian 12+ also works)
- A non-root user with passwordless `sudo` privileges
- Internet access for downloading packages and mkcert

## Installation

Run the installer from the repository:

```bash
bash scripts/install.sh
```

The installer will:

1. Update system packages.
2. Install Nginx, MariaDB, Python, Supervisor, Composer, NVM, Node.js LTS, pnpm, and phpMyAdmin.
3. Install PHP 8.5. If PHP 8.5 is unavailable in the default repositories, the script automatically adds the [Ondrej PHP PPA](https://launchpad.net/~ondrej/+archive/ubuntu/php) and retries.
4. Create the `wslaragon` MariaDB user with full privileges.
5. Install `mkcert` and configure a local certificate authority for SSL.
6. Copy the project to `/opt/wslaragon` and install the `wslaragon` Python package.
7. Enable and start Nginx, MariaDB, PHP-FPM, and the WSLaragon web service.

After installation, reload your shell or run:

```bash
source ~/.bashrc
```

Verify the CLI:

```bash
wslaragon --version
```

## Site Creation

Create a plain PHP site:

```bash
wslaragon site create myproject --php
```

Create a WordPress site:

```bash
wslaragon site create myproject --wordpress --mysql
```

Create a Laravel site:

```bash
wslaragon site create myproject --laravel --mysql
```

The default TLD is `.test`, so the site will be available at `http://myproject.test`.

By default, WSLaragon on native Ubuntu:

- Writes host entries to `/etc/hosts` using `sudo`.
- Creates databases with the configured `wslaragon` MariaDB user.
- Applies POSIX ACLs for `www-data`, falling back to `chmod` if `setfacl` is unavailable.

## SSL Certificates

WSLaragon uses `mkcert` for locally trusted SSL certificates. To enable HTTPS for a site, use the `--ssl` flag:

```bash
wslaragon site create myproject --php --ssl
```

The certificate and key are stored under `~/.wslaragon/ssl/`. Browsers that trust the mkcert CA will accept the certificate without warnings.

If you prefer to manage certificates manually, the `wslaragon ssl` command group provides `setup`, `renew`, and `remove` subcommands.

## Service Management

Start services:

```bash
wslaragon service start nginx
wslaragon service start mysql
wslaragon service start php
```

Switch PHP versions (requires the target FPM package to be installed):

```bash
wslaragon php switch 8.5
```

View service status:

```bash
wslaragon service status
```

## Database Access

The installer creates a dedicated MariaDB user:

- Username: `wslaragon`
- Password: `wslaragon`
- Host: `localhost`

Connect from the terminal:

```bash
mariadb -u wslaragon -p
```

Or use phpMyAdmin at `http://localhost/phpmyadmin` if your web server is configured to serve it.

Site creators read `mysql.user` and `mysql.password` from `~/.wslaragon/config.yaml`, so WordPress and Laravel `.env` files use this account automatically.

## Uninstall

To remove WSLaragon packages while keeping your sites and databases:

```bash
bash scripts/uninstall.sh
```

To remove everything, including site directories, configuration, and the `wslaragon` database user:

```bash
bash scripts/uninstall.sh --purge
```

The `--purge` flag requires you to type `yes` before any data is deleted.

## Testing

Run the unit suite with the project-wide coverage gate:

```bash
pytest tests/unit/ -q --tb=short
```

Run the integration suite with `--no-cov` so the unit-test `--cov-fail-under=90` threshold is not applied:

```bash
pytest tests/integration/ -v --run-slow --tb=short --no-cov
```

> Do not remove `--cov-fail-under=90` from `pyproject.toml`; that threshold is required for the unit suite.

Lint installer shell scripts:

```bash
shellcheck -x --severity=warning scripts/*.sh
```

## Troubleshooting

### PHP 8.5 installation fails

The installer adds the Ondrej PPA automatically when PHP 8.5 is not found in the default repositories. If it still fails, ensure `software-properties-common` is installed and your system can reach `launchpad.net`.

### `wslaragon` command not found

Reload your shell:

```bash
source ~/.bashrc
```

Or check that `/opt/wslaragon/venv/bin` is in your `PATH`.

### Sites return 502 Bad Gateway

Verify that PHP-FPM is running for the configured version:

```bash
sudo systemctl status "php${PHP_VERSION}-fpm"
```

### Cannot edit `/etc/hosts`

Native Ubuntu uses `sudo tee` to update `/etc/hosts`. Ensure your user has passwordless `sudo` for the commands listed in `/etc/sudoers.d/wslaragon`.

### sudo timeout during long site creation

WSLaragon keeps `sudo` credentials alive during site creation. If you are still prompted, run `sudo -v` before creating a site.
