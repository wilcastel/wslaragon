"""Contract tests for the unified Omarchygon installer."""

import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]
INSTALLER = ROOT / "scripts" / "install-omarchygon.sh"


def run_installer(*arguments):
    return subprocess.run(
        [str(INSTALLER), *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_installer_is_executable_and_has_valid_bash_syntax():
    assert INSTALLER.stat().st_mode & 0o111
    result = subprocess.run(
        ["bash", "-n", str(INSTALLER)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_installer_help_documents_safe_database_selection():
    result = run_installer("--help")

    assert result.returncode == 0
    assert "--database <mysql8|mariadb11>" in result.stdout
    assert "--skip-database" in result.stdout
    assert "leaves the WSLaragon runtime stopped" in result.stdout


def test_installer_rejects_invalid_database_before_installing():
    result = run_installer("--database", "postgres")

    assert result.returncode == 2
    assert "Invalid database container: postgres" in result.stderr


def test_installer_rejects_unknown_options_before_installing():
    result = run_installer("--does-not-exist")

    assert result.returncode == 2
    assert "Unknown option: --does-not-exist" in result.stderr

