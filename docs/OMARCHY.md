# Omarchy support

Omarchy support is being delivered in focused phases. The first phase provides
local `.test` domains, trusted HTTPS, Nginx virtual hosts, and static or generic
PHP document roots. Database provisioning and framework scaffolding remain out
of scope until later phases.

## Phase 1 setup

Run the setup from an interactive terminal so `sudo` and `mkcert` can request
confirmation when needed:

```bash
./scripts/setup-omarchy-phase1.sh
```

Then install the CLI in the repository virtual environment and create a site:

```bash
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/wslaragon site create demo --html
```

Open `https://demo.test` in the browser. Site creation adds IPv4 and IPv6 loopback
entries to `/etc/hosts`, writes the Nginx virtual host, generates a local
certificate, validates Nginx, and reloads the service.

Omarchy uses these native paths and services:

- PHP configuration: `/etc/php/php.ini`
- PHP-FPM service: `php-fpm.service`
- PHP-FPM socket: `/run/php-fpm/php-fpm.sock`
- Nginx sites: `/etc/nginx/sites-available` and `/etc/nginx/sites-enabled`
- Local name resolution: `/etc/hosts`

The setup grants the Arch web-server user (`http`) traversal-only access to the
user home directory through an ACL. It also imports the local CA into Firefox
and Zen profiles stored below `~/.config/mozilla`, which `mkcert` does not detect
automatically on every Omarchy installation. Restart an already-open browser
after the initial setup so it reloads its certificate database.

## Phase 2: MariaDB

The database phase supports both container conventions provided by Omarchy:
`mariadb11` and `mysql8`, exposed only on `127.0.0.1:3306`. Install or start
MariaDB with:

```bash
./scripts/setup-omarchy-mariadb.sh
```

Verify the runtime and SQL connection, then manage databases:

```bash
.venv/bin/wslaragon mysql status
.venv/bin/wslaragon mysql create-db example_db
.venv/bin/wslaragon mysql databases
```

Lifecycle commands (`mysql start`, `mysql stop`, and `mysql restart`) control
the detected Docker engine on Omarchy and retain systemd compatibility on
WSL/Ubuntu. The setup also enables PHP's `mysqli` extension for phpMyAdmin.

Create the phpMyAdmin virtual host with:

```bash
.venv/bin/wslaragon site create pma --phpmyadmin
```

It uses the existing database server and is available at `https://pma.test`.
