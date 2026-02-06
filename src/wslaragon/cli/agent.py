import click
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
import os

from wslaragon.core.config import Config
from wslaragon.services.agent.agent_manager import AgentManager

console = Console()

@click.group()
def agent():
    """Agentic AI management commands"""
    pass

@agent.command('init')
@click.option('--preset', default='default', help='Skill preset (default, laravel, wordpress, python)')
@click.option('--path', default='.', help='Target directory (default: current)')
def init_agent(preset, path):
    """Initialize .agent structure with skills"""
    config = Config()
    mgr = AgentManager(config)
    
    # Check valid presets
    valid_presets = mgr.get_presets()
    if preset not in valid_presets:
        console.print(f"[red]✗ Invalid preset '{preset}'. Available: {', '.join(valid_presets.keys())}[/red]")
        return
        
    with console.status(f"[bold green]Initializing Agent structure ({preset})..."):
        result = mgr.init_agent_structure(path, preset)
    
    if result['success']:
        console.print(Panel(
            f"[bold green]Agent Core Initialized[/bold green]\n\n"
            f"Preset: {result['preset']}\n"
            f"Location: {result['path']}",
            title="Success"
        ))
        
        # Draw tree
        tree = Tree(f"[bold blue].agent/[/bold blue]")
        skills = tree.add("skills")
        for skill in result['skills']:
            skills.add(f"[green]{skill}/SKILL.md[/green]")
        tree.add("memory")
        tree.add("workflows")
        
        console.print(tree)
        console.print("\n[dim]You can now ask your AI assistant to use these skills by name.[/dim]")
    else:
        console.print(f"[red]✗ Failed to initialize: {result['error']}[/red]")
