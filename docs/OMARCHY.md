# Omarchy support

Omarchy support is being delivered in focused phases. The first phase provides
local `.test` domains, trusted HTTPS, Nginx virtual hosts, and static or generic
PHP document roots. Database provisioning and framework scaffolding remain out
of scope until later phases.

## Global command

Expose the editable virtual-environment installation through the user-local
binary directory:

```bash
./scripts/install-omarchy-cli.sh
```

Afterward, use `wslaragon` directly instead of `.venv/bin/wslaragon`. The
launcher remains linked to this repository, so code changes in the editable
installation are immediately available.

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

## Phase 3: WordPress

Install the maintained Arch WordPress distribution once:

```bash
./scripts/setup-omarchy-wordpress.sh
```

Create an isolated WordPress project with its database, Nginx virtual host,
local DNS entry, and HTTPS certificate:

```bash
.venv/bin/wslaragon site create myblog --wordpress
```

Open `https://myblog.test` to complete WordPress's browser-based installation.
On Omarchy, each project receives a copy of `/usr/share/webapps/wordpress` and
uses the Docker database through `127.0.0.1:3306`. Generated `wp-config.php`
files include unique authentication salts and force HTTPS for the admin area.

## Phase 4: Laravel

Install Composer and verify the PHP and database prerequisites:

```bash
./scripts/setup-omarchy-laravel.sh
```

Create a Laravel project (version 12 by default) with its MySQL database,
Nginx `public/` document root, local domain, and HTTPS certificate:

```bash
.venv/bin/wslaragon site create myapp --laravel=12
```

Open `https://myapp.test`. The generated `.env` uses the configured Omarchygon
MySQL host, port, username, and password. To suppress database creation, pass
`--no-mysql` explicitly.

## Phase 5: Node.js and PM2

Install the native Arch Node.js runtime, pnpm, and PM2 process manager:

```bash
./scripts/setup-omarchy-node.sh
```

Create a basic Node.js application with an automatically allocated port,
Nginx reverse proxy, local domain, and HTTPS certificate, then start it:

```bash
.venv/bin/wslaragon site create node-demo --node
.venv/bin/wslaragon node start node-demo
```

Open `https://node-demo.test`. Process lifecycle is managed with `node list`,
`node stop`, `node restart`, and `node delete`.

## Phase 6: Vite

Create a Vite project using pnpm and any supported template, then start its
development server through PM2:

```bash
.venv/bin/wslaragon site create vite-demo --vite react
.venv/bin/wslaragon node start vite-demo
```

Open `https://vite-demo.test`. Nginx proxies HTTP and secure WebSocket traffic
to Vite, so hot module replacement works through the local HTTPS domain. The
generated scripts bind to the allocated port with `--strictPort`, and Vite only
accepts the generated `.test` hostname.

## Phase 7: SvelteKit and Astro

Svelte projects that only need a browser frontend can use the Vite template.
Full SvelteKit applications receive a proxy port and run through PM2:

```bash
wslaragon site create svelte-demo --vite svelte
wslaragon node start svelte-demo

wslaragon site create kit-demo --sveltekit
wslaragon node start kit-demo
```

Astro sites are built as static output and served directly from `dist/`, so no
PM2 process is required:

```bash
wslaragon site create astro-demo --astro
```

Open `https://svelte-demo.test`, `https://kit-demo.test`, or
`https://astro-demo.test` respectively.
