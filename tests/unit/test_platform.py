"""Tests for platform detection utilities."""
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest


class TestPlatformDetection:
    """Test suite for platform detection helpers."""

    @pytest.fixture
    def platform(self):
        from wslaragon.core.platform import Platform
        return Platform

    def test_is_wsl_returns_true_when_wsl_distro_name_set(self, platform):
        """WSL_DISTRO_NAME env var marks WSL."""
        with patch.dict('os.environ', {'WSL_DISTRO_NAME': 'Ubuntu'}):
            assert platform.is_wsl() is True

    def test_is_wsl_returns_true_when_proc_version_has_microsoft(self, platform):
        """/proc/version containing 'microsoft' marks WSL."""
        proc_version = 'Linux version 5.15.0-microsoft-standard-WSL2'
        with patch.dict('os.environ', {}, clear=True):
            with patch('builtins.open', mock_open(read_data=proc_version)):
                with patch('pathlib.Path.exists', return_value=True):
                    assert platform.is_wsl() is True

    def test_is_wsl_returns_false_on_native_linux(self, platform):
        """Native Linux without WSL markers is not WSL."""
        proc_version = 'Linux version 5.15.0-generic #1-Ubuntu SMP'
        with patch.dict('os.environ', {}, clear=True):
            with patch('builtins.open', mock_open(read_data=proc_version)):
                with patch('pathlib.Path.exists', return_value=True):
                    assert platform.is_wsl() is False

    def test_is_wsl_returns_false_when_proc_version_unreadable(self, platform):
        """Missing /proc/version falls back to False."""
        with patch.dict('os.environ', {}, clear=True):
            with patch('builtins.open', side_effect=FileNotFoundError):
                assert platform.is_wsl() is False

    def test_is_native_ubuntu_returns_true_on_ubuntu(self, platform):
        """Native Ubuntu is detected from /etc/os-release."""
        os_release = 'PRETTY_NAME="Ubuntu 24.04 LTS"\nID=ubuntu\n'
        with patch.object(platform, 'is_wsl', return_value=False):
            with patch('builtins.open', mock_open(read_data=os_release)):
                assert platform.is_native_ubuntu() is True

    def test_is_native_ubuntu_returns_false_on_wsl(self, platform):
        """WSL is never native Ubuntu."""
        with patch.object(platform, 'is_wsl', return_value=True):
            assert platform.is_native_ubuntu() is False

    def test_is_native_ubuntu_returns_false_on_non_ubuntu(self, platform):
        """Non-Ubuntu Linux distributions return False."""
        os_release = 'PRETTY_NAME="Debian GNU/Linux 12"\nID=debian\n'
        with patch.object(platform, 'is_wsl', return_value=False):
            with patch('builtins.open', mock_open(read_data=os_release)):
                assert platform.is_native_ubuntu() is False

    def test_is_native_ubuntu_returns_false_when_os_release_unreadable(self, platform):
        """Missing /etc/os-release falls back to False."""
        with patch.object(platform, 'is_wsl', return_value=False):
            with patch('builtins.open', side_effect=FileNotFoundError):
                assert platform.is_native_ubuntu() is False


class TestHostsFile:
    """Test suite for hosts file path resolution."""

    @pytest.fixture
    def platform(self):
        from wslaragon.core.platform import Platform
        return Platform

    @pytest.fixture
    def mock_config(self):
        class MockConfig:
            def get(self, key, default=None):
                return {
                    'windows.hosts_file': '/mnt/c/Windows/System32/drivers/etc/hosts',
                    'hosts.hosts_file': '/etc/hosts',
                }.get(key, default)
        return MockConfig()

    def test_hosts_file_returns_etc_hosts_on_native_ubuntu(self, platform, mock_config):
        """Native Ubuntu resolves to /etc/hosts."""
        with patch.object(platform, 'is_wsl', return_value=False):
            result = platform.hosts_file(mock_config)
            assert result == Path('/etc/hosts')

    def test_hosts_file_returns_windows_hosts_on_wsl(self, platform, mock_config):
        """WSL resolves to the Windows hosts file from config."""
        with patch.object(platform, 'is_wsl', return_value=True):
            result = platform.hosts_file(mock_config)
            assert result == Path('/mnt/c/Windows/System32/drivers/etc/hosts')

    def test_hosts_file_uses_config_fallback_for_wsl(self, platform):
        """WSL uses the configured windows.hosts_file path."""
        class MinimalConfig:
            def get(self, key, default=None):
                if key == 'windows.hosts_file':
                    return '/custom/windows/hosts'
                return default

        with patch.object(platform, 'is_wsl', return_value=True):
            result = platform.hosts_file(MinimalConfig())
            assert result == Path('/custom/windows/hosts')
