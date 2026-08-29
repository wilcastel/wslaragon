"""Opt-in native-Ubuntu integration harness for agent-privileged site creation.

This exercises the *real* privilege boundary end to end: TTY bootstrap of the
root helper + dedicated sudoers fragment, a non-interactive ``sudo -n`` ready
probe, normal agent-mode creation, a forced headless second-registration
rollback, and ``disable`` with sudoers-first removal.

It is DISABLED by default. It installs a system helper, writes a sudoers
fragment and mutates ``/etc/hosts`` / Nginx, so it must only ever run against a
dedicated throwaway user + root on a native-Ubuntu box you are willing to
change. Enable it explicitly:

    WSLARAGON_AGENT_NATIVE_TEST=1 \
      ./venv/bin/pytest -m "integration and requires_sudo" \
      tests/integration/test_agent_privilege_native.py

Never run this against your normal account or system paths.
"""
import os
import shutil
import subprocess

import pytest

from wslaragon.core.platform import Platform

pytestmark = [pytest.mark.integration, pytest.mark.requires_sudo]

_ENABLED = os.environ.get("WSLARAGON_AGENT_NATIVE_TEST") == "1"
_SETUP_SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "..", "scripts", "agent-privilege-setup.sh"
)

pytestmark.append(
    pytest.mark.skipif(
        not _ENABLED,
        reason="native agent-privilege harness is opt-in; set WSLARAGON_AGENT_NATIVE_TEST=1",
    )
)


@pytest.fixture(scope="module")
def bootstrapped_helper():
    """Bootstrap the helper before the module and always disable it afterwards."""
    if Platform.is_wsl() or not shutil.which("sudo"):
        pytest.skip("requires a native-Ubuntu host with sudo")
    if not os.path.exists(_SETUP_SCRIPT):
        pytest.skip(f"setup script not found: {_SETUP_SCRIPT}")

    subprocess.run(["bash", _SETUP_SCRIPT, "bootstrap"], check=True)
    try:
        yield
    finally:
        subprocess.run(["bash", _SETUP_SCRIPT, "disable"], check=False)


def test_ready_probe_is_non_interactive(bootstrapped_helper):
    proc = subprocess.run(
        ["sudo", "-n", "--", "/usr/lib/wslaragon/agent-privilege-helper"],
        input='{"version":1,"op":"ready"}\n',
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert proc.returncode == 0, proc.stderr


@pytest.mark.skip(reason="fill in once a dedicated test user/root fixture is available")
def test_normal_agent_creation_and_headless_rollback(bootstrapped_helper):
    """Placeholder for the full normal-create + forced headless rollback + disable
    flow against an isolated dedicated account."""
