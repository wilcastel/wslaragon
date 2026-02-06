import click
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from ..core.config import Config
from ..core.services import ServiceManager
from ..services.php import PHPManager
from ..services.nginx import NginxManager
from ..services.mysql import MySQLManager
from ..services.sites import SiteManager
from ..services.ssl import SSLManager

console = Console()

@click.group()
@click.version_option()
def cli():
    """WSLaragon - Laragon-style development environment manager for WSL2"""
    pass

@cli.group()
def site():
    """Site management commands"""
    pass

@site.command()
@click.argument('name')
@click.option('--php/--no-php', default=True, help='Enable PHP')
@click.option('--mysql/--no-mysql', default=False, help='Create MySQL database')
@click.option('--ssl/--no-ssl', default=False, help='Enable SSL')
@click.option('--database', help='Custom database name')
@click.option('--public/--no-public', default=False, help='Point document root to public/ directory')
@click.option('--proxy', type=int, help='Proxy port (e.g. 8000) for Python/Node apps')
@click.option('--html', 'site_type', flag_value='html', help='Create static HTML site')
@click.option('--wordpress', 'site_type', flag_value='wordpress', help='Create WordPress site')
@click.option('--laravel', 'site_type', help='Create Laravel site (specify version, e.g., --laravel=12)')
@click.option('--postgres', 'db_type', flag_value='postgres', help='Use PostgreSQL instead of MySQL')
@click.option('--supabase', 'db_type', flag_value='supabase', help='Use Supabase (PostgreSQL + Supabase config)')
@click.option('--force', 'recreate', is_flag=True, default=False, help='Force recreate site (overwrite existing files)')
def create(name, php, mysql, ssl, database, public, proxy, site_type, db_type, recreate):
    """Create a new site"""
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
                                    recreate=recreate)
    
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
@click.option('--remove-files/--keep-files', default=False, help='Remove document root')
@click.option('--remove-database/--keep-database', default=False, help='Remove database')
def delete(name, remove_files, remove_database):
    """Delete a site"""
    config = Config()
    nginx = NginxManager(config)
    mysql_mgr = MySQLManager(config)
    site_mgr = SiteManager(config, nginx, mysql_mgr)
    
    if not site_mgr.get_site(name):
        console.print(f"[red]✗ Site '{name}' not found[/red]")
        return
    
    if click.confirm(f"Are you sure you want to delete site '{name}'?"):
        with console.status(f"[bold red]Deleting site {name}..."):
            result = site_mgr.delete_site(name, remove_files, remove_database)
        
        if result['success']:
            console.print(f"[green]✓ Site '{name}' deleted successfully[/green]")
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

@cli.group()
def service():
    """Service management commands"""
    pass

@service.command()
def status():
    """Show service status"""
    service_mgr = ServiceManager()
    services = service_mgr.status()
    
    table = Table(title="Service Status")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Port", style="blue")
    
    for name, info in services.items():
        status_text = "✓ Running" if info['running'] else "✗ Stopped"
        status_style = "green" if info['running'] else "red"
        table.add_row(name, f"[{status_style}]{status_text}[/{status_style}]", str(info['port']))
    
    console.print(table)

@service.command()
@click.argument('service_name')
def start(service_name):
    """Start a service"""
    service_mgr = ServiceManager()
    
    with console.status(f"[bold green]Starting {service_name}..."):
        result = service_mgr.start(service_name)
    
    if result:
        console.print(f"[green]✓ {service_name} started[/green]")
    else:
        console.print(f"[red]✗ Failed to start {service_name}[/red]")

@service.command()
@click.argument('service_name')
def stop(service_name):
    """Stop a service"""
    service_mgr = ServiceManager()
    
    with console.status(f"[bold red]Stopping {service_name}..."):
        result = service_mgr.stop(service_name)
    
    if result:
        console.print(f"[red]✓ {service_name} stopped[/red]")
    else:
        console.print(f"[red]✗ Failed to stop {service_name}[/red]")

@service.command()
@click.argument('service_name')
def restart(service_name):
    """Restart a service"""
    service_mgr = ServiceManager()
    
    with console.status(f"[bold yellow]Restarting {service_name}..."):
        result = service_mgr.restart(service_name)
    
    if result:
        console.print(f"[yellow]✓ {service_name} restarted[/yellow]")
    else:
        console.print(f"[red]✗ Failed to restart {service_name}[/red]")

@cli.group()
def php():
    """PHP management commands"""
    pass

