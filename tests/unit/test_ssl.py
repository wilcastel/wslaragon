"""Tests for SSL manager module"""
import subprocess
import base64
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest


def _get_ssl_manager_class():
    from wslaragon.services.ssl import SSLManager
    return SSLManager


class TestSSLManagerInit:
    """Test suite for SSLManager.__init__"""

    @pytest.fixture
    def ssl_manager(self, mock_config):
        from wslaragon.services.ssl import SSLManager
        return SSLManager(mock_config)

    def test_init_sets_config(self, ssl_manager):
        """Test that init sets config attribute"""
        assert ssl_manager.config is not None

    def test_init_sets_ssl_dir(self, ssl_manager):
        """Test that init sets ssl_dir"""
        assert ssl_manager.ssl_dir is not None

    def test_init_sets_ca_file(self, ssl_manager):
        """Test that init sets ca_file"""
        assert ssl_manager.ca_file is not None

    def test_init_sets_ca_key(self, ssl_manager):
        """Test that init sets ca_key"""
        assert ssl_manager.ca_key is not None

    def test_init_sets_windows_hosts(self, ssl_manager):
        """Test that init sets windows_hosts"""
        assert ssl_manager.windows_hosts is not None


class TestSSLManagerEnsureDirs:
    """Test suite for _ensure_dirs method"""

    @pytest.fixture
    def ssl_manager(self, mock_config, tmp_path):
        from wslaragon.services.ssl import SSLManager
        config = mock_config
        ssl_dir = tmp_path / "ssl"
        config.get.side_effect = lambda key, default=None: {
            "ssl.dir": str(ssl_dir),
            "ssl.ca_file": str(ssl_dir / "rootCA.pem"),
            "ssl.ca_key": str(ssl_dir / "rootCA-key.pem"),
            "windows.hosts_file": "/mnt/c/Windows/System32/drivers/etc/hosts",
        }.get(key, default)
        return SSLManager(config)

    def test_ensure_dirs_creates_ssl_dir(self, ssl_manager):
        """Test that _ensure_dirs creates SSL directory"""
        assert ssl_manager.ssl_dir.exists()


class TestSSLManagerIsMkcertInstalled:
    """Test suite for is_mkcert_installed method"""

    @pytest.fixture
    def ssl_manager(self, mock_config):
        from wslaragon.services.ssl import SSLManager
        return SSLManager(mock_config)

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_is_mkcert_installed_returns_true(self, mock_run, ssl_manager):
        """Test is_mkcert_installed returns True when installed"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = ssl_manager.is_mkcert_installed()
        
        assert result is True
        mock_run.assert_called_with(['mkcert', '-version'], capture_output=True, text=True)

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_is_mkcert_installed_returns_false(self, mock_run, ssl_manager):
        """Test is_mkcert_installed returns False when not installed"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = ssl_manager.is_mkcert_installed()
        
        assert result is False

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_is_mkcert_installed_returns_false_on_exception(self, mock_run, ssl_manager):
        """Test is_mkcert_installed returns False on exception"""
        mock_run.side_effect = Exception("Command not found")

        result = ssl_manager.is_mkcert_installed()
        
        assert result is False


