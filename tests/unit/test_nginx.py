"""Tests for Nginx manager module"""
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import pytest


class TestNginxManagerInit:
    """Test suite for NginxManager.__init__"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    def test_init_sets_config(self, nginx_manager):
        """Test that init sets config attribute"""
        assert nginx_manager.config is not None

    def test_init_sets_config_dir(self, nginx_manager):
        """Test that init sets config_dir"""
        assert nginx_manager.config_dir is not None

    def test_init_sets_sites_available(self, nginx_manager):
        """Test that init sets sites_available"""
        assert nginx_manager.sites_available is not None

    def test_init_sets_sites_enabled(self, nginx_manager):
        """Test that init sets sites_enabled"""
        assert nginx_manager.sites_enabled is not None


class TestNginxManagerTestConfig:
    """Test suite for test_config method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_test_config_returns_true_on_success(self, mock_run, nginx_manager):
        """Test test_config returns True when nginx config is valid"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = nginx_manager.test_config()
        
        assert result is True
        mock_run.assert_called_with(
            ['sudo', 'nginx', '-t'],
            capture_output=True, text=True
        )

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_test_config_returns_false_on_failure(self, mock_run, nginx_manager):
        """Test test_config returns False when nginx config is invalid"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "nginx: configuration file test failed"
        mock_run.return_value = mock_result

        result = nginx_manager.test_config()
        
        assert result is False

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_test_config_returns_false_on_exception(self, mock_run, nginx_manager):
        """Test test_config returns False on exception"""
        mock_run.side_effect = Exception("Command failed")

        result = nginx_manager.test_config()
        
        assert result is False


class TestNginxManagerReload:
    """Test suite for reload method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_reload_returns_true_on_success(self, mock_run, nginx_manager):
        """Test reload returns True on successful reload"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = nginx_manager.reload()
        
        assert result is True
        mock_run.assert_called_with(
            ['sudo', 'systemctl', 'reload', 'nginx'],
            capture_output=True, text=True
        )

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_reload_returns_false_on_failure(self, mock_run, nginx_manager):
        """Test reload returns False on failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = nginx_manager.reload()
        
        assert result is False

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_reload_returns_false_on_exception(self, mock_run, nginx_manager):
        """Test reload returns False on exception"""
        mock_run.side_effect = Exception("Command failed")

        result = nginx_manager.reload()
        
        assert result is False


class TestNginxManagerRestart:
    """Test suite for restart method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_restart_returns_true_on_success(self, mock_run, nginx_manager):
        """Test restart returns True on successful restart"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = nginx_manager.restart()
        
        assert result is True
        mock_run.assert_called_with(
            ['sudo', 'systemctl', 'restart', 'nginx'],
            capture_output=True, text=True
        )

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_restart_returns_false_on_failure(self, mock_run, nginx_manager):
        """Test restart returns False on failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = nginx_manager.restart()
        
        assert result is False

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_restart_returns_false_on_exception(self, mock_run, nginx_manager):
        """Test restart returns False on exception"""
        mock_run.side_effect = Exception("Command failed")

        result = nginx_manager.restart()
        
        assert result is False