@php.command()
def versions():
    """List installed PHP versions"""
    config = Config()
    php_mgr = PHPManager(config)
    
    installed = php_mgr.get_installed_versions()
    current = php_mgr.get_current_version()
    
    table = Table(title="PHP Versions")
    table.add_column("Version", style="cyan")
    table.add_column("Status", style="green")
    
    for version in installed:
        status = "✓ Current" if current and version in current else "Available"
        table.add_row(version, status)
    
    console.print(table)

@php.command()
@click.argument('version')
def switch(version):
    """Switch PHP version"""
    config = Config()
    php_mgr = PHPManager(config)
    
    with console.status(f"[bold green]Switching to PHP {version}..."):
        result = php_mgr.switch_version(version)
    
    if result:
        console.print(f"[green]✓ Switched to PHP {version}[/green]")
    else:
        console.print(f"[red]✗ Failed to switch to PHP {version}[/red]")

@php.command()
def extensions():
    """List PHP extensions"""
    config = Config()
    php_mgr = PHPManager(config)
    
    extensions = php_mgr.get_extensions()
    
    table = Table(title="PHP Extensions")
    table.add_column("Extension", style="cyan")
    
    for ext in extensions:
        table.add_row(ext)
    
    console.print(table)

@php.command()
@click.argument('extension')
def enable_ext(extension):
    """Enable a PHP extension"""
    config = Config()
    php_mgr = PHPManager(config)
    
    with console.status(f"[bold green]Enabling {extension}..."):
        result = php_mgr.enable_extension(extension)
    
    if result:
        console.print(f"[green]✓ Extension {extension} enabled[/green]")
    else:
        console.print(f"[red]✗ Failed to enable extension {extension}[/red]")

@php.command()
@click.argument('extension')
def disable_ext(extension):
    """Disable a PHP extension"""
    config = Config()
    php_mgr = PHPManager(config)
    
    with console.status(f"[bold red]Disabling {extension}..."):
        result = php_mgr.disable_extension(extension)
    
    if result:
        console.print(f"[red]✓ Extension {extension} disabled[/red]")
    else:
        console.print(f"[red]✗ Failed to disable extension {extension}[/red]")

@php.group()
def config():
    """Manage PHP configuration"""
    pass