class TestSSLManagerInstallMkcert:
    """Test suite for install_mkcert method"""

    @pytest.fixture
    def ssl_manager(self, mock_config):
        from wslaragon.services.ssl import SSLManager
        return SSLManager(mock_config)

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_install_mkcert_success(self, mock_run, ssl_manager):
        """Test install_mkcert succeeds"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = ssl_manager.install_mkcert()
        
        assert result is True
        assert mock_run.call_count >= 3

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_install_mkcert_returns_false_on_failure(self, mock_run, ssl_manager):
        """Test install_mkcert returns False on failure"""
        mock_run.side_effect = Exception("Download failed")

        result = ssl_manager.install_mkcert()
        
        assert result is False


class TestSSLManagerCreateCA:
    """Test suite for create_ca method"""

    @pytest.fixture
    def ssl_manager(self, mock_config):
        from wslaragon.services.ssl import SSLManager
        return SSLManager(mock_config)

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_create_ca_success(self, mock_run, ssl_manager, tmp_path):
        """Test create_ca succeeds"""
        ssl_manager.is_mkcert_installed = MagicMock(return_value=True)
        ssl_manager._get_caroot_path = MagicMock(return_value=str(tmp_path))
        mock_run.return_value = MagicMock(returncode=0)
        
        (tmp_path / "rootCA.pem").write_text("cert")
        (tmp_path / "rootCA-key.pem").write_text("key")
        
        ssl_manager.ssl_dir = tmp_path
        ssl_manager.ca_file = tmp_path / "rootCA.pem"
        ssl_manager.ca_key = tmp_path / "rootCA-key.pem"

        result = ssl_manager.create_ca()
        
        assert result is True

    def test_create_ca_installs_mkcert_if_needed(self, ssl_manager):
        """Test create_ca installs mkcert if not present"""
        ssl_manager.is_mkcert_installed = MagicMock(return_value=False)
        ssl_manager.install_mkcert = MagicMock(return_value=False)

        result = ssl_manager.create_ca()
        
        assert result is False

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_create_ca_returns_false_when_no_caroot(self, mock_run, ssl_manager):
        """Test create_ca returns False when CAROOT not found"""
        ssl_manager.is_mkcert_installed = MagicMock(return_value=True)
        ssl_manager._get_caroot_path = MagicMock(return_value=None)

        result = ssl_manager.create_ca()
        
        assert result is False

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_create_ca_returns_false_on_exception(self, mock_run, ssl_manager, tmp_path):
        """Test create_ca returns False on exception"""
        ssl_manager.is_mkcert_installed = MagicMock(return_value=True)
        ssl_manager._get_caroot_path = MagicMock(return_value=str(tmp_path))
        mock_run.side_effect = Exception("Command failed")
        
        (tmp_path / "rootCA.pem").write_text("cert")
        
        ssl_manager.ssl_dir = tmp_path
        ssl_manager.ca_file = tmp_path / "rootCA.pem"
        ssl_manager.ca_key = tmp_path / "rootCA-key.pem"

        result = ssl_manager.create_ca()
        
        assert result is False

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_create_ca_copies_ca_files(self, mock_run, ssl_manager, tmp_path):
        """Test create_ca copies CA files successfully"""
        ssl_manager.is_mkcert_installed = MagicMock(return_value=True)
        
        caroot_dir = tmp_path / "caroot"
        caroot_dir.mkdir()
        (caroot_dir / "rootCA.pem").write_text("ca-cert")
        (caroot_dir / "rootCA-key.pem").write_text("ca-key")
        
        ssl_dir = tmp_path/ "ssl"
        ssl_dir.mkdir()
        
        ssl_manager._get_caroot_path = MagicMock(return_value=str(caroot_dir))
        mock_run.return_value = MagicMock(returncode=0)
        
        ssl_manager.ssl_dir = ssl_dir
        ssl_manager.ca_file = ssl_dir / "rootCA.pem"
        ssl_manager.ca_key = ssl_dir / "rootCA-key.pem"

        result = ssl_manager.create_ca()
        
        assert result is True


class TestSSLManagerGetCarootPath:
    """Test suite for _get_caroot_path method"""

    @pytest.fixture
    def ssl_manager(self, mock_config):
        from wslaragon.services.ssl import SSLManager
        return SSLManager(mock_config)

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_get_caroot_path_returns_path(self, mock_run, ssl_manager):
        """Test _get_caroot_path returns path"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "/home/user/.local/share/mkcert\n"
        mock_run.return_value = mock_result

        result = ssl_manager._get_caroot_path()
        
        assert result == "/home/user/.local/share/mkcert"

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_get_caroot_path_returns_none_on_failure(self, mock_run, ssl_manager):
        """Test _get_caroot_path returns None on failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = ssl_manager._get_caroot_path()
        
        assert result is None

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_get_caroot_path_returns_none_on_exception(self, mock_run, ssl_manager):
        """Test _get_caroot_path returns None on exception"""
        mock_run.side_effect = Exception("Command failed")

        result = ssl_manager._get_caroot_path()
        
        assert result is None


class TestSSLManagerGenerateCertificate:
    """Test suite for generate_certificate method"""

    @pytest.fixture
    def ssl_manager(self, mock_config, tmp_path):
        from wslaragon.services.ssl import SSLManager
        config = mock_config
        ssl_dir = tmp_path / "ssl"
        ssl_dir.mkdir(parents=True)
        config.get.side_effect = lambda key, default=None: {
            "ssl.dir": str(ssl_dir),
            "ssl.ca_file": str(ssl_dir / "rootCA.pem"),
            "ssl.ca_key": str(ssl_dir / "rootCA-key.pem"),
            "windows.hosts_file": "/mnt/c/Windows/System32/drivers/etc/hosts",
        }.get(key, default)
        return SSLManager(config)

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_generate_certificate_success(self, mock_run, ssl_manager, tmp_path):
        """Test generate_certificate succeeds"""
        ssl_manager.is_mkcert_installed = MagicMock(return_value=True)
        mock_run.return_value = MagicMock(returncode=0)
        
        ssl_dir = tmp_path / "ssl"
        (ssl_dir / "example.test.pem").write_text("cert")
        (ssl_dir / "example.test-key.pem").write_text("key")

        result = ssl_manager.generate_certificate("example.test")
        
        assert result is True

    def test_generate_certificate_returns_false_when_no_mkcert(self, ssl_manager):
        """Test generate_certificate returns False when mkcert not installed"""
        ssl_manager.is_mkcert_installed = MagicMock(return_value=False)

        result = ssl_manager.generate_certificate("example.test")
        
        assert result is False

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_generate_certificate_with_additional_domains(self, mock_run, ssl_manager, tmp_path):
        """Test generate_certificate handles additional domains"""
        ssl_manager.is_mkcert_installed = MagicMock(return_value=True)
        mock_run.return_value = MagicMock(returncode=0)
        
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        (ssl_dir / "example.test.pem").write_text("cert")
        (ssl_dir / "example.test-key.pem").write_text("key")

        result = ssl_manager.generate_certificate("example.test", ["www.example.test"])
        
        assert isinstance(result, bool)

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_generate_certificate_returns_false_on_exception(self, mock_run, ssl_manager):
        """Test generate_certificate returns False on exception"""
        ssl_manager.is_mkcert_installed = MagicMock(return_value=True)
        mock_run.side_effect = Exception("Command failed")

        result = ssl_manager.generate_certificate("example.test")
        
        assert result is False

    @patch('wslaragon.services.ssl.subprocess.run')
    @patch('wslaragon.services.ssl.Path')
    def test_generate_certificate_moves_files(self, mock_path_class, mock_run, ssl_manager, tmp_path):
        """Test generate_certificate moves generated files to ssl_dir"""
        ssl_manager.is_mkcert_installed = MagicMock(return_value=True)
        mock_run.return_value = MagicMock(returncode=0)
        
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        (ssl_dir / "example.test.pem").write_text("cert")
        (ssl_dir / "example.test-key.pem").write_text("key")

        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.name = "example.test.pem"
        mock_file_instance = MagicMock()
        mock_file_instance.glob.return_value = iter([mock_file])
        mock_path_class.return_value = mock_file_instance

        result = ssl_manager.generate_certificate("example.test")
        
        assert result is True


class TestSSLManagerGenerateCert:
    """Test suite for generate_cert method"""

    @pytest.fixture
    def ssl_manager(self, mock_config):
        from wslaragon.services.ssl import SSLManager
        return SSLManager(mock_config)

    def test_generate_cert_returns_success(self, ssl_manager):
        """Test generate_cert returns success dict"""
        ssl_manager.generate_certificate = MagicMock(return_value=True)
        ssl_manager.add_to_windows_hosts = MagicMock(return_value=True)

        result = ssl_manager.generate_cert("example.test")
        
        assert result['success'] is True

    def test_generate_cert_returns_failure(self, ssl_manager):
        """Test generate_cert returns failure dict"""
        ssl_manager.generate_certificate = MagicMock(return_value=False)

        result = ssl_manager.generate_cert("example.test")
        
        assert result['success'] is False
        assert 'error' in result

    def test_generate_cert_calls_add_to_windows_hosts(self, ssl_manager):
        """Test generate_cert calls add_to_windows_hosts"""
        ssl_manager.generate_certificate = MagicMock(return_value=True)
        ssl_manager.add_to_windows_hosts = MagicMock(return_value=True)

        ssl_manager.generate_cert("example.test")
        
        ssl_manager.add_to_windows_hosts.assert_called_once_with("example.test")

    def test_generate_cert_handles_exception(self, ssl_manager):
        """Test generate_cert handles exceptions"""
        ssl_manager.generate_certificate = MagicMock(side_effect=Exception("Error"))

        result = ssl_manager.generate_cert("example.test")
        
        assert result['success'] is False
        assert 'error' in result


class TestSSLManagerAddToWindowsHosts:
    """Test suite for add_to_windows_hosts method"""

    @pytest.fixture
    def ssl_manager(self, mock_config, tmp_path):
        from wslaragon.services.ssl import SSLManager
        config = mock_config
        ssl_dir = tmp_path / "ssl"
        ssl_dir.mkdir(parents=True)
        config.get.side_effect = lambda key, default=None: {
            "ssl.dir": str(ssl_dir),
            "ssl.ca_file": str(ssl_dir / "rootCA.pem"),
            "ssl.ca_key": str(ssl_dir / "rootCA-key.pem"),
            "windows.hosts_file": str(tmp_path / "hosts"),
        }.get(key, default)
        return SSLManager(config)

    def test_add_to_windows_hosts_returns_true_if_exists(self, ssl_manager, tmp_path):
        """Test add_to_windows_hosts returns True if domain already exists"""
        hosts_file = tmp_path / "hosts"
        hosts_file.write_text("127.0.0.1 example.test")
        ssl_manager.windows_hosts = hosts_file

        result = ssl_manager.add_to_windows_hosts("example.test")
        
        assert result is True

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_add_to_windows_hosts_calls_powershell(self, mock_run, ssl_manager, tmp_path):
        """Test add_to_windows_hosts calls PowerShell"""
        hosts_file = tmp_path / "hosts"
        hosts_file.write_text("")
        ssl_manager.windows_hosts = hosts_file
        
        mock_run.return_value = MagicMock(returncode=0)

        result = ssl_manager.add_to_windows_hosts("example.test")
        
        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert 'powershell.exe' in call_args

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_add_to_windows_hosts_returns_false_on_exception(self, mock_run, ssl_manager, tmp_path):
        """Test add_to_windows_hosts returns False on exception"""
        hosts_file = tmp_path / "hosts"
        hosts_file.write_text("")
        ssl_manager.windows_hosts = hosts_file
        
        mock_run.side_effect = Exception("PowerShell failed")

        result = ssl_manager.add_to_windows_hosts("example.test")
        
        assert result is False


class TestSSLManagerRemoveFromWindowsHosts:
    """Test suite for remove_from_windows_hosts method"""

    @pytest.fixture
    def ssl_manager(self, mock_config, tmp_path):
        from wslaragon.services.ssl import SSLManager
        config = mock_config
        ssl_dir = tmp_path / "ssl"
        ssl_dir.mkdir(parents=True)
        config.get.side_effect = lambda key, default=None: {
            "ssl.dir": str(ssl_dir),
            "ssl.ca_file": str(ssl_dir / "rootCA.pem"),
            "ssl.ca_key": str(ssl_dir / "rootCA-key.pem"),
            "windows.hosts_file": str(tmp_path / "hosts"),
        }.get(key, default)
        return SSLManager(config)

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_remove_from_windows_hosts_success(self, mock_run, ssl_manager):
        """Test remove_from_windows_hosts succeeds"""
        mock_run.return_value = MagicMock(returncode=0)

        result = ssl_manager.remove_from_windows_hosts("example.test")
        
        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert 'powershell.exe' in call_args

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_remove_from_windows_hosts_returns_false_on_exception(self, mock_run,ssl_manager):
        """Test remove_from_windows_hosts returns False on exception"""
        mock_run.side_effect = Exception("PowerShell failed")

        result = ssl_manager.remove_from_windows_hosts("example.test")
        
        assert result is False


class TestSSLManagerListCertificates:
    """Test suite for list_certificates method"""

    @pytest.fixture
    def ssl_manager(self, mock_config, tmp_path):
        from wslaragon.services.ssl import SSLManager
        config = mock_config
        ssl_dir = tmp_path / "ssl"
        ssl_dir.mkdir(parents=True)
        config.get.side_effect = lambda key, default=None: {
            "ssl.dir": str(ssl_dir),
            "ssl.ca_file": str(ssl_dir / "rootCA.pem"),
            "ssl.ca_key": str(ssl_dir / "rootCA-key.pem"),
            "windows.hosts_file": "/mnt/c/Windows/System32/drivers/etc/hosts",
        }.get(key, default)
        return SSLManager(config)

    def test_list_certificates_returns_list(self, ssl_manager, tmp_path):
        """Test list_certificates returns certificate list"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        (ssl_dir / "site1.test.pem").write_text("cert1")
        (ssl_dir / "site1.test-key.pem").write_text("key1")
        (ssl_dir / "site2.test.pem").write_text("cert2")
        
        ssl_manager.get_certificate_info = MagicMock(side_effect=lambda domain: {'domain': domain})

        result = ssl_manager.list_certificates()
        
        assert len(result) == 2

    def test_list_certificates_excludes_key_files(self, ssl_manager, tmp_path):
        """Test list_certificates excludes key files"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        (ssl_dir / "site.test.pem").write_text("cert")
        (ssl_dir / "site.test-key.pem").write_text("key")
        
        ssl_manager.get_certificate_info = MagicMock(return_value={'domain': 'site.test'})

        result = ssl_manager.list_certificates()
        
        assert len(result) == 1
        ssl_manager.get_certificate_info.assert_called_once_with('site.test')

    def test_list_certificates_returns_empty_when_none(self, ssl_manager, tmp_path):
        """Test list_certificates returns empty list when no certs"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir

        result = ssl_manager.list_certificates()
        
        assert result == []


