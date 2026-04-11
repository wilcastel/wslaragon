"""
Node.js process management commands for WSLaragon CLI.
"""
import click
import logging
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ..core.config import Config
from ..services.nginx import NginxManager
from ..services.mysql import MySQLManager
from ..services.sites import SiteManager
from ..services.node.pm2 import PM2Manager

logger = logging.getLogger(__name__)
console = Console()


@click.group()
def node():
    """Node.js process management (PM2)"""
    pass


@node.command('list')
def list_node():
    """List running Node processes"""
    pm2 = PM2Manager()
    processes = pm2.list_processes()
    
    if not processes:
        console.print("[yellow]No running Node processes found[/yellow]")
        return
        
    table = Table(title="Node.js Processes (PM2)")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Memory", style="blue")
    table.add_column("Uptime", style="yellow")
    
    for proc in processes:
        pm2_env = proc.get('pm2_env', {})
        status = pm2_env.get('status', 'unknown')
        status_color = "green" if status == 'online' else "red"
        
        mem = proc.get('monit', {}).get('memory', 0) / 1024 / 1024
        
        table.add_row(
            str(proc.get('pm_id')),
            proc.get('name'),
            f"[{status_color}]{status}[/{status_color}]",
            f"{mem:.1f} MB",
            str(pm2_env.get('pm_uptime', 0))
        )
    
    console.print(table)


@node.command('start')
@click.argument('site_name')
def start_node(site_name):
    """Start app for a site (looks for app.js/server.js/npm start)"""
    config = Config()
    nginx = NginxManager(config)
    # But we can read sites.json directly or via SiteManager
    site_mgr = SiteManager(config, nginx, MySQLManager(config))
    site = site_mgr.get_site(site_name)
    
    if not site:
        console.print(f"[red]✗ Site '{site_name}' not found[/red]")
        return
        
    if not site.get('proxy_port'):
        console.print(f"[red]✗ Site '{site_name}' is not configured as an App (no proxy port)[/red]")
        return
        
    pm2 = PM2Manager()
    
    # Heuristic to find entry point
    web_root = Path(site['document_root'])
    script_to_run = "npm"
    
    # Simplified logic: 
    # If package.json exists -> pm2 start npm --name "site" -- start
    # If app.js exists -> pm2 start app.js --name "site"
    
    if (web_root / "app.js").exists():
        script_to_run = str(web_root / "app.js")
    elif (web_root / "main.py").exists():
        script_to_run = str(web_root / "main.py")
        # For python we need interpreter
        # This will be handled by auto-detection or we can force it
        
    # We'll use the generic PM2 start logic we built, but we need to refine it for 'npm' case vs 'file' case
    # The current PM2Manager.start_process assumes a file path.
    
    # Let's trust PM2 to be smart or just point to the likely entry file if we created it.
    # Since we created 'app.js' in our create_site logic, let's look for that first.
    
    with console.status(f"[bold green]Starting process for {site_name}..."):
        # Set PORT env via config environment of PM2
        # For now, let's try starting app.js directly if it exists, as it's our standard
        if (web_root / "app.js").exists():
             result = pm2.start_process(site_name, str(web_root / "app.js"), site['proxy_port'], cwd=str(web_root))
        elif (web_root / "package.json").exists():
             # Fallback to npm start
             console.print("[yellow]Notice: package.json found but no app.js. Attempting to start 'npm start' via PM2...[/yellow]")
             # We must pass --cwd so PM2 finds package.json
             # Also --port env var is good practice
             result = pm2._run_pm2(['start', 'npm', '--name', site_name, '--cwd', str(web_root), '--', 'start'])
        elif (web_root / "main.py").exists():
             result = pm2.start_process(site_name, str(web_root / "main.py"), site['proxy_port'], interpreter='python3', cwd=str(web_root))
        else:
             console.print("[red]✗ No entry point (app.js, main.py) found.[/red]")
             return

    if result['success']:
        console.print(f"[green]✓ Process '{site_name}' started on port {site['proxy_port']}[/green]")
        pm2.save() # Save list
    else:
        console.print(f"[red]✗ Failed to start process: {result.get('error')}[/red]")


@node.command('stop')
@click.argument('site_name')
def stop_node(site_name):
    """Stop Node process"""
    pm2 = PM2Manager()
    with console.status(f"[bold red]Stopping {site_name}..."):
        result = pm2.stop_process(site_name)
        
    if result['success']:
        console.print(f"[green]✓ Process '{site_name}' stopped[/green]")
        pm2.save()
    else:
        console.print(f"[red]✗ Failed to stop: {result.get('error')}[/red]")


@node.command('delete')
@click.argument('site_name')
def delete_node(site_name):
    """Delete Node process"""
    pm2 = PM2Manager()
    with console.status(f"[bold red]Deleting {site_name}..."):
        result = pm2.delete_process(site_name)
    
    if result['success']:
        console.print(f"[green]✓ Process '{site_name}' deleted[/green]")
        pm2.save() # Save list to persist deletion
    else:
        console.print(f"[red]✗ Failed to delete process: {result.get('error')}[/red]")


@node.command('restart')
@click.argument('site_name')
def restart_node(site_name):
    """Restart Node process"""
    pm2 = PM2Manager()
    with console.status(f"[bold yellow]Restarting {site_name}..."):
        result = pm2.restart_process(site_name)
        
    if result['success']:
        console.print(f"[green]✓ Process '{site_name}' restarted[/green]")
    else:
        console.print(f"[red]✗ Failed to restart: {result.get('error')}[/red]")