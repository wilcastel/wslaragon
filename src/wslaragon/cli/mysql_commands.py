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