@config.command('list')
def list_config():
    """List common PHP configuration settings"""
    config = Config()
    php_mgr = PHPManager(config)
    
    # Common settings to display
    common_keys = [
        'memory_limit', 
        'upload_max_filesize', 
        'post_max_size', 
        'max_execution_time',
        'max_input_time',
        'display_errors',
        'date.timezone'
    ]
    
    current_config = php_mgr.read_ini()
    
    table = Table(title="PHP Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    for key in common_keys:
        value = current_config.get(key, 'Not set')
        table.add_row(key, value)
    
    console.print(table)

@config.command('set')
@click.argument('key')
@click.argument('value')
def set_config(key, value):
    """Set a PHP configuration value"""
    config = Config()
    php_mgr = PHPManager(config)
    
    # Validate sudo permissions
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return

    with console.status(f"[bold green]Updating {key} to {value}..."):
        result = php_mgr.update_config(key, value)
    
    if result:
        console.print(f"[green]✓ Updated {key} to {value}[/green]")
        console.print("[dim]PHP-FPM restarted[/dim]")
    else:
        console.print(f"[red]✗ Failed to update configuration[/red]")

@config.command('get')
@click.argument('key')
def get_config(key):
    """Get a PHP configuration value"""
    config = Config()
    php_mgr = PHPManager(config)
    
    current_config = php_mgr.read_ini()
    value = current_config.get(key, 'Not set')
    
    console.print(f"[cyan]{key}[/cyan] = [green]{value}[/green]")

@cli.group()
def mysql():
    """MySQL management commands"""
    pass

@mysql.command()
def databases():
    """List MySQL databases"""
    config = Config()
    mysql_mgr = MySQLManager(config)
    
    databases = mysql_mgr.list_databases()
    
    table = Table(title="MySQL Databases")
    table.add_column("Database", style="cyan")
    table.add_column("Size", style="green")
    
    for db in databases:
        size = mysql_mgr.get_database_size(db)
        table.add_row(db, size or "Unknown")
    
    console.print(table)

@mysql.command()
@click.argument('name')
def create_db(name):
    """Create a MySQL database"""
    config = Config()
    mysql_mgr = MySQLManager(config)
    
    with console.status(f"[bold green]Creating database {name}..."):
        result = mysql_mgr.create_database(name)
    
    if result:
        console.print(f"[green]✓ Database '{name}' created[/green]")
    else:
        console.print(f"[red]✗ Failed to create database '{name}'[/red]")

@mysql.command()
@click.argument('name')
def drop_db(name):
    """Drop a MySQL database"""
    config = Config()
    mysql_mgr = MySQLManager(config)
    
    if click.confirm(f"Are you sure you want to drop database '{name}'?"):
        with console.status(f"[bold red]Dropping database {name}..."):
            result = mysql_mgr.drop_database(name)
        
        if result:
            console.print(f"[red]✓ Database '{name}' dropped[/red]")
        else:
            console.print(f"[red]✗ Failed to drop database '{name}'[/red]")

@cli.group()
def ssl():
    """SSL management commands"""
    pass

@ssl.command()
def setup():
    """Setup SSL certificates"""
    config = Config()
    ssl_mgr = SSLManager(config)
    
    with console.status("[bold green]Setting up SSL..."):
        result = ssl_mgr.create_ca()
    
    if result:
        console.print("[green]✓ SSL CA created successfully[/green]")
    else:
        console.print("[red]✗ Failed to create SSL CA[/red]")

@ssl.command()
@click.argument('domain')
def generate(domain):
    """Generate SSL certificate for domain"""
    config = Config()
    ssl_mgr = SSLManager(config)
    
    with console.status(f"[bold green]Generating certificate for {domain}..."):
        result = ssl_mgr.generate_certificate(domain)
    
    if result:
        console.print(f"[green]✓ Certificate generated for {domain}[/green]")
    else:
        console.print(f"[red]✗ Failed to generate certificate for {domain}[/red]")

@cli.group()
def nginx():
    """Nginx management commands"""
    pass

@nginx.group()
def config():
    """Manage Nginx configuration"""
    pass

@config.command('list')
def list_nginx_config():
    """List configurable Nginx settings"""
    config = Config()
    
    # Settings exposed for configuration
    exposed_settings = [
        'client_max_body_size'
    ]
    
    table = Table(title="Nginx Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    for key in exposed_settings:
        value = config.get(f'nginx.{key}', '128M') # Default backup
        table.add_row(key, value)
    
    console.print(table)

@config.command('set')
@click.argument('key')
@click.argument('value')
def set_nginx_config(key, value):
    """Set an Nginx configuration value"""
    config = Config()
    nginx_mgr = NginxManager(config)
    
    # Validate sudo permissions
    try:
        subprocess.run(['sudo', '-v'], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]✗ This command requires sudo privileges[/red]")
        return
    
    valid_keys = ['client_max_body_size']
    if key not in valid_keys:
        console.print(f"[red]✗ Invalid setting '{key}'. Valid settings: {', '.join(valid_keys)}[/red]")
        return

    with console.status(f"[bold green]Updating {key} to {value}..."):
        # Update config
        config.set(f'nginx.{key}', value)
        
        # Reload Nginx to apply might not be enough if template needs regen
        # Ideally we should offer to regen all sites, but for now just saving the config
        # is the first step. The user needs to recreate/update sites for this to apply 
        # unless we force immediate regeneration.
        # However, for global settings, usually we might want to update global nginx.conf 
        # but here we are using per-site config injections.
        
        # For this specific implementation where we inject into site configs:
        # We need to iterate all enabled sites and re-apply config.
        # This is expensive but necessary for "consistency" as requested.
        
        site_mgr = SiteManager(config, nginx_mgr, MySQLManager(config))
        sites = site_mgr.list_sites()
        
        for site in sites:
            # Re-generate config for each site
            site_mgr.update_site(site['name'])
            
    console.print(f"[green]✓ Updated {key} to {value}[/green]")
    console.print("[dim]Access rules updated for all sites. Nginx reloaded.[/dim]")

@ssl.command()
def list():
    """List SSL certificates"""
    config = Config()
    ssl_mgr = SSLManager(config)
    
    certificates = ssl_mgr.list_certificates()
    
    if not certificates:
        console.print("[yellow]No certificates found[/yellow]")
        return
    
    table = Table(title="SSL Certificates")
    table.add_column("Domain", style="cyan")
    table.add_column("Subject", style="green")
    table.add_column("Issuer", style="blue")
    table.add_column("Valid Until", style="yellow")
    
    for cert in certificates:
        table.add_row(
            cert.get('file', '').split('/')[-1].replace('.pem', ''),
            cert.get('subject', 'N/A'),
            cert.get('issuer', 'N/A'),
            cert.get('valid_until', 'N/A')
        )
    
    console.print(table)

def main():
    cli()