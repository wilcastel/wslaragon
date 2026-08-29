"""Best-effort sudo credential handling for privileged CLI commands."""
import subprocess
import sys


def _interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def ensure_sudo(console=None) -> bool:
    """Warm up sudo so a privileged command can proceed.

    A still-valid cached ticket, or the absence of a TTY (e.g. the MCP server),
    proceeds immediately: the individual ``sudo <cmd>`` calls then rely on the
    NOPASSWD policy. Only with an interactive terminal do we refresh the sudo
    timestamp so a long operation behind a spinner never hits a mid-run
    password prompt.

    Returns ``False`` only when an interactive refresh was attempted and the
    user failed to authenticate.
    """
    if subprocess.run(["sudo", "-n", "-v"], capture_output=True).returncode == 0:
        return True
    if not _interactive():
        return True
    try:
        subprocess.run(["sudo", "-v"], check=True)
        return True
    except subprocess.CalledProcessError:
        if console is not None:
            console.print("[red]✗ This command requires sudo privileges[/red]")
        return False