class TestSSLManagerRevokeCertificate:
    """Test suite for revoke_certificate method"""

    @pytest.fixture
    def ssl_manager(self, mock_config, tmp_path):
        from wslaragon.services.ssl import SSLManager
        config = mock_config
        ssl_dir = tmp_path / "ssl"
        ssl_dir.mkdir(parents=True)
        config.get.side_effect = lambda key, default=None: {
            "ssl.dir": str(ssl_dir),
            "ssl.ca_file": str(ssl_dir / "rootCA.pem"),
            "ssl.ca_key": str(ssl_dir / "rootCA-key.pem"),
            "windows.hosts_file": "/mnt/c/Windows/System32/drivers/etc/hosts",
        }.get(key, default)
        return SSLManager(config)

    def test_revoke_certificate_removes_files(self, ssl_manager, tmp_path):
        """Test revoke_certificate removes certificate files"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        cert_file = ssl_dir / "example.test.pem"
        key_file = ssl_dir / "example.test-key.pem"
        cert_file.write_text("cert")
        key_file.write_text("key")
        
        ssl_manager.remove_from_windows_hosts = MagicMock(return_value=True)

        result = ssl_manager.revoke_certificate("example.test")
        
        assert result is True
        assert not cert_file.exists()
        assert not key_file.exists()

    def test_revoke_certificate_returns_false_when_no_files(self, ssl_manager, tmp_path):
        """Test revoke_certificate returns False when no files exist"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        ssl_manager.remove_from_windows_hosts = MagicMock(return_value=True)

        result = ssl_manager.revoke_certificate("nonexistent")
        
        assert result is False

    def test_revoke_certificate_calls_remove_from_hosts(self, ssl_manager, tmp_path):
        """Test revoke_certificate calls remove_from_windows_hosts"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        cert_file = ssl_dir / "example.test.pem"
        key_file = ssl_dir / "example.test-key.pem"
        cert_file.write_text("cert")
        key_file.write_text("key")
        
        ssl_manager.remove_from_windows_hosts = MagicMock(return_value=True)

        ssl_manager.revoke_certificate("example.test")
        
        ssl_manager.remove_from_windows_hosts.assert_called_once_with("example.test")

    def test_revoke_certificate_returns_false_on_exception(self, ssl_manager, tmp_path):
        """Test revoke_certificate returns False on exception"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        cert_file = ssl_dir / "example.test.pem"
        key_file = ssl_dir / "example.test-key.pem"
        cert_file.write_text("cert")
        key_file.write_text("key")
        
        ssl_manager.remove_from_windows_hosts = MagicMock(side_effect=Exception("Error"))

        result = ssl_manager.revoke_certificate("example.test")
        
        assert result is False


