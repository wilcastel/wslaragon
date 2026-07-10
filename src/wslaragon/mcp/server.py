"""
WSLaragon MCP Server

Exposes wslaragon capabilities to Claude via the Model Context Protocol.
Run with: wslaragon-mcp  (or: python -m wslaragon.mcp.server)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "wslaragon",
    instructions=(
        "WSLaragon is a Laragon-style dev environment manager for WSL2. "
        "It manages Nginx, PHP-FPM, MariaDB, Redis and local .test domains with SSL. "
        "Sites live in ~/web/ and are accessible at <name>.test (HTTPS). "
        "Use the available tools to create projects, check services, and manage infrastructure."
    ),
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sites_file() -> Path:
    return Path.home() / ".wslaragon" / "sites" / "sites.json"


def _load_sites() -> dict:
    f = _sites_file()
    if f.exists():
        return json.loads(f.read_text())
    return {}


def _run(cmd: list[str]) -> dict:
    """Run a shell command and return {success, stdout, stderr}."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _run_interactive(cmd: list[str], input_text: str) -> dict:
    """Run a shell command feeding it stdin input, for CLI commands that prompt
    for interactive confirmation, and return {success, stdout, stderr}."""
    result = subprocess.run(cmd, input=input_text, capture_output=True, text=True)
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _service_status(service: str) -> str:
    r = subprocess.run(
        ["systemctl", "is-active", service], capture_output=True, text=True
    )
    return r.stdout.strip()


# ---------------------------------------------------------------------------
# Resources  (read-only context)
# ---------------------------------------------------------------------------

@mcp.resource("wslaragon://sites")
def resource_sites() -> str:
    """All sites registered in WSLaragon (name, domain, PHP, SSL, proxy port, etc.)."""
    sites = _load_sites()
    if not sites:
        return "No sites registered yet."
    lines = ["# WSLaragon sites\n"]
    for name, info in sites.items():
        lines.append(f"## {name}")
        lines.append(f"- Domain: {info.get('domain', f'{name}.test')}")
        lines.append(f"- Document root: {info.get('document_root', '')}")
        lines.append(f"- PHP: {'yes' if info.get('php') else 'no'}")
        lines.append(f"- MySQL: {'yes' if info.get('mysql') else 'no'}")
        lines.append(f"- SSL: {'yes' if info.get('ssl') else 'no'}")
        if info.get("proxy_port"):
            lines.append(f"- Proxy port: {info['proxy_port']}")
        if info.get("site_type"):
            lines.append(f"- Type: {info['site_type']}")
        lines.append("")
    return "\n".join(lines)


@mcp.resource("wslaragon://services")
def resource_services() -> str:
    """Current status of Nginx, PHP-FPM, MariaDB and Redis."""
    checks = {
        "nginx":       "nginx",
        "php-fpm":     "php8.3-fpm",
        "mariadb":     "mariadb",
        "redis":       "redis-server",
    }
    lines = ["# Service status\n"]
    for label, svc in checks.items():
        status = _service_status(svc)
        icon = "✓" if status == "active" else "✗"
        lines.append(f"- {icon} {label}: {status}")
    return "\n".join(lines)


@mcp.resource("wslaragon://config")
def resource_config() -> str:
    """WSLaragon configuration (TLD, document root, PHP version, etc.)."""
    config_file = Path.home() / ".wslaragon" / "config.yaml"
    if config_file.exists():
        return config_file.read_text()
    return "Config file not found at ~/.wslaragon/config.yaml"


# ---------------------------------------------------------------------------
# Tools  (actions Claude can execute)
# ---------------------------------------------------------------------------

@mcp.tool()
def list_sites() -> str:
    """List all sites managed by WSLaragon with their configuration."""
    sites = _load_sites()
    if not sites:
        return "No sites registered yet. Use create_site to create one."
    rows = []
    for name, info in sites.items():
        domain = info.get("domain", f"{name}.test")
        tech = f"proxy:{info['proxy_port']}" if info.get("proxy_port") else ("php" if info.get("php") else "static")
        ssl = "ssl" if info.get("ssl") else "no-ssl"
        rows.append(f"- {name} → https://{domain}  [{tech}] [{ssl}]")
    return "\n".join(rows)


@mcp.tool()
def get_services_status() -> str:
    """Check whether Nginx, PHP-FPM, MariaDB and Redis are running."""
    return resource_services()


