"""
WSLaragon CLI - Main entry point.

This module defines the top-level CLI group and registers all command subgroups
from their respective modules for better maintainability.
"""
import click
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .doctor import doctor_command
from .agent import agent
from .site_commands import site
from .service_commands import service
from .php_commands import php
from .mysql_commands import mysql
from .ssl_commands import ssl
from .node_commands import node
from .nginx_commands import nginx

logger = logging.getLogger(__name__)
console = Console()


@click.group(invoke_without_command=True)
@click.version_option()
@click.option('--glossary', '-g', is_flag=True, help='Show full command glossary')
@click.pass_context
def cli(ctx, glossary):
    """WSLaragon - Laragon-style development environment manager for WSL2"""
    if glossary:
        from rich.markdown import Markdown
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        glosario_path = root_dir / "docs" / "glosario.md"

        if not glosario_path.exists():
            glosario_path = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "glosario.md"

        if glosario_path.exists():
            with open(glosario_path, 'r') as f:
                md = Markdown(f.read())
            console.print(md)
        else:
            console.print(f"[red]Glossary not found at {glosario_path}[/red]")
        ctx.exit()
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option('--install', is_flag=True, help="Automatically install into shell config")
@click.option('--shell', type=click.Choice(['bash', 'zsh']), default='bash', help="Target shell")
def completion(install, shell):
    """Enable shell autocompletion"""
    script = 'eval "$(_WSLARAGON_COMPLETE=bash_source wslaragon)"'
    if shell == 'zsh':
        script = 'eval "$(_WSLARAGON_COMPLETE=zsh_source wslaragon)"'

    if install:
        rc_file = Path.home() / f".{shell}rc"

        if not rc_file.exists():
            console.print(f"[red]Could not find configuration file: {rc_file}. Run as your normal user.[/red]")
            return

        # Check for duplicates
        try:
            content = rc_file.read_text()
            if script in content:
                console.print(f"[yellow]Completion already installed in {rc_file}[/yellow]")
                return
        except Exception:
            pass

        try:
            with open(rc_file, "a") as f:
                f.write(f"\n# WSLaragon Autocompletion\n{script}\n")
            console.print(f"[green]✓ Installed to {rc_file}.[/green]")
            console.print(f"[yellow]Please run: source {rc_file}[/yellow]")
        except PermissionError:
            console.print(f"[red]Permission denied writing to {rc_file}. Try running with sudo?[/red]")
    else:
        console.print(f"To enable {shell} completion, add this to your {shell}rc:")
        console.print(Panel(script, title="Completion Script", style="cyan"))


@cli.command()
@click.argument('term', required=False)
def glossary(term):
    """View or search the command glossary"""
    from rich.markdown import Markdown

    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    glosario_path = root_dir / "docs" / "glosario.md"
    if not glosario_path.exists():
        glosario_path = Path("/usr/share/wslaragon/docs/glosario.md")

    if not glosario_path.exists():
        console.print("[red]Glossary not found.[/red]")
        return

    with open(glosario_path, 'r') as f:
        content = f.read()

    if term:
        normalized_term = term.lower()
        sections = content.split('\n## ')

        filtered_content = []
        found = False

        if normalized_term in sections[0].lower():
            filtered_content.append(sections[0])
            found = True

        for s in sections[1:]:
            if normalized_term in s.lower():
                filtered_content.append(f"## {s}")
                found = True

        if found:
            console.print(Markdown('\n'.join(filtered_content)))
        else:
            console.print(f"[yellow]No info found for '{term}' in glossary.[/yellow]")
            console.print("Tip: Use 'wslaragon glossary' to see everything.")
    else:
        console.print(Markdown(content))


# Register all command subgroups
cli.add_command(doctor_command)
cli.add_command(agent)
cli.add_command(site)
cli.add_command(service)
cli.add_command(php)
cli.add_command(mysql)
cli.add_command(ssl)
cli.add_command(node)
cli.add_command(nginx)


def main():
    cli()


if __name__ == '__main__':
    main()