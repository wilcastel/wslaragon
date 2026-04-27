"""
Site management commands for WSLaragon CLI.
"""
import click
import subprocess
import logging
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..core.config import Config
from ..core.services import ServiceManager
from ..services.php import PHPManager
from ..services.nginx import NginxManager
from ..services.mysql import MySQLManager
from ..services.sites import SiteManager
from ..services.ssl import SSLManager
from ..services.backup import BackupManager

logger = logging.getLogger(__name__)
console = Console()


@click.group()
def site():
    """Site management commands"""
    pass


@site.command()
@click.argument('name')
@click.option('--php/--no-php', default=True, help='Enable PHP')
@click.option('--mysql/--no-mysql', default=None, help='Create MySQL database (default: True for WordPress)')
@click.option('--ssl/--no-ssl', default=True, help='Enable SSL (default: True)')
@click.option('--database', help='Custom database name')
@click.option('--public/--no-public', default=False, help='Point document root to public/ directory')
@click.option('--proxy', type=int, help='Proxy port (e.g. 8000) for Python/Node apps')
@click.option('--html', 'site_type', flag_value='html', help='Create static HTML site')
@click.option('--wordpress', 'site_type', flag_value='wordpress', help='Create WordPress site')
@click.option('--phpmyadmin', 'site_type', flag_value='phpmyadmin', help='Create phpMyAdmin site')
@click.option('--laravel', 'site_type', help='Create Laravel site (specify version, e.g., --laravel=12)')
@click.option('--node', 'site_type', flag_value='node', help='Create Node.js app (auto-port starting 3000)')
@click.option('--python', 'site_type', flag_value='python', help='Create Python app (auto-port starting 8000)')
@click.option('--vite', help='Create Vite app with template (react, vue, svelte, vanilla, etc.)')
@click.option('--astro', help='Create Astro app with template (basics, blog, minimal, etc.)')
@click.option('--postgres', 'db_type', flag_value='postgres', help='Use PostgreSQL instead of MySQL')
@click.option('--supabase', 'db_type', flag_value='supabase', help='Use Supabase (PostgreSQL + Supabase config)')
@click.option('--force', 'recreate', is_flag=True, default=False, help='Force recreate site (overwrite existing files)')
def create(name, php, mysql, ssl, database, public, proxy, site_type, vite, astro, db_type, recreate):
    """Create a new site"""
    # Override defaults for Node/Python/Vite/Astro if not explicitly set
    
    if site_type in ('node', 'python') or vite or astro:
        # If user didn't explicitly ask for PHP, disable it
        if php: # php is True by default
            php = False
            
        # If vite is selected, enforce node type implicitly
        if vite and not site_type:
            site_type = 'node'
        
        # If astro is selected, enforce node type implicitly
        if astro and not site_type:
            site_type = 'node'
    
    # phpMyAdmin doesn't need its own database (it manages existing ones)
    if site_type == 'phpmyadmin' and mysql is None:
        mysql = False
             
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    
    # Ensure sudo permissions before showing spinner
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return

    with console.status(f"[bold green]Creating site {name}..."):
        result = site_mgr.create_site(name, php=php, mysql=mysql, ssl=ssl, 
                                    database_name=database, public_dir=public,
                                    proxy_port=proxy, site_type=site_type, db_type=db_type,
                                    recreate=recreate, vite_template=vite,
                                    astro_template=astro)
    
    if result['success']:
        site_info = result['site']
        console.print(Panel(f"[bold green]Site created successfully![/bold green]\n\n"
                           f"Domain: {site_info['domain']}\n"
                           f"Document Root: {site_info['document_root']}\n"
                           f"PHP: {'Yes' if site_info['php'] else 'No'}\n"
                           f"Proxy: {site_info.get('proxy_port') if site_info.get('proxy_port') else 'No'}\n"
                           f"MySQL: {'Yes' if site_info['mysql'] else 'No'}\n"
                           f"SSL: {'Yes' if site_info['ssl'] else 'No'}",
                           title=f"Site: {name}"))
        
        if ssl:
             console.print(f"[green]✓ SSL configured for {site_info['domain']}[/green]")
    else:
        console.print(f"[red]✗ Failed to create site: {result['error']}[/red]")


