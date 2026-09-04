"""Top-level commands for the centralized WSLaragon runtime."""

import subprocess

import click
from rich.console import Console
from rich.table import Table

from ..services.runtime import RuntimeManager

console = Console()


def _authorize_sudo():
    """Request sudo credentials before Rich hides subprocess output."""
    try:
        subprocess.run(['sudo', '-v'], check=True, timeout=30)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        console.print('[red]✗ Could not obtain sudo privileges.[/red]')
        return False


def _print_actions(result, active_label):
    for item in result['components']:
        if item.get('skipped'):
            console.print(f"[dim]○ {item['component']}: {item.get('detail')}[/dim]")
        elif item['success']:
            console.print(f"[green]✓ {item['component']}: {active_label}[/green]")
        else:
            console.print(f"[red]✗ {item['component']}: {item.get('detail') or 'failed'}[/red]")


@click.command('on')
def runtime_on():
    """Start the complete local development environment."""
    if not _authorize_sudo():
        return
    manager = RuntimeManager()
    with console.status('[bold green]Starting WSLaragon...'):
        result = manager.start()
    _print_actions(result, 'running')
    if result['success']:
        console.print('[bold green]WSLaragon is ready.[/bold green]')


@click.command('off')
def runtime_off():
    """Stop the environment and disable service autostart."""
    if not _authorize_sudo():
        return
    manager = RuntimeManager()
    with console.status('[bold red]Stopping WSLaragon...'):
        result = manager.stop()
    _print_actions(result, 'stopped')
    if result['success']:
        console.print('[bold green]WSLaragon is fully stopped.[/bold green]')


@click.command('status')
def runtime_status():
    """Show the centralized environment status."""
    result = RuntimeManager().status()
    table = Table(title='WSLaragon Runtime')
    table.add_column('Component')
    table.add_column('Status')
    table.add_column('Details')
    for item in result['components']:
        state = '[green]Running[/green]' if item['running'] else '[red]Stopped[/red]'
        table.add_row(item['component'], state, item.get('detail') or '')
    console.print(table)
    label = '[green]ON[/green]' if result['running'] else '[yellow]OFF or partial[/yellow]'
    console.print(f"Environment: {label}")
