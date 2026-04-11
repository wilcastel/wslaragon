import logging
import click
import subprocess
import os
import socket
import re
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Tuple

from ..core.config import Config
from ..services.php import PHPManager

logger = logging.getLogger(__name__)
console = Console()

def check_port(port: int, host: str = 'localhost') -> bool:
    """Check if a port is in use"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0
    except (OSError, ConnectionError) as e:
        logger.debug(f"check_port failed for {host}:{port}: {e}")
        return False

def get_service_status(service_name: str) -> Tuple[str, str]:
    """Get systemd service status and active state"""
    try:
        # Check active state
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True, text=True
        )
        active = result.stdout.strip()
        
        if active == 'active':
            return 'active', 'Running'
            
        # If not active, check if it failed or is just stopped
        status_cmd = subprocess.run(
            ['systemctl', 'is-failed', service_name],
            capture_output=True, text=True
        )
        if status_cmd.stdout.strip() == 'failed':
            return 'failed', 'Error'
            
        return 'inactive', 'Stopped'
    except FileNotFoundError:
        return 'missing', 'Not installed'
    except Exception as e:
        logger.debug(f"Service status check failed for {service_name}: {e}")
        return 'error', str(e)

@click.command('doctor')
def doctor_command():
    """Diagnose WSLaragon environment issues"""
    config = Config()
    php_mgr = PHPManager(config)
    
    console.print(Panel("[bold cyan]WSLaragon Doctor[/bold cyan]", subtitle="Diagnosing your environment"))
    
    # 1. System Services
    console.print("\n[bold]1. System Services[/bold]")
    services = {
        'Nginx': 'nginx',
        'MariaDB': 'mariadb',
        'Redis': 'redis-server'
    }
    
    # Determine PHP version service name
    current_php_version = php_mgr.get_current_version()
    short_version = None
    if current_php_version:
        v_match = re.search(r'(\d+\.\d+)', current_php_version)
        if v_match:
            short_version = v_match.group(1)
            services[f'PHP {short_version} FPM'] = f'php{short_version}-fpm'
    
    # If detection failed or we want to be safe, check generic if specific not found?
    # Actually php-fpm usually aliases to specific version, but let's stick to detected one.
    if not short_version:
         services['PHP FPM'] = 'php-fpm'
         
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Service")
    table.add_column("Systemd Name")
    table.add_column("Status")
    
    for label, name in services.items():
        state, details = get_service_status(name)
        
        if state == 'active':
            status_style = "green"
        elif state == 'failed':
            status_style = "red"
        elif state == 'missing':
             status_style = "dim"
        else:
            status_style = "yellow"
            
        table.add_row(label, name, f"[{status_style}]{details} ({state})[/{status_style}]")
        
    console.print(table)
    
    # 2. Network Ports
    console.print("\n[bold]2. Network Ports[/bold]")
    ports = {
        80: 'HTTP (Nginx)',
        443: 'HTTPS (Nginx)',
        3306: 'MySQL/MariaDB',
        6379: 'Redis'
    }
    
    # Add PHP FPM port if relevant (default 9000, or 9000+ based on config, usually 9000 for main)
    # Checking 9000 is good practice
    ports[9000] = 'PHP-FPM'
    
    port_table = Table(show_header=True, header_style="bold magenta")
    port_table.add_column("Port")
    port_table.add_column("Service")
    port_table.add_column("Status")
    
    for port, service in ports.items():
        is_open = check_port(port)
        if is_open:
            status = "[green]✓ Listening[/green]"
        else:
            # If service is stopped, closed is expected (yellow). If service running but closed -> red.
            # Simple logic for now:
            status = "[yellow]Broadcasting/Closed[/yellow]"
            
        port_table.add_row(str(port), service, status)
        
    console.print(port_table)
    
    # 3. Security & Config
    console.print("\n[bold]3. Security & Configuration[/bold]")
    
    checks = []
    
    # Check SSL CA
    ca_cert = config.get('ssl.ca_file')
    if ca_cert and os.path.exists(ca_cert):
         checks.append((f"SSL Root CA ({ca_cert})", "[green]✓ Installed[/green]"))
    else:
         checks.append(("SSL Root CA", f"[red]✗ Missing at {ca_cert} (Run 'wslaragon ssl setup')[/red]"))
         
    # Check PHP Ini
    php_ini = config.get('php.ini_file')
    if php_ini and os.path.exists(php_ini):
         checks.append((f"PHP Configuration ({php_ini})", "[green]✓ Found[/green]"))
    else:
         checks.append(("PHP Configuration", f"[red]✗ Missing at {php_ini}[/red]"))
         
    sec_table = Table(show_header=False, box=None)
    for check in checks:
        sec_table.add_row(check[0], check[1])
    console.print(sec_table)
    
    console.print("\n[dim]Tip: Use 'wslaragon service start <name>' to fix stopped services.[/dim]")
