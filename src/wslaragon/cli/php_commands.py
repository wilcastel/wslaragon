"""
PHP management commands for WSLaragon CLI.
"""
import click
import subprocess
import logging

from rich.console import Console
from rich.table import Table

from ..core.config import Config
from ..services.php import PHPManager

logger = logging.getLogger(__name__)
console = Console()


@click.group()
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


@click.group()
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


# Register config as a subgroup of php
php.add_command(config)