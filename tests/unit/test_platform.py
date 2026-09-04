from pathlib import Path
from unittest.mock import patch

from wslaragon.core.platform import detect_platform, platform_defaults, read_os_release


def test_read_os_release(tmp_path):
    release = tmp_path / "os-release"
    release.write_text('ID=arch\nNAME="Arch Linux"\nID_LIKE=linux\n')
    assert read_os_release(release)["ID"] == "arch"


@patch("wslaragon.core.platform._kernel_release", return_value="linux")
@patch("wslaragon.core.platform.read_os_release", return_value={"ID": "arch"})
@patch("wslaragon.core.platform.Path.exists")
def test_detects_omarchy(mock_exists, _release, _kernel):
    mock_exists.side_effect = [False, True]
    assert detect_platform() == "omarchy"


def test_omarchy_defaults_use_native_hosts_and_arch_php():
    config = platform_defaults("omarchy", Path("/home/test"))
    assert config["hosts"] == {"file": "/etc/hosts", "mode": "local"}
    assert config["php"]["ini_file"] == "/etc/php/php.ini"
    assert config["php"]["fpm_service"] == "php-fpm"
    assert config["php"]["fpm_listen"] == "unix:/run/php-fpm/php-fpm.sock"
