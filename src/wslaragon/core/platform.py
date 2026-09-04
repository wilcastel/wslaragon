"""Host platform detection and platform-specific defaults."""

from pathlib import Path
from typing import Dict


def read_os_release(path: Path = Path("/etc/os-release")) -> Dict[str, str]:
    values: Dict[str, str] = {}
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return values


def _kernel_release() -> str:
    try:
        return Path("/proc/sys/kernel/osrelease").read_text(encoding="utf-8").lower()
    except OSError:
        return ""


def detect_platform() -> str:
    """Detect the configuration profile used by WSLaragon."""
    if Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists() or "microsoft" in _kernel_release():
        return "wsl"
    release = read_os_release()
    distro_ids = {release.get("ID", "").lower()}
    distro_ids.update(release.get("ID_LIKE", "").lower().split())
    if "arch" in distro_ids:
        return "omarchy" if Path("/usr/share/omarchy").exists() else "arch"
    return "linux"


def platform_defaults(platform: str, home_dir: Path) -> Dict:
    """Return paths and service conventions for a supported platform."""
    ssl_dir = home_dir / ".wslaragon" / "ssl"
    common = {
        "platform": {"name": platform},
        "ssl": {
            "dir": str(ssl_dir),
            "ca_file": str(ssl_dir / "rootCA.pem"),
            "ca_key": str(ssl_dir / "rootCA-key.pem"),
        },
        "sites": {"tld": ".test", "document_root": str(home_dir / "web")},
    }
    if platform in {"arch", "omarchy"}:
        common.update({
            "php": {
                "version": "system", "ini_file": "/etc/php/php.ini",
                "extensions_dir": "/usr/lib/php/modules",
                "fpm_service": "php-fpm",
                "fpm_listen": "unix:/run/php-fpm/php-fpm.sock",
            },
            "nginx": {
                "config_dir": "/etc/nginx",
                "sites_available": "/etc/nginx/sites-available",
                "sites_enabled": "/etc/nginx/sites-enabled",
                "client_max_body_size": "512M",
                "user": "http",
            },
            "mysql": {
                "data_dir": "/var/lib/mysql", "config_file": "/etc/my.cnf.d/server.cnf",
                "user": "root", "password": "",
            },
            "hosts": {"file": "/etc/hosts", "mode": "local"},
            "windows": {"hosts_file": "/mnt/c/Windows/System32/drivers/etc/hosts"},
        })
    else:
        windows_hosts = "/mnt/c/Windows/System32/drivers/etc/hosts"
        common.update({
            "php": {
                "version": "8.3", "ini_file": "/etc/php/8.3/fpm/php.ini",
                "extensions_dir": "/usr/lib/php/20230831",
                "fpm_service": "php8.3-fpm",
                "fpm_listen": "unix:/var/run/php/php8.3-fpm.sock",
            },
            "nginx": {
                "config_dir": "/etc/nginx",
                "sites_available": "/etc/nginx/sites-available",
                "sites_enabled": "/etc/nginx/sites-enabled",
                "client_max_body_size": "512M",
                "user": "www-data",
            },
            "mysql": {
                "data_dir": "/var/lib/mysql",
                "config_file": "/etc/mysql/mariadb.conf.d/50-server.cnf",
                "user": "root", "password": "",
            },
            "hosts": {"file": windows_hosts, "mode": "windows"},
            "windows": {"hosts_file": windows_hosts},
        })
    return common
