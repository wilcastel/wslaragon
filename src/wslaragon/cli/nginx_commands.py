"""
Nginx management commands for WSLaragon CLI.
"""
import click
import subprocess
import logging

from rich.console import Console
from rich.table import Table

from ..core.config import Config
from ..services.nginx import NginxManager
from ..services.mysql import MySQLManager
from ..services.sites import SiteManager

logger = logging.getLogger(__name__)
console = Console()


@click.group()
def nginx():
    """Nginx management commands"""
    pass


@click.group()
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


# Register config as a subgroup of nginx
nginx.add_command(config)