@site.command()
def list():
    """List all sites"""
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    sites = site_mgr.list_sites()
    
    if not sites:
        console.print("[yellow]No sites found[/yellow]")
        return
    
    table = Table(title="Sites")
    table.add_column("Name", style="cyan")
    table.add_column("Domain", style="magenta")
    table.add_column("PHP", style="green")
    table.add_column("MySQL", style="blue")
    table.add_column("SSL", style="yellow")
    table.add_column("Status", style="red")
    
    for site in sites:
        status = "✓ Enabled" if site['enabled'] else "✗ Disabled"
        # Determine PHP/Proxy status
        if site.get('proxy_port'):
            tech_status = f"[blue]Proxy:{site['proxy_port']}[/blue]"
        else:
            tech_status = "✓" if site['php'] else "✗"

        table.add_row(
            site['name'],
            site['domain'],
            tech_status,
            "✓" if site['mysql'] else "✗",
            "✓" if site['ssl'] else "✗",
            status
        )
    
    console.print(table)


@site.command()
@click.argument('name')
@click.option('--remove-database/--keep-database', default=False, help='Remove database')
def delete(name, remove_database):
    """Delete a site"""
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    # Validate sudo permissions
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return
     
    site_info = site_mgr.get_site(name)
    if not site_info:
        console.print(f"[red]✗ Site '{name}' not found[/red]")
        return
    
    doc_root = site_info.get('document_root', '')
    db_name = site_info.get('database', '')
    
    # Ask about removing files
    remove_files = click.confirm(
        f"[bold]Delete the project files at {doc_root}?[/bold]", 
        default=True
    )
    
    if not click.confirm(f"Are you sure you want to delete site '{name}'?"):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    with console.status(f"[bold red]Deleting site {name}..."):
        result = site_mgr.delete_site(name, remove_files, remove_database)
    
    if result['success']:
        console.print(f"[green]✓ Site '{name}' deleted successfully[/green]")
        if remove_files:
            console.print(f"[dim]Files removed: {doc_root}[/dim]")
        else:
            console.print(f"[yellow]Files kept at: {doc_root}[/yellow]")
        if remove_database and db_name:
            console.print(f"[dim]Database removed: {db_name}[/dim]")
    else:
        console.print(f"[red]✗ Failed to delete site: {result['error']}[/red]")


@site.command()
@click.argument('name')
def enable(name):
    """Enable a site"""
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    with console.status(f"[bold green]Enabling site {name}..."):
        result = site_mgr.enable_site(name)
    
    if result['success']:
        console.print(f"[green]✓ Site '{name}' enabled[/green]")
    else:
        console.print(f"[red]✗ Failed to enable site: {result['error']}[/red]")


@site.command('public')
@click.argument('name')
@click.option('--enable/--disable', default=True, help='Enable/Disable public directory serving')
def set_public(name, enable):
    """Set site root to public/ directory (Laravel/Symfony)"""
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    # Ensure sudo permissions
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return

    action = "Enabling" if enable else "Disabling"
    with console.status(f"[bold green]{action} public directory for {name}..."):
        result = site_mgr.update_site_root(name, public_dir=enable)
    
    if result['success']:
        console.print(f"[green]✓ Site rules updated for {name}[/green]")
        path = "public/" if enable else "./"
        console.print(f"[dim]Web root now points to: {path}[/dim]")
    else:
        console.print(f"[red]✗ Failed to update site: {result['error']}[/red]")


@site.command()
@click.argument('name')
def disable(name):
    """Disable a site"""
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    with console.status(f"[bold yellow]Disabling site {name}..."):
        result = site_mgr.disable_site(name)
    
    if result['success']:
        console.print(f"[yellow]✓ Site '{name}' disabled[/yellow]")
    else:
        console.print(f"[red]✗ Failed to disable site: {result['error']}[/red]")


@site.command('fix-permissions')
@click.argument('name')
def fix_permissions(name):
    """Fix file permissions for a site"""
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    # Validate sudo permissions
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return

    with console.status(f"[bold green]Fixing permissions for {name}..."):
        result = site_mgr.fix_permissions(name)
    
    if result['success']:
        console.print(f"[green]✓ Permissions fixed for '{name}'[/green]")
        console.print(f"[dim]Owner set to current user, Group set to www-data (775)[/dim]")
    else:
        console.print(f"[red]✗ Failed to fix permissions: {result['error']}[/red]")


@site.command('export')
@click.argument('name')
@click.option('--output', help='Output directory or filename')
def export_site(name, output):
    """Export a site to a backup file"""
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    backup_mgr = BackupManager(config, site_mgr, mysql_mgr, nginx)
    
    # Ensure sudo
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return
        
    with console.status(f"[bold green]Backing up {name}..."):
        result = backup_mgr.export_site(name, output)
        
    if result['success']:
        console.print(f"[green]✓ Site exported successfully[/green]")
        console.print(f"[dim]File: {result['file']}[/dim]")
    else:
         console.print(f"[red]✗ Failed to export site: {result['error']}[/red]")