@mcp.tool()
def create_site(
    name: str,
    site_type: Optional[str] = None,
    mysql: bool = False,
    ssl: bool = True,
    php: bool = True,
    proxy_port: Optional[int] = None,
    laravel_version: Optional[str] = None,
    vite_template: Optional[str] = None,
    db_type: Optional[str] = None,
    public_dir: bool = False,
    astro_template: Optional[str] = None,
) -> str:
    """
    Create a new local site via WSLaragon.

    Parameters
    ----------
    name : str
        Site name (becomes <name>.test). Use lowercase letters, numbers and hyphens only.
    site_type : str, optional
        'html'        – static HTML site
        'wordpress'   – WordPress auto-install
        'node'        – Node.js app (auto-assigns port from 3000)
        'python'      – Python/WSGI app (auto-assigns port from 8000)
        'phpmyadmin'  – phpMyAdmin instance (manages existing MySQL databases,
                        does not create its own database)
        Leave empty for a generic PHP/Laravel site.
    mysql : bool
        Create a MySQL database with the same name as the site.
    ssl : bool
        Generate a local SSL certificate (default: True).
    php : bool
        Enable PHP-FPM (default: True, automatically disabled for node/python/Astro).
    proxy_port : int, optional
        Custom proxy port for node/python apps.
    laravel_version : str, optional
        Laravel version to install (e.g. '12'). Triggers Laravel scaffolding.
    vite_template : str, optional
        Vite template: 'react', 'vue', 'svelte', 'vanilla', etc.
    db_type : str, optional
        'postgres' or 'supabase' to use PostgreSQL instead of MySQL.
    public_dir : bool
        Serve from <site>/public/ (needed for Laravel).
    astro_template : str, optional
        Create an Astro static site (SSG, served from dist/, no PHP/proxy) using this
        template: 'basics', 'blog', or 'minimal'. Leave empty for a non-Astro site.
    """
    cmd = ["wslaragon", "site", "create", name]

    if site_type == "html":
        cmd.append("--html")
    elif site_type == "wordpress":
        cmd.append("--wordpress")
    elif site_type == "node":
        cmd.append("--node")
    elif site_type == "python":
        cmd.append("--python")
    elif site_type == "phpmyadmin":
        cmd.append("--phpmyadmin")

    if laravel_version:
        cmd += [f"--laravel={laravel_version}"]

    if vite_template:
        cmd += ["--vite", vite_template]

    if astro_template:
        cmd.append(f"--astro={astro_template}")

    if mysql:
        cmd.append("--mysql")

    if not ssl:
        cmd.append("--no-ssl")

    if not php and site_type not in ("node", "python"):
        cmd.append("--no-php")

    if proxy_port:
        cmd += ["--proxy", str(proxy_port)]

    if db_type in ("postgres", "supabase"):
        cmd.append(f"--{db_type}")

    if public_dir:
        cmd.append("--public")

    result = _run(cmd)
    if result["success"]:
        sites = _load_sites()
        info = sites.get(name, {})
        domain = info.get("domain", f"{name}.test")
        return (
            f"Site '{name}' created successfully.\n"
            f"URL: https://{domain}\n"
            f"Document root: {info.get('document_root', f'~/web/{name}')}\n"
            f"{result['stdout']}"
        ).strip()
    return f"Failed to create site:\n{result['stderr'] or result['stdout']}"


@mcp.tool()
def start_service(service: str) -> str:
    """
    Start a WSLaragon service.

    Parameters
    ----------
    service : str
        One of: 'nginx', 'php', 'mysql', 'redis', 'all'
    """
    if service == "all":
        results = []
        for svc in ["nginx", "php", "mysql"]:
            r = _run(["wslaragon", "service", "start", svc])
            results.append(f"{svc}: {'started' if r['success'] else 'failed'}")
        return "\n".join(results)
    r = _run(["wslaragon", "service", "start", service])
    return f"{service}: {'started' if r['success'] else 'failed — ' + r['stderr']}"


@mcp.tool()
def stop_service(service: str) -> str:
    """
    Stop a WSLaragon service.

    Parameters
    ----------
    service : str
        One of: 'nginx', 'php', 'mysql', 'redis', 'all'
    """
    if service == "all":
        results = []
        for svc in ["nginx", "php", "mysql"]:
            r = _run(["wslaragon", "service", "stop", svc])
            results.append(f"{svc}: {'stopped' if r['success'] else 'failed'}")
        return "\n".join(results)
    r = _run(["wslaragon", "service", "stop", service])
    return f"{service}: {'stopped' if r['success'] else 'failed — ' + r['stderr']}"