class TestSSLManagerGetCertificateInfo:
    """Test suite for get_certificate_info method"""

    @pytest.fixture
    def ssl_manager(self, mock_config, tmp_path):
        from wslaragon.services.ssl import SSLManager
        config = mock_config
        ssl_dir = tmp_path / "ssl"
        ssl_dir.mkdir(parents=True)
        config.get.side_effect = lambda key, default=None: {
            "ssl.dir": str(ssl_dir),
            "ssl.ca_file": str(ssl_dir / "rootCA.pem"),
            "ssl.ca_key": str(ssl_dir / "rootCA-key.pem"),
            "windows.hosts_file": "/mnt/c/Windows/System32/drivers/etc/hosts",
        }.get(key, default)
        return SSLManager(config)

    def test_get_certificate_info_returns_none_when_no_file(self, ssl_manager, tmp_path):
        """Test get_certificate_info returns None when file doesn't exist"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir

        result = ssl_manager.get_certificate_info("nonexistent")
        
        assert result is None

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_get_certificate_info_parses_output(self, mock_run, ssl_manager, tmp_path):
        """Test get_certificate_info parses openssl output"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        cert_file = ssl_dir / "example.test.pem"
        cert_file.write_text("cert")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """Certificate:
    Subject: CN=example.test
    Issuer: CN=mkcert development CA
    Not Before: Jan  1 00:00:00 2024 GMT
    Not After : Dec 31 23:59:59 2024 GMT
"""
        mock_run.return_value = mock_result

        result = ssl_manager.get_certificate_info("example.test")
        
        assert result is not None
        assert 'subject' in result
        assert 'issuer' in result

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_get_certificate_info_returns_none_on_error(self, mock_run, ssl_manager, tmp_path):
        """Test get_certificate_info returns None on openssl error"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        cert_file = ssl_dir / "example.test.pem"
        cert_file.write_text("cert")
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = ssl_manager.get_certificate_info("example.test")
        
        assert result is None

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_get_certificate_info_returns_none_on_exception(self, mock_run, ssl_manager, tmp_path):
        """Test get_certificate_info returns None on exception"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        cert_file = ssl_dir / "example.test.pem"
        cert_file.write_text("cert")
        
        mock_run.side_effect = Exception("OpenSSL failed")

        result = ssl_manager.get_certificate_info("example.test")
        
        assert result is None

    @patch('wslaragon.services.ssl.subprocess.run')
    def test_get_certificate_info_parses_all_fields(self, mock_run, ssl_manager, tmp_path):
        """Test get_certificate_info parses all certificate fields"""
        ssl_dir = tmp_path / "ssl"
        ssl_manager.ssl_dir = ssl_dir
        
        cert_file = ssl_dir / "example.test.pem"
        cert_file.write_text("cert")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """Certificate:
    Subject: CN=example.test
    Issuer: CN=mkcert development CA
    Not Before: Jan  1 00:00:00 2024 GMT
    Not After : Dec  31 23:59:59 2024 GMT
"""
        mock_run.return_value = mock_result

        result = ssl_manager.get_certificate_info("example.test")
        
        assert result is not None
        assert result['subject'] == 'Subject: CN=example.test'
        assert result['issuer'] == 'Issuer: CN=mkcert development CA'
        assert 'valid_from' in result
        assert 'valid_until' in result


