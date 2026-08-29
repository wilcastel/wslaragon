"""Tests for wslaragon.core.privilege.ensure_sudo."""
import subprocess
from unittest.mock import MagicMock, patch

from wslaragon.core.privilege import _interactive, ensure_sudo


def test_interactive_is_false_without_a_terminal():
    # pytest captures stdio, so neither stream is a real TTY here.
    assert _interactive() is False


@patch("wslaragon.core.privilege._interactive", return_value=True)
@patch("wslaragon.core.privilege.subprocess.run")
def test_valid_cached_ticket_proceeds_without_refresh(mock_run, _interactive):
    mock_run.return_value = MagicMock(returncode=0)  # sudo -n -v succeeds

    assert ensure_sudo() is True
    mock_run.assert_called_once_with(["sudo", "-n", "-v"], capture_output=True)


@patch("wslaragon.core.privilege._interactive", return_value=False)
@patch("wslaragon.core.privilege.subprocess.run")
def test_no_tty_proceeds_without_prompting(mock_run, _interactive):
    mock_run.return_value = MagicMock(returncode=1)  # no cached ticket

    assert ensure_sudo() is True
    # only the non-interactive probe ran; plain `sudo -v` never
    mock_run.assert_called_once_with(["sudo", "-n", "-v"], capture_output=True)


@patch("wslaragon.core.privilege._interactive", return_value=True)
@patch("wslaragon.core.privilege.subprocess.run")
def test_tty_refreshes_interactively_when_ticket_missing(mock_run, _interactive):
    mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=0)]

    assert ensure_sudo() is True
    assert mock_run.call_args_list[1].args[0] == ["sudo", "-v"]
    assert mock_run.call_args_list[1].kwargs == {"check": True}


@patch("wslaragon.core.privilege._interactive", return_value=True)
@patch("wslaragon.core.privilege.subprocess.run")
def test_tty_auth_failure_returns_false_and_warns(mock_run, _interactive):
    mock_run.side_effect = [
        MagicMock(returncode=1),
        subprocess.CalledProcessError(1, ["sudo", "-v"]),
    ]
    console = MagicMock()

    assert ensure_sudo(console) is False
    console.print.assert_called_once()