class TestNginxManagerCreateSiteConfig:
    """Test suite for create_site_config method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    def test_create_site_config_basic(self, nginx_manager):
        """Test basic site config generation"""
        config = nginx_manager.create_site_config("myapp", "/var/www/myapp")
        
        assert "server_name myapp.test" in config
        assert "listen 80" in config
        assert "root /var/www/myapp" in config

    def test_create_site_config_with_php(self, nginx_manager):
        """Test PHP site config generation"""
        config = nginx_manager.create_site_config("myapp", "/var/www/myapp", php=True)
        
        assert "fastcgi_pass" in config
        assert "php8.3-fpm.sock" in config

    def test_create_site_config_without_php(self, nginx_manager):
        """Test static site config generation"""
        config = nginx_manager.create_site_config("myapp", "/var/www/myapp", php=False)
        
        assert "fastcgi_pass" not in config
        assert "root /var/www/myapp" in config

    def test_create_site_config_with_ssl(self, nginx_manager):
        """Test SSL site config generation"""
        config = nginx_manager.create_site_config("myapp", "/var/www/myapp", ssl=True)
        
        assert "listen 443 ssl" in config
        assert "ssl_certificate" in config
        assert "listen 80" in config  # HTTP redirect block
        assert "return 301" in config

    def test_create_site_config_without_ssl(self, nginx_manager):
        """Test non-SSL site config generation"""
        config = nginx_manager.create_site_config("myapp", "/var/www/myapp", ssl=False)
        
        assert "listen 443" not in config
        assert "ssl_certificate" not in config
        assert "server_name myapp.test" in config

    def test_create_site_config_with_proxy_port(self, nginx_manager):
        """Test proxy config generation"""
        config = nginx_manager.create_site_config("myapp", "/var/www/myapp", proxy_port=3000)
        
        assert "proxy_pass http://127.0.0.1:3000" in config
        assert "proxy_http_version 1.1" in config
        assert "proxy_set_header" in config

    def test_create_site_config_includes_security_headers(self, nginx_manager):
        """Test that security headers are included"""
        config = nginx_manager.create_site_config("myapp", "/var/www/myapp")
        
        assert "X-Frame-Options" in config
        assert "X-XSS-Protection" in config
        assert "X-Content-Type-Options" in config

    def test_create_site_config_ssl_includes_hsts(self, nginx_manager):
        """Test that HSTS header is included in SSL config"""
        config = nginx_manager.create_site_config("myapp", "/var/www/myapp", ssl=True)
        
        assert "Strict-Transport-Security" in config

    def test_create_site_config_includes_client_max_body_size(self, nginx_manager):
        """Test that client_max_body_size is included"""
        config = nginx_manager.create_site_config("myapp", "/var/www/myapp")
        
        assert "client_max_body_size 128M" in config


class TestNginxManagerAddSite:
    """Test suite for add_site method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    @patch('wslaragon.services.nginx.subprocess.Popen')
    def test_add_site_returns_true_on_success(self, mock_popen, nginx_manager):
        """Test add_site returns True on successful creation"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process
        
        nginx_manager.enable_site = MagicMock(return_value=(True, None))

        result, error = nginx_manager.add_site("myapp", "/var/www/myapp")
        
        assert result is True
        assert error is None

    @patch('wslaragon.services.nginx.subprocess.Popen')
    def test_add_site_returns_false_on_popen_failure(self, mock_popen, nginx_manager):
        """Test add_site returns False when Popen fails"""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"failed")
        mock_popen.return_value = mock_process

        result, error = nginx_manager.add_site("myapp", "/var/www/myapp")
        
        assert result is False
        assert error is not None

    @patch('wslaragon.services.nginx.subprocess.Popen')
    def test_add_site_calls_enable_site(self, mock_popen, nginx_manager):
        """Test add_site calls enable_site after creating config"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process
        
        nginx_manager.enable_site = MagicMock(return_value=(True, None))

        nginx_manager.add_site("myapp", "/var/www/myapp")
        
        nginx_manager.enable_site.assert_called_once_with("myapp")

    @patch('wslaragon.services.nginx.subprocess.Popen')
    def test_add_site_returns_false_when_enable_fails(self, mock_popen, nginx_manager):
        """Test add_site returns False when enable_site fails"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process
        
        nginx_manager.enable_site = MagicMock(return_value=(False, "Enable failed"))

        result, error = nginx_manager.add_site("myapp", "/var/www/myapp")
        
        assert result is False
        assert error == "Enable failed"

    @patch('wslaragon.services.nginx.subprocess.Popen')
    def test_add_site_returns_false_on_exception(self, mock_popen, nginx_manager):
        """Test add_site returns False on exception"""
        mock_popen.side_effect = Exception("Unexpected error")

        result, error = nginx_manager.add_site("myapp", "/var/www/myapp")
        
        assert result is False
        assert "Unexpected error" in error


class TestNginxManagerEnableSite:
    """Test suite for enable_site method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_enable_site_returns_true_on_success(self, mock_run, nginx_manager):
        """Test enable_site returns True on successful enabling"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        nginx_manager.test_config = MagicMock(return_value=True)
        nginx_manager.reload = MagicMock(return_value=True)

        result, error = nginx_manager.enable_site("myapp")
        
        assert result is True
        assert error is None

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_enable_site_returns_false_on_test_failure(self, mock_run, nginx_manager):
        """Test enable_site returns False when config test fails"""
        mock_result = MagicMock()
        mock_result.stderr = "configuration test failed"
        mock_run.return_value = mock_result
        
        nginx_manager.test_config = MagicMock(return_value=False)

        result, error = nginx_manager.enable_site("myapp")
        
        assert result is False
        assert "configuration test failed" in error

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_enable_site_returns_false_on_reload_failure(self, mock_run, nginx_manager):
        """Test enable_site returns False when reload fails"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        nginx_manager.test_config = MagicMock(return_value=True)
        nginx_manager.reload = MagicMock(return_value=False)

        result, error = nginx_manager.enable_site("myapp")
        
        assert result is False
        assert "reload" in error.lower()

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_enable_site_returns_false_on_called_process_error(self, mock_run, nginx_manager):
        """Test enable_site returns False on CalledProcessError"""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ln', stderr='Permission denied')

        result, error = nginx_manager.enable_site("myapp")
        
        assert result is False
        assert "Process error" in error

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_enable_site_returns_false_on_exception(self, mock_run, nginx_manager):
        """Test enable_site returns False on general exception"""
        mock_run.side_effect = Exception("Unexpected error")

        result, error = nginx_manager.enable_site("myapp")
        
        assert result is False
        assert "Unexpected error" in error


