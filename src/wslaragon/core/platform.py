"""Runtime platform detection helpers."""
import os
from pathlib import Path


class Platform:
    """Detect the runtime platform and resolve platform-specific paths."""

    @staticmethod
    def is_wsl() -> bool:
        """Return True when running inside Windows Subsystem for Linux."""
        if os.environ.get('WSL_DISTRO_NAME'):
            return True

        try:
            with open('/proc/version', 'r', encoding='utf-8') as f:
                return 'microsoft' in f.read().lower()
        except (FileNotFoundError, PermissionError, OSError):
            return False

    @staticmethod
    def is_native_ubuntu() -> bool:
        """Return True when running on native Ubuntu (not WSL)."""
        if Platform.is_wsl():
            return False

        try:
            with open('/etc/os-release', 'r', encoding='utf-8') as f:
                return 'ubuntu' in f.read().lower()
        except (FileNotFoundError, PermissionError, OSError):
            return False

    @staticmethod
    def hosts_file(config) -> Path:
        """Return the hosts file path for the current platform."""
        if Platform.is_wsl():
            return Path(config.get('windows.hosts_file', '/mnt/c/Windows/System32/drivers/etc/hosts'))
        return Path(config.get('hosts.hosts_file', '/etc/hosts'))
