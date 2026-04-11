"""
SSL management commands for WSLaragon CLI.
"""
import click
import logging

from rich.console import Console
from rich.table import Table

from ..core.config import Config
from ..services.ssl import SSLManager

logger = logging.getLogger(__name__)
console = Console()


@click.group()
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
        result = ssl_mgr.generate_cert(domain)
    
    if result['success']:
        console.print(f"[green]✓ Certificate generated for {domain}[/green]")
    else:
        console.print(f"[red]✗ Failed to generate certificate: {result['error']}[/red]")


@ssl.command()
@click.argument('domain')
def delete(domain):
    """Delete SSL certificate for domain"""
    config = Config()
    ssl_mgr = SSLManager(config)
    
    if click.confirm(f"Are you sure you want to delete SSL certificate for '{domain}'?"):
        with console.status(f"[bold red]Deleting certificate for {domain}..."):
            result = ssl_mgr.revoke_certificate(domain)
        
        if result:
            console.print(f"[green]✓ Certificate deleted for {domain}[/green]")
        else:
            console.print(f"[red]✗ Failed to delete certificate for {domain}[/red]")


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