class TestNginxManagerDisableSite:
    """Test suite for disable_site method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_disable_site_returns_true_on_success(self, mock_run, nginx_manager):
        """Test disable_site returns True on successful disabling"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        nginx_manager.reload = MagicMock(return_value=True)

        result = nginx_manager.disable_site("myapp")
        
        assert result is True

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_disable_site_returns_false_on_exception(self, mock_run, nginx_manager):
        """Test disable_site returns False on exception"""
        mock_run.side_effect = Exception("Error")

        result = nginx_manager.disable_site("myapp")
        
        assert result is False


class TestNginxManagerRemoveSite:
    """Test suite for remove_site method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_remove_site_calls_disable_first(self, mock_run, nginx_manager):
        """Test remove_site disables site before removing"""
        nginx_manager.disable_site = MagicMock(return_value=True)
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = nginx_manager.remove_site("myapp")
        
        assert result is True
        nginx_manager.disable_site.assert_called_once_with("myapp")

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_remove_site_returns_false_on_exception(self, mock_run, nginx_manager):
        """Test remove_site returns False on exception"""
        nginx_manager.disable_site = MagicMock(return_value=True)
        mock_run.side_effect = Exception("Remove failed")

        result = nginx_manager.remove_site("myapp")
        
        assert result is False


class TestNginxManagerListSites:
    """Test suite for list_sites method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    def test_list_sites_returns_available_sites(self, nginx_manager, tmp_path):
        """Test list_sites returns available sites"""
        sites_available = tmp_path / "sites-available"
        sites_available.mkdir(parents=True)
        sites_enabled = tmp_path / "sites-enabled"
        sites_enabled.mkdir(parents=True)
        
        nginx_manager.sites_available = sites_available
        nginx_manager.sites_enabled = sites_enabled
        
        (sites_available / "site1.test.conf").write_text("server {}")
        (sites_available / "site2.test.conf").write_text("server {}")
        
        result = nginx_manager.list_sites()
        
        assert "site1.test" in result
        assert "site2.test" in result
        assert result["site1.test"]["available"] is True

    def test_list_sites_detects_enabled_sites(self, nginx_manager, tmp_path):
        """Test list_sites detects enabled sites"""
        sites_available = tmp_path / "sites-available"
        sites_available.mkdir(parents=True)
        sites_enabled = tmp_path / "sites-enabled"
        sites_enabled.mkdir(parents=True)
        
        nginx_manager.sites_available = sites_available
        nginx_manager.sites_enabled = sites_enabled
        
        (sites_available / "enabled.test.conf").write_text("server {}")
        (sites_enabled / "enabled.test.conf").symlink_to(sites_available / "enabled.test.conf")
        
        result = nginx_manager.list_sites()
        
        assert result["enabled.test"]["enabled"] is True

    def test_list_sites_returns_empty_dict_when_no_sites(self, nginx_manager, tmp_path):
        """Test list_sites returns empty dict when no sites exist"""
        sites_available = tmp_path / "sites-available"
        sites_available.mkdir(parents=True)
        sites_enabled = tmp_path / "sites-enabled"
        sites_enabled.mkdir(parents=True)
        
        nginx_manager.sites_available = sites_available
        nginx_manager.sites_enabled = sites_enabled
        
        result = nginx_manager.list_sites()
        
        assert result == {}


class TestNginxManagerGetSiteConfig:
    """Test suite for get_site_config method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    def test_get_site_config_returns_content(self, nginx_manager, tmp_path):
        """Test get_site_config returns config content"""
        sites_available = tmp_path / "sites-available"
        sites_available.mkdir(parents=True)
        
        nginx_manager.sites_available = sites_available
        
        config_content = "server { listen 80; }"
        (sites_available / "myapp.test.conf").write_text(config_content)
        
        result = nginx_manager.get_site_config("myapp.test")
        
        assert result == config_content

    def test_get_site_config_returns_none_when_not_found(self, nginx_manager, tmp_path):
        """Test get_site_config returns None when config doesn't exist"""
        sites_available = tmp_path / "sites-available"
        sites_available.mkdir(parents=True)
        
        nginx_manager.sites_available = sites_available
        
        result = nginx_manager.get_site_config("nonexistent")
        
        assert result is None

    def test_get_site_config_handles_exception(self, nginx_manager, tmp_path):
        """Test get_site_config returns None on exception"""
        sites_available = tmp_path / "sites-available"
        sites_available.mkdir(parents=True)
        
        nginx_manager.sites_available = sites_available
        config_file = sites_available / "myapp.conf"
        config_file.write_text("content")
        config_file.chmod(0o000)
        
        result = nginx_manager.get_site_config("myapp")
        
        assert result is None