@site.command('import')
@click.argument('file')
@click.option('--name', help='New name for the imported site')
def import_site_cmd(file, name):
    """Import a site from a backup file"""
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    backup_mgr = BackupManager(config, site_mgr, mysql_mgr, nginx)
    
    # Ensure sudo
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return
    
    with console.status(f"[bold green]Importing {file}..."):
        result = backup_mgr.import_site(file, name)
        
    if result['success']:
        console.print(f"[green]✓ Site imported successfully as '{result['site']}'[/green]")
        site = result['info']
        console.print(Panel(f"Domain: {site['domain']}\n"
                           f"Location: {site['document_root']}",
                           title="Import Success"))
    else:
         console.print(f"[red]✗ Failed to import site: {result['error']}[/red]")


@site.command('ssl')
@click.argument('name')
def site_ssl(name):
    """Enable SSL for an existing site"""
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    site_info = site_mgr.get_site(name)
    if not site_info:
        console.print(f"[red]✗ Site '{name}' not found[/red]")
        return
    
    if site_info.get('ssl'):
        console.print(f"[yellow]✓ Site '{name}' already has SSL enabled[/yellow]")
        return
    
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return

    with console.status(f"[bold green]Enabling SSL for {name}..."):
        ssl_mgr = SSLManager(config)
        ssl_result = ssl_mgr.setup_ssl_for_site(name, site_mgr.tld)
        
        if not ssl_result['success']:
            console.print(f"[red]✗ Failed to generate SSL: {ssl_result['error']}[/red]")
            return
        
        web_root = site_info['web_root']
        nginx_result = nginx.add_site(
            name, 
            web_root, 
            ssl=True, 
            php=site_info.get('php', True),
            proxy_port=site_info.get('proxy_port')
        )
        
        if not nginx_result[0]:
            console.print(f"[red]✗ Failed to update Nginx: {nginx_result[1]}[/red]")
            return
        
        site_mgr.update_site(name, ssl=True)
    
    console.print(Panel(f"[bold green]SSL enabled successfully![/bold green]\n\n"
                       f"Domain: https://{name}{site_mgr.tld}\n"
                       f"URL: https://{name}.test",
                       title=f"Site: {name}"))


# --- API Proxy sub-group ---

@site.group('api')
def api():
    """Manage API proxies for a site"""
    pass


@api.command('add')
@click.argument('name')
@click.argument('path')
@click.argument('backend')
def api_add(name, path, backend):
    """Add an API proxy to a site
    
    NAME: Site name (e.g. dash)
    PATH: URL path prefix (e.g. /api)
    BACKEND: Backend URL (e.g. https://api.dash.test)
    
    Example: wslaragon site api add dash /api https://api.dash.test
    """
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    # Validate sudo permissions
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return
    
    result = site_mgr.add_api_proxy(name, path, backend)
    
    if result['success']:
        console.print(f"[green]✓ API proxy added: {result['path']} -> {result['backend']}[/green]")
        console.print(f"[dim]Nginx config regenerated and reloaded[/dim]")
    else:
        console.print(f"[red]✗ Failed to add API proxy: {result['error']}[/red]")


@api.command('remove')
@click.argument('name')
@click.argument('path')
def api_remove(name, path):
    """Remove an API proxy from a site
    
    NAME: Site name (e.g. dash)
    PATH: URL path prefix to remove (e.g. /api)
    
    Example: wslaragon site api remove dash /api
    """
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    # Validate sudo permissions
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return
    
    result = site_mgr.remove_api_proxy(name, path)
    
    if result['success']:
        console.print(f"[green]✓ API proxy removed: {result['removed_path']} (was -> {result['removed_backend']})[/green]")
        console.print(f"[dim]Nginx config regenerated and reloaded[/dim]")
    else:
        console.print(f"[red]✗ Failed to remove API proxy: {result['error']}[/red]")


@api.command('list')
@click.argument('name')
def api_list(name):
    """List all API proxies for a site
    
    NAME: Site name (e.g. dash)
    """
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    result = site_mgr.list_api_proxies(name)
    
    if not result['success']:
        console.print(f"[red]✗ {result['error']}[/red]")
        return
    
    proxies = result['proxies']
    if not proxies:
        console.print(f"[yellow]No API proxies configured for '{name}'[/yellow]")
        return
    
    table = Table(title=f"API Proxies: {name}")
    table.add_column("Path", style="cyan")
    table.add_column("Backend", style="green")
    
    for proxy_path, backend in proxies.items():
        table.add_row(proxy_path, backend)
    
    console.print(table)