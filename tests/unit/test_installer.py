"""Tests for installer/uninstaller shell scripts and project metadata."""
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).parent.parent.parent


def _render_setup_env_config(
    scripts_dir,
    php_version="8.5",
    php_ini="/etc/php/8.5/fpm/php.ini",
    php_extensions_dir="/usr/lib/php/20250925",
    ssl_dir="/home/user/.wslaragon/ssl",
    web_root="/home/user/web",
    windows_hosts_file="/mnt/c/Windows/System32/drivers/etc/hosts",
):
    """Extract and render the YAML heredoc produced by setup-env.sh."""
    content = (scripts_dir / "setup-env.sh").read_text()
    match = re.search(r'cat > "\$CONFIG_FILE" << EOF\n(.*?)\nEOF', content, re.DOTALL)
    assert match, "setup-env.sh config heredoc not found"
    template = match.group(1)
    return (
        template.replace("$PHP_VERSION", php_version)
        .replace("$PHP_INI", php_ini)
        .replace("$PHP_EXTENSIONS_DIR", php_extensions_dir)
        .replace("$SSL_DIR", ssl_dir)
        .replace("$WEB_ROOT", web_root)
        .replace("$WINDOWS_HOSTS_FILE", windows_hosts_file)
    )


@pytest.fixture
def scripts_dir():
    return PROJECT_ROOT / "scripts"


class TestVarsScript:
    """Tests for scripts/vars.sh defaults."""

    def test_hosts_file_points_to_etc_hosts(self, scripts_dir):
        content = (scripts_dir / "vars.sh").read_text()
        assert 'HOSTS_FILE="/etc/hosts"' in content

    def test_php_version_is_85(self, scripts_dir):
        content = (scripts_dir / "vars.sh").read_text()
        assert 'PHP_VERSION="8.5"' in content


class TestSetupEnvScript:
    """Tests for scripts/setup-env.sh platform behavior."""

    def test_no_wsl_only_warning(self, scripts_dir):
        content = (scripts_dir / "setup-env.sh").read_text()
        assert "designed for WSL2" not in content
        assert "WSL2 environment" not in content

    def test_has_platform_check(self, scripts_dir):
        content = (scripts_dir / "setup-env.sh").read_text()
        assert "/proc/version" in content

    def test_generated_config_yaml_is_valid(self, scripts_dir):
        rendered = _render_setup_env_config(scripts_dir)
        config = yaml.safe_load(rendered)
        assert config["php"]["version"] == "8.5"
        assert config["php"]["ini_file"] == "/etc/php/8.5/fpm/php.ini"
        assert config["nginx"]["config_dir"] == "/etc/nginx"

    def test_generated_config_yaml_accepts_alternate_php_version(self, scripts_dir):
        rendered = _render_setup_env_config(
            scripts_dir, php_version="8.4", php_ini="/etc/php/8.4/fpm/php.ini"
        )
        config = yaml.safe_load(rendered)
        assert config["php"]["version"] == "8.4"
        assert config["php"]["ini_file"] == "/etc/php/8.4/fpm/php.ini"


class TestDocs:
    """Documentation checks for project guides."""

    def test_ubuntu_docs_describe_integration_tests_without_coverage_gate(self, scripts_dir):
        content = (scripts_dir.parent / "docs" / "UBUNTU.md").read_text()
        assert "pytest tests/integration/ -v --run-slow --tb=short --no-cov" in content


class TestInstallScript:
    """Tests for scripts/install.sh stack setup."""

    def test_installs_php85_packages(self, scripts_dir):
        content = (scripts_dir / "install.sh").read_text()
        assert "php8.5-fpm" in content or 'php${PHP_VERSION}-fpm' in content

    def test_has_php_ppa_fallback(self, scripts_dir):
        content = (scripts_dir / "install.sh").read_text()
        assert "ppa" in content.lower() or "ondrej" in content.lower()

    def test_creates_wslaragon_database_user(self, scripts_dir):
        content = (scripts_dir / "install.sh").read_text()
        assert "wslaragon" in content
        assert "CREATE USER" in content.upper() or "grant" in content.lower()

    def test_installs_ubuntu_stack_tools(self, scripts_dir):
        content = (scripts_dir / "install.sh").read_text()
        assert "composer" in content.lower()
        assert "nvm" in content.lower()
        assert "pnpm" in content.lower()
        assert "phpmyadmin" in content.lower()


class TestUninstallScript:
    """Tests for scripts/uninstall.sh behavior."""

    def test_uninstall_script_exists(self, scripts_dir):
        uninstall = scripts_dir / "uninstall.sh"
        assert uninstall.exists()
        assert os.access(uninstall, os.X_OK)

    def test_default_preserves_data(self, scripts_dir):
        content = (scripts_dir / "uninstall.sh").read_text()
        assert "--purge" in content
        assert "preserve" in content.lower()

    def test_purge_requires_confirmation(self, scripts_dir):
        content = (scripts_dir / "uninstall.sh").read_text()
        assert "read -r" in content or "confirm" in content.lower()
        assert "--purge" in content

    def test_uninstall_stops_services_and_removes_packages(self, scripts_dir):
        content = (scripts_dir / "uninstall.sh").read_text()
        assert "systemctl stop" in content
        assert "apt remove" in content.lower()


class TestProjectMetadata:
    """Tests that project metadata reflects Ubuntu support."""

    def test_pyproject_description_drops_wsl2_only(self):
        content = (PROJECT_ROOT / "pyproject.toml").read_text()
        assert "only for WSL2" not in content
        assert "only" not in content.split('description = "')[1].split('"')[0].lower()
        assert "Ubuntu" in content or "ubuntu" in content.lower()

    def test_main_docstring_drops_wsl2_only(self):
        from wslaragon.cli import main

        doc = main.cli.callback.__doc__
        assert "only for WSL2" not in doc
        assert "Ubuntu" in doc


class TestShellLint:
    """Shell script linting via shellcheck when available."""

    @pytest.mark.skipif(shutil.which("shellcheck") is None, reason="shellcheck not installed")
    def test_shellcheck_on_scripts(self, scripts_dir):
        scripts = [
            scripts_dir / name
            for name in ["vars.sh", "setup-env.sh", "install.sh", "uninstall.sh"]
            if (scripts_dir / name).exists()
        ]
        result = subprocess.run(
            ["shellcheck", "-x", "--severity=warning"] + [str(s) for s in scripts],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
