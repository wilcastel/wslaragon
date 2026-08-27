"""Subprocess harness for the TTY-only agent privilege administrator lifecycle."""
import os
import stat
import subprocess
from pathlib import Path

import pytest


SOURCE = Path(__file__).parents[2] / "scripts" / "agent-privilege-setup.sh"


def install_harness(tmp_path):
    root = tmp_path / "root"
    source = tmp_path / "agent-privilege-helper.py"
    source.write_text('#!/usr/bin/env python3\nimport os\nprint(os.getenv("READY_RESPONSE", "{\\"version\\":1,\\"ok\\":true,\\"code\\":\\"ok\\"}"))\n')
    source.chmod(0o755)
    script = tmp_path / "setup.sh"
    text = SOURCE.read_text()
    text = text.replace('ROOT="/"', f'ROOT="{root}"').replace(
        'SOURCE_HELPER="scripts/agent-privilege-helper.py"', f'SOURCE_HELPER="{source}"'
    )
    text = text.replace("OWNER=0", f"OWNER={os.getuid()}")
    text = text.replace(
        "sudo -n -- /usr/lib/wslaragon/agent-privilege-helper",
        f"sudo -n -- {root}/usr/lib/wslaragon/agent-privilege-helper",
    )
    text = text.replace("is_tty() { [ -t 0 ] && [ -t 1 ]; }", "is_tty() { return 0; }")
    text = text.replace("platform_ok() {", "platform_ok() { return 0; }\nplatform_unused() {")
    script.write_text(text)
    script.chmod(0o755)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    commands = {
        "sudo": '#!/bin/sh\nwhile [ "$1" = -n ] || [ "$1" = -- ]; do shift; done\nexec "$@"\n',
        "visudo": '#!/bin/sh\n[ "${VISUDO_FAIL:-}" != 1 ]\n',
        "id": '#!/bin/sh\n[ "$1" = -un ] && { echo wslaragon; exit; }; echo 1000\n',
        "getent": '#!/bin/sh\necho "wslaragon:x:1000:1000::/tmp/wslaragon:/bin/sh"\n',
    }
    for name, body in commands.items():
        command = bindir / name
        command.write_text(body)
        command.chmod(0o755)
    return root, script, bindir


def run(script, bindir, action, **env):
    environment = os.environ | {"PATH": f"{bindir}:{os.environ['PATH']}"} | env
    return subprocess.run([str(script), action], text=True, capture_output=True, env=environment)


def test_bootstrap_refuses_non_tty_before_creating_artifacts(tmp_path):
    root, _, _ = install_harness(tmp_path)
    result = subprocess.run([str(SOURCE), "bootstrap"], text=True, capture_output=True)
    assert result.returncode != 0
    assert not (root / "usr/lib/wslaragon/agent-privilege-helper").exists()


def test_bootstrap_installs_verified_helper_before_dedicated_policy(tmp_path):
    root, script, bindir = install_harness(tmp_path)
    result = run(script, bindir, "bootstrap")
    helper = root / "usr/lib/wslaragon/agent-privilege-helper"
    policy = root / "etc/sudoers.d/wslaragon-agent-privilege"
    assert result.returncode == 0, result.stderr
    assert helper.is_file() and stat.S_IMODE(helper.stat().st_mode) == 0o755
    assert policy.read_text() == "wslaragon ALL=(root) NOPASSWD: /usr/lib/wslaragon/agent-privilege-helper\n"


def test_bootstrap_aborts_on_visudo_failure_without_policy(tmp_path):
    root, script, bindir = install_harness(tmp_path)
    result = run(script, bindir, "bootstrap", VISUDO_FAIL="1")
    assert result.returncode != 0
    assert not (root / "etc/sudoers.d/wslaragon-agent-privilege").exists()
    assert not (root / "usr/lib/wslaragon/agent-privilege-helper").exists()


def test_bootstrap_preserves_legacy_and_foreign_artifacts(tmp_path):
    root, script, bindir = install_harness(tmp_path)
    legacy = root / "etc/sudoers.d/wslaragon"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("legacy\n")
    result = run(script, bindir, "bootstrap")
    assert result.returncode != 0
    assert legacy.read_text() == "legacy\n"


@pytest.mark.parametrize(
    "relative,contents",
    [
        ("usr/lib/wslaragon/agent-privilege-helper", "foreign helper"),
        ("etc/wslaragon/agent-privilege.json", "foreign config"),
        ("etc/sudoers.d/wslaragon-agent-privilege", "foreign policy"),
    ],
)
def test_bootstrap_refuses_foreign_feature_artifacts(tmp_path, relative, contents):
    root, script, bindir = install_harness(tmp_path)
    artifact = root / relative
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(contents)
    result = run(script, bindir, "bootstrap")
    assert result.returncode != 0
    assert artifact.read_text() == contents


def test_readiness_failure_rolls_back_policy_before_helper(tmp_path):
    root, script, bindir = install_harness(tmp_path)
    result = run(script, bindir, "bootstrap", READY_RESPONSE='{"version":1,"ok":false,"code":"not_ready"}')
    assert result.returncode != 0
    assert not (root / "etc/sudoers.d/wslaragon-agent-privilege").exists()
    assert not (root / "usr/lib/wslaragon/agent-privilege-helper").exists()


def test_status_is_read_only_and_disable_removes_verified_artifacts(tmp_path):
    root, script, bindir = install_harness(tmp_path)
    assert run(script, bindir, "bootstrap").returncode == 0
    helper = root / "usr/lib/wslaragon/agent-privilege-helper"
    policy = root / "etc/sudoers.d/wslaragon-agent-privilege"
    before = (helper.stat().st_mtime_ns, policy.stat().st_mtime_ns)
    assert run(script, bindir, "status").returncode == 0
    assert before == (helper.stat().st_mtime_ns, policy.stat().st_mtime_ns)
    assert run(script, bindir, "disable").returncode == 0
    assert not helper.exists() and not policy.exists()