@mcp.tool()
def restart_service(service: str) -> str:
    """
    Restart a WSLaragon service.

    Parameters
    ----------
    service : str
        One of: 'nginx', 'php', 'mysql', 'redis', 'all'
    """
    if service == "all":
        results = []
        for svc in ["nginx", "php", "mysql"]:
            r = _run(["wslaragon", "service", "restart", svc])
            results.append(f"{svc}: {'restarted' if r['success'] else 'failed'}")
        return "\n".join(results)
    r = _run(["wslaragon", "service", "restart", service])
    return f"{service}: {'restarted' if r['success'] else 'failed — ' + r['stderr']}"


@mcp.tool()
def generate_ssl(domain: str) -> str:
    """
    Generate a local SSL certificate for a domain using mkcert.

    Parameters
    ----------
    domain : str
        Domain name, e.g. 'myproject.test'
    """
    r = _run(["wslaragon", "ssl", "generate", domain])
    if r["success"]:
        return f"SSL certificate generated for {domain}."
    return f"SSL generation failed:\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def agent_init(project_path: str, preset: str = "default") -> str:
    """
    Initialize the .agent/skills structure inside an existing project.

    Parameters
    ----------
    project_path : str
        Absolute path to the project directory.
    preset : str
        Skill preset. Options: 'default', 'laravel', 'wordpress', 'javascript', 'python', 'meta'.
    """
    r = _run(["wslaragon", "agent", "init", "--preset", preset, "--path", project_path])
    if r["success"]:
        return f".agent structure initialised in {project_path} with preset '{preset}'."
    return f"agent init failed:\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def run_doctor() -> str:
    """Run WSLaragon's diagnostic tool to detect configuration issues."""
    r = _run(["wslaragon", "doctor"])
    return r["stdout"] or r["stderr"] or "Doctor finished with no output."


# ---------------------------------------------------------------------------
# Tools — site management (delete, headless, enable/disable, api proxies, ...)
# ---------------------------------------------------------------------------

@mcp.tool()
def create_headless_site(
    url: str,
    backend: str,
    frontend: str,
    ssl: bool = True,
    database: Optional[str] = None,
    force: bool = False,
) -> str:
    """
    Create a headless site: a linked frontend + backend/API pair that share one
    project root directory. This is separate from create_site because headless
    sites use a base --url instead of a positional site name.

    Parameters
    ----------
    url : str
        Base site name. Creates a frontend at <url>.test and a backend/API at
        api.<url>.test.
    backend : str
        Backend framework. One of: 'wordpress', 'laravel'.
    frontend : str
        Frontend framework. One of: 'sveltekit', 'astro'.
    ssl : bool
        Generate local SSL certificates for both the frontend and backend domains
        (default: True).
    database : str, optional
        Custom MySQL database name for the backend. Defaults to a name derived
        from the site.
    force : bool
        Overwrite existing files if a site with this name already exists.
    """
    cmd = [
        "wslaragon", "site", "create",
        "--headless",
        f"--backend={backend}",
        f"--frontend={frontend}",
        f"--url={url}",
    ]
    if not ssl:
        cmd.append("--no-ssl")
    if database:
        cmd += ["--database", database]
    if force:
        cmd.append("--force")

    result = _run(cmd)
    if result["success"]:
        return (
            f"Headless site '{url}' created successfully.\n"
            f"Frontend: https://{url}.test\n"
            f"Backend/API: https://api.{url}.test\n"
            f"{result['stdout']}"
        ).strip()
    return f"Failed to create headless site:\n{result['stderr'] or result['stdout']}"