class TestSSLManagerSetupSSLForSite:
    """Test suite for setup_ssl_for_site method"""

    @pytest.fixture
    def ssl_manager(self, mock_config):
        from wslaragon.services.ssl import SSLManager
        return SSLManager(mock_config)

    def test_setup_ssl_for_site_returns_success(self, ssl_manager):
        """Test setup_ssl_for_site returns success dict"""
        ssl_manager.generate_certificate = MagicMock(return_value=True)
        ssl_manager.add_to_windows_hosts = MagicMock(return_value=True)
        ssl_manager.get_certificate_info = MagicMock(return_value={'subject': 'test'})

        result = ssl_manager.setup_ssl_for_site("myapp", ".test")
        
        assert result['success'] is True
        assert 'domain' in result
        assert 'certificate' in result

    def test_setup_ssl_for_site_returns_failure_on_cert_error(self, ssl_manager):
        """Test setup_ssl_for_site returns failure on certificate error"""
        ssl_manager.generate_certificate = MagicMock(return_value=False)

        result = ssl_manager.setup_ssl_for_site("myapp", ".test")
        
        assert result['success'] is False
        assert 'error' in result

    def test_setup_ssl_for_site_returns_failure_on_hosts_error(self, ssl_manager):
        """Test setup_ssl_for_site returns failure on hosts file error"""
        ssl_manager.generate_certificate = MagicMock(return_value=True)
        ssl_manager.add_to_windows_hosts = MagicMock(return_value=False)

        result = ssl_manager.setup_ssl_for_site("myapp", ".test")
        
        assert result['success'] is False
        assert 'error' in result

    def test_setup_ssl_for_site_handles_exception(self, ssl_manager):
        """Test setup_ssl_for_site handles exceptions"""
        ssl_manager.generate_certificate = MagicMock(side_effect=Exception("Error"))

        result = ssl_manager.setup_ssl_for_site("myapp", ".test")
        
        assert result['success'] is False
        assert 'error' in result