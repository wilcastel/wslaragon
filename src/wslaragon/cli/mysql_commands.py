"""
MySQL management commands for WSLaragon CLI.
"""
import click
import logging

from rich.console import Console
from rich.table import Table

from ..core.config import Config
from ..services.mysql import MySQLManager

logger = logging.getLogger(__name__)
console = Console()


@click.group()
def mysql():
    """MySQL management commands"""
    pass


@mysql.command()
def status():
    """Show database runtime and connection status."""
    config = Config()
    mysql_mgr = MySQLManager(config)
    backend = config.get('mysql.backend', 'systemd')
    runtime = (
        f"{config.get('mysql.host', '127.0.0.1')}:{config.get('mysql.port', 3306)}"
        if backend == 'docker' else config.get('mysql.service')
    )

    if not mysql_mgr.is_running():
        console.print(f"[yellow]Database runtime is stopped ({backend}: {runtime})[/yellow]")
        return

    version = mysql_mgr.get_version()
    if version:
        console.print(f"[green]✓ MariaDB/MySQL {version} is ready ({backend}: {runtime})[/green]")
    else:
        console.print(f"[red]Runtime is active but the database connection failed ({backend}: {runtime})[/red]")


def _change_runtime(action):
    config = Config()
    mysql_mgr = MySQLManager(config)
    success = getattr(mysql_mgr, action)()
    if success:
        console.print(f"[green]✓ Database runtime {action}ed[/green]")
    else:
        console.print(f"[red]✗ Could not {action} database runtime[/red]")


@mysql.command()
def start():
    """Start the configured database runtime."""
    _change_runtime('start')


@mysql.command()
def stop():
    """Stop the configured database runtime."""
    _change_runtime('stop')


@mysql.command()
def restart():
    """Restart the configured database runtime."""
    _change_runtime('restart')


@mysql.command('use')
@click.argument('container', type=click.Choice(['mysql8', 'mariadb11']))
def use_runtime(container):
    """Select the Docker database container managed by WSLaragon."""
    config = Config()
    if config.get('mysql.backend', 'systemd') != 'docker':
        console.print('[red]✗ Database container selection is only available with Docker[/red]')
        return
    config.set('mysql.container', container)
    console.print(f"[green]✓ Database runtime set to '{container}'[/green]")
    console.print('[yellow]Run wslaragon service start mysql to start it.[/yellow]')


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
        result, error = mysql_mgr.create_database(name)
    
    if result:
        console.print(f"[green]✓ Database '{name}' created[/green]")
    else:
        console.print(f"[red]✗ Failed to create database '{name}'[/red]")
        if error:
            console.print(f"[red]  Error: {error}[/red]")


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