@mcp.tool()
def delete_site(name: str, remove_files: bool = True, remove_database: bool = False) -> str:
    """
    Delete a site's Nginx/PHP-FPM registration and, optionally, its files and
    MySQL database. This CLI command is interactive; this tool answers its
    confirmation prompts automatically based on the parameters below.

    Parameters
    ----------
    name : str
        Site name to delete.
    remove_files : bool
        Also delete the project's files on disk (default: True). If False, only
        the Nginx/PHP registration is removed and the files are kept.
    remove_database : bool
        Also drop the site's MySQL database, if it has one (default: False).

    Notes
    -----
    If this site is one half of a headless frontend/backend pair (they share a
    single project root), deleting it also deletes its paired site.
    """
    cmd = [
        "wslaragon", "site", "delete", name,
        "--remove-database" if remove_database else "--keep-database",
    ]
    confirm_input = f"{'y' if remove_files else 'n'}\ny\n"
    result = _run_interactive(cmd, confirm_input)
    if result["success"]:
        return f"Site '{name}' deleted successfully.\n{result['stdout']}".strip()
    return f"Failed to delete site:\n{result['stderr'] or result['stdout']}"


@mcp.tool()
def enable_site(name: str) -> str:
    """
    Enable a site (re-activates its Nginx configuration).

    Parameters
    ----------
    name : str
        Site name to enable.
    """
    r = _run(["wslaragon", "site", "enable", name])
    if r["success"]:
        return f"Site '{name}' enabled."
    return f"Failed to enable site '{name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def disable_site(name: str) -> str:
    """
    Disable a site (deactivates its Nginx configuration without deleting files).

    Parameters
    ----------
    name : str
        Site name to disable.
    """
    r = _run(["wslaragon", "site", "disable", name])
    if r["success"]:
        return f"Site '{name}' disabled."
    return f"Failed to disable site '{name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def set_site_public(name: str, enable: bool = True) -> str:
    """
    Point a site's web root at its public/ subdirectory, or back at its project
    root. Needed for Laravel/Symfony-style projects.

    Parameters
    ----------
    name : str
        Site name to update.
    enable : bool
        True to serve from <site>/public/ (default). False to serve from the
        project root.
    """
    cmd = ["wslaragon", "site", "public", name, "--enable" if enable else "--disable"]
    r = _run(cmd)
    if r["success"]:
        path = "public/" if enable else "./"
        return f"Site '{name}' web root set to {path}."
    return f"Failed to update site '{name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def fix_site_permissions(name: str) -> str:
    """
    Fix filesystem ownership/permissions for a site's files (owner: current
    user, group: www-data, mode 775). Use after files are created as root or
    with the wrong owner.

    Parameters
    ----------
    name : str
        Site name whose files need permission repair.
    """
    r = _run(["wslaragon", "site", "fix-permissions", name])
    if r["success"]:
        return f"Permissions fixed for site '{name}' (owner: current user, group: www-data, mode 775)."
    return f"Failed to fix permissions for '{name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def export_site(name: str, output: Optional[str] = None) -> str:
    """
    Export a site (files, Nginx config, and MySQL database if any) to a backup
    archive file.

    Parameters
    ----------
    name : str
        Site name to export.
    output : str, optional
        Output directory or filename for the backup archive. Defaults to the
        current directory with an auto-generated filename.
    """
    cmd = ["wslaragon", "site", "export", name]
    if output:
        cmd += ["--output", output]
    r = _run(cmd)
    if r["success"]:
        return f"Site '{name}' exported successfully.\n{r['stdout']}".strip()
    return f"Failed to export site '{name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def import_site(file: str, name: Optional[str] = None) -> str:
    """
    Import a site from a backup archive file previously created with export_site.

    Parameters
    ----------
    file : str
        Path to the backup archive file to import.
    name : str, optional
        New name to give the imported site. Defaults to the name stored in the
        backup archive.
    """
    cmd = ["wslaragon", "site", "import", file]
    if name:
        cmd += ["--name", name]
    r = _run(cmd)
    if r["success"]:
        return f"Site imported successfully from '{file}'.\n{r['stdout']}".strip()
    return f"Failed to import site from '{file}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def enable_site_ssl(name: str) -> str:
    """
    Enable SSL for an already-created site by generating a local certificate and
    wiring it into that site's Nginx configuration. Different from generate_ssl,
    which only creates a raw mkcert certificate for an arbitrary domain without
    touching any site's Nginx config.

    Parameters
    ----------
    name : str
        Name of an existing WSLaragon site to enable SSL for.
    """
    r = _run(["wslaragon", "site", "ssl", name])
    if r["success"]:
        return f"SSL enabled for site '{name}'.\n{r['stdout']}".strip()
    return f"Failed to enable SSL for site '{name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def add_api_proxy(name: str, path: str, backend: str) -> str:
    """
    Add a reverse-proxy rule to a site's Nginx config, forwarding requests under
    a URL path prefix to a backend URL.

    Parameters
    ----------
    name : str
        Site name to add the proxy rule to, e.g. 'dash'.
    path : str
        URL path prefix to proxy, e.g. '/api'.
    backend : str
        Backend URL to forward matching requests to, e.g. 'https://api.dash.test'.
    """
    r = _run(["wslaragon", "site", "api", "add", name, path, backend])
    if r["success"]:
        return f"API proxy added to '{name}': {path} -> {backend}."
    return f"Failed to add API proxy to '{name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def remove_api_proxy(name: str, path: str) -> str:
    """
    Remove a reverse-proxy rule from a site's Nginx config.

    Parameters
    ----------
    name : str
        Site name to remove the proxy rule from, e.g. 'dash'.
    path : str
        URL path prefix to remove, e.g. '/api'.
    """
    r = _run(["wslaragon", "site", "api", "remove", name, path])
    if r["success"]:
        return f"API proxy removed from '{name}': {path}."
    return f"Failed to remove API proxy from '{name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def list_api_proxies(name: str) -> str:
    """
    List all reverse-proxy (API) rules configured for a site.

    Parameters
    ----------
    name : str
        Site name whose API proxies should be listed, e.g. 'dash'.
    """
    r = _run(["wslaragon", "site", "api", "list", name])
    if r["success"]:
        return r["stdout"] or f"No API proxies configured for '{name}'."
    return f"Failed to list API proxies for '{name}':\n{r['stderr'] or r['stdout']}"


