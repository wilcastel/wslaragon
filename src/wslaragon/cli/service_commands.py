"""
Service management commands for WSLaragon CLI.
"""
import click
import logging

from rich.console import Console
from rich.table import Table

from ..core.services import ServiceManager

logger = logging.getLogger(__name__)
console = Console()


@click.group()
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