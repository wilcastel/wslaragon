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
) -> str:
    """
    Create a new local site via WSLaragon.

    Parameters
    ----------
    name : str
        Site name (becomes <name>.test). Use lowercase letters, numbers and hyphens only.
    site_type : str, optional
        'html'      – static HTML site
        'wordpress' – WordPress auto-install
        'node'      – Node.js app (auto-assigns port from 3000)
        'python'    – Python/WSGI app (auto-assigns port from 8000)
        Leave empty for a generic PHP/Laravel site.
    mysql : bool
        Create a MySQL database with the same name as the site.
    ssl : bool
        Generate a local SSL certificate (default: True).
    php : bool
        Enable PHP-FPM (default: True, automatically disabled for node/python).
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

    if laravel_version:
        cmd += [f"--laravel={laravel_version}"]

    if vite_template:
        cmd += ["--vite", vite_template]

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
    r = _run(["wslaragon", "agent", "init", preset, "--path", project_path])
    if r["success"]:
        return f".agent structure initialised in {project_path} with preset '{preset}'."
    # Fallback: some versions don't have --path, run from cwd
    result = subprocess.run(
        ["wslaragon", "agent", "init", preset],
        capture_output=True, text=True, cwd=project_path
    )
    if result.returncode == 0:
        return f".agent structure initialised in {project_path} with preset '{preset}'."
    return f"agent init failed:\n{result.stderr or result.stdout}"


@mcp.tool()
def run_doctor() -> str:
    """Run WSLaragon's diagnostic tool to detect configuration issues."""
    r = _run(["wslaragon", "doctor"])
    return r["stdout"] or r["stderr"] or "Doctor finished with no output."


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