# ---------------------------------------------------------------------------
# Tools — PHP management
# ---------------------------------------------------------------------------

@mcp.tool()
def list_php_versions() -> str:
    """List all PHP versions installed and which one is currently active."""
    r = _run(["wslaragon", "php", "versions"])
    return r["stdout"] or r["stderr"] or "No PHP versions found."


@mcp.tool()
def switch_php_version(version: str) -> str:
    """
    Switch the system-wide active PHP-FPM version.

    Parameters
    ----------
    version : str
        PHP version to switch to, e.g. '8.3'. Must already be installed
        (see list_php_versions).
    """
    r = _run(["wslaragon", "php", "switch", version])
    if r["success"]:
        return f"Switched to PHP {version}."
    return f"Failed to switch to PHP {version}:\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def list_php_extensions() -> str:
    """List PHP extensions available for the currently active PHP version."""
    r = _run(["wslaragon", "php", "extensions"])
    return r["stdout"] or r["stderr"] or "No PHP extensions found."


@mcp.tool()
def enable_php_extension(extension: str) -> str:
    """
    Enable a PHP extension for the currently active PHP version.

    Parameters
    ----------
    extension : str
        PHP extension name, e.g. 'gd', 'redis', 'xdebug'.
    """
    r = _run(["wslaragon", "php", "enable-ext", extension])
    if r["success"]:
        return f"PHP extension '{extension}' enabled."
    return f"Failed to enable PHP extension '{extension}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def disable_php_extension(extension: str) -> str:
    """
    Disable a PHP extension for the currently active PHP version.

    Parameters
    ----------
    extension : str
        PHP extension name, e.g. 'gd', 'redis', 'xdebug'.
    """
    r = _run(["wslaragon", "php", "disable-ext", extension])
    if r["success"]:
        return f"PHP extension '{extension}' disabled."
    return f"Failed to disable PHP extension '{extension}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def list_php_config() -> str:
    """List common php.ini settings for the active PHP version (memory_limit,
    upload_max_filesize, post_max_size, max_execution_time, max_input_time,
    display_errors, date.timezone)."""
    r = _run(["wslaragon", "php", "config", "list"])
    return r["stdout"] or r["stderr"] or "No PHP configuration found."


@mcp.tool()
def get_php_config(key: str) -> str:
    """
    Get the value of a single php.ini setting for the active PHP version.

    Parameters
    ----------
    key : str
        php.ini setting name, e.g. 'memory_limit' or 'upload_max_filesize'.
    """
    r = _run(["wslaragon", "php", "config", "get", key])
    return r["stdout"] or r["stderr"] or f"Setting '{key}' not found."


@mcp.tool()
def set_php_config(key: str, value: str) -> str:
    """
    Set a php.ini setting for the active PHP version and restart PHP-FPM.

    Parameters
    ----------
    key : str
        php.ini setting name, e.g. 'memory_limit'.
    value : str
        New value for the setting, e.g. '256M'.
    """
    r = _run(["wslaragon", "php", "config", "set", key, value])
    if r["success"]:
        return f"PHP setting '{key}' updated to '{value}'. PHP-FPM restarted."
    return f"Failed to update PHP setting '{key}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def set_php_upload_limit(size: str = "512M") -> str:
    """
    Set upload size limits across ALL installed PHP versions (both FPM and CLI)
    in one shot, plus Nginx's client_max_body_size.

    Updates upload_max_filesize, post_max_size, memory_limit, max_execution_time
    and max_input_time for every installed PHP version.

    Parameters
    ----------
    size : str
        Size string understood by PHP/Nginx, e.g. '512M', '1G' (default: '512M').
    """
    r = _run(["wslaragon", "php", "upload-limit", size])
    if r["success"]:
        return f"Upload limits set to {size} across all PHP versions and Nginx."
    return f"Failed to set upload limits:\n{r['stderr'] or r['stdout']}"


# ---------------------------------------------------------------------------
# Tools — MySQL management
# ---------------------------------------------------------------------------

@mcp.tool()
def list_mysql_databases() -> str:
    """List all MySQL databases with their sizes."""
    r = _run(["wslaragon", "mysql", "databases"])
    return r["stdout"] or r["stderr"] or "No MySQL databases found."


@mcp.tool()
def create_mysql_database(name: str) -> str:
    """
    Create a new, empty MySQL database.

    Parameters
    ----------
    name : str
        MySQL database name to create.
    """
    r = _run(["wslaragon", "mysql", "create-db", name])
    if r["success"]:
        return f"MySQL database '{name}' created."
    return f"Failed to create MySQL database '{name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def drop_mysql_database(name: str) -> str:
    """
    Permanently drop a MySQL database. This is irreversible. The underlying CLI
    command asks for interactive confirmation; this tool confirms automatically.

    Parameters
    ----------
    name : str
        MySQL database name to drop.
    """
    result = _run_interactive(["wslaragon", "mysql", "drop-db", name], "y\n")
    if result["success"]:
        return f"MySQL database '{name}' dropped."
    return f"Failed to drop MySQL database '{name}':\n{result['stderr'] or result['stdout']}"


# ---------------------------------------------------------------------------
# Tools — Nginx configuration
# ---------------------------------------------------------------------------

@mcp.tool()
def list_nginx_config() -> str:
    """List configurable Nginx settings (currently: client_max_body_size)."""
    r = _run(["wslaragon", "nginx", "config", "list"])
    return r["stdout"] or r["stderr"] or "No Nginx configuration found."


@mcp.tool()
def set_nginx_config(key: str, value: str) -> str:
    """
    Set a global Nginx configuration value and re-apply it to every enabled site.

    Parameters
    ----------
    key : str
        Nginx setting name. Currently only 'client_max_body_size' is supported.
    value : str
        New value, e.g. '128M'.
    """
    r = _run(["wslaragon", "nginx", "config", "set", key, value])
    if r["success"]:
        return f"Nginx setting '{key}' updated to '{value}' for all sites."
    return f"Failed to update Nginx setting '{key}':\n{r['stderr'] or r['stdout']}"


# ---------------------------------------------------------------------------
# Tools — SSL management (generate_ssl already covers `ssl generate`)
# ---------------------------------------------------------------------------

@mcp.tool()
def setup_ssl() -> str:
    """Bootstrap the local root Certificate Authority (mkcert) used to issue
    trusted SSL certificates for .test domains. Run this once per machine
    before generating any certificates."""
    r = _run(["wslaragon", "ssl", "setup"])
    if r["success"]:
        return "SSL root CA created successfully."
    return f"Failed to create SSL root CA:\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def delete_ssl_cert(domain: str) -> str:
    """
    Delete the local SSL certificate for a domain. The underlying CLI command
    asks for interactive confirmation; this tool confirms automatically.

    Parameters
    ----------
    domain : str
        Domain whose certificate should be deleted, e.g. 'myproject.test'.
    """
    result = _run_interactive(["wslaragon", "ssl", "delete", domain], "y\n")
    if result["success"]:
        return f"SSL certificate deleted for {domain}."
    return f"Failed to delete SSL certificate for {domain}:\n{result['stderr'] or result['stdout']}"


@mcp.tool()
def list_ssl_certs() -> str:
    """List all locally issued SSL certificates (domain, subject, issuer, and
    expiry date)."""
    r = _run(["wslaragon", "ssl", "list"])
    return r["stdout"] or r["stderr"] or "No SSL certificates found."


# ---------------------------------------------------------------------------
# Tools — Node.js process management (PM2)
# ---------------------------------------------------------------------------

@mcp.tool()
def list_node_processes() -> str:
    """List Node.js/Python app processes currently managed by PM2, with their
    status, memory usage and uptime."""
    r = _run(["wslaragon", "node", "list"])
    return r["stdout"] or r["stderr"] or "No running Node processes found."


@mcp.tool()
def start_node_process(site_name: str) -> str:
    """
    Start the app process for a node/python site under PM2 (auto-detects
    app.js, main.py, or falls back to `npm start`).

    Parameters
    ----------
    site_name : str
        Name of an existing WSLaragon site configured with a proxy port
        (created with site_type='node' or 'python').
    """
    r = _run(["wslaragon", "node", "start", site_name])
    if r["success"]:
        return f"Process '{site_name}' started."
    return f"Failed to start process '{site_name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def stop_node_process(site_name: str) -> str:
    """
    Stop the PM2-managed app process for a node/python site.

    Parameters
    ----------
    site_name : str
        Name of the site/process to stop.
    """
    r = _run(["wslaragon", "node", "stop", site_name])
    if r["success"]:
        return f"Process '{site_name}' stopped."
    return f"Failed to stop process '{site_name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def restart_node_process(site_name: str) -> str:
    """
    Restart the PM2-managed app process for a node/python site.

    Parameters
    ----------
    site_name : str
        Name of the site/process to restart.
    """
    r = _run(["wslaragon", "node", "restart", site_name])
    if r["success"]:
        return f"Process '{site_name}' restarted."
    return f"Failed to restart process '{site_name}':\n{r['stderr'] or r['stdout']}"


@mcp.tool()
def delete_node_process(site_name: str) -> str:
    """
    Permanently remove a PM2-managed app process for a node/python site
    (stops it and removes it from the PM2 process list).

    Parameters
    ----------
    site_name : str
        Name of the site/process to delete.
    """
    r = _run(["wslaragon", "node", "delete", site_name])
    if r["success"]:
        return f"Process '{site_name}' deleted."
    return f"Failed to delete process '{site_name}':\n{r['stderr'] or r['stdout']}"


# ---------------------------------------------------------------------------
# Tools — Agent skills
# ---------------------------------------------------------------------------

@mcp.tool()
def import_skill(url_or_path: str) -> str:
    """
    Import an .agent skill from a URL or local path into the current project's
    .agent/skills structure.

    Parameters
    ----------
    url_or_path : str
        URL (e.g. a GitHub raw link) or local filesystem path pointing to the
        skill to import.
    """
    r = _run(["wslaragon", "agent", "import", url_or_path])
    if r["success"]:
        return f"Skill imported successfully from '{url_or_path}'.\n{r['stdout']}".strip()
    return f"Failed to import skill from '{url_or_path}':\n{r['stderr'] or r['stdout']}"


# ---------------------------------------------------------------------------
# Prompts  (guided workflows)
# ---------------------------------------------------------------------------

@mcp.prompt()
def new_project(
    name: str,
    stack: str = "laravel",
    with_database: bool = True,
) -> str:
    """
    Guided prompt to scaffold a new local project with WSLaragon.

    Parameters
    ----------
    name : str
        Project name (will become <name>.test).
    stack : str
        Technology stack: 'laravel', 'wordpress', 'react', 'vue', 'node', 'python', 'html'.
    with_database : bool
        Whether the project needs a database.
    """
    return (
        f"I need to set up a new local project called **{name}** using WSLaragon.\n\n"
        f"Stack: **{stack}**\n"
        f"Database needed: {'yes' if with_database else 'no'}\n\n"
        "Please:\n"
        "1. Check that nginx, php-fpm and mariadb are running (use get_services_status).\n"
        "2. Start any stopped services.\n"
        f"3. Create the site using create_site with the right flags for '{stack}'.\n"
        "4. Confirm the URL and document root when done.\n"
        "5. If the stack is Laravel or a JS framework, suggest the next commands to run "
        "   inside the project directory (composer install, npm install, etc.)."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    mcp.run()


if __name__ == "__main__":
    main()
