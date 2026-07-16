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


class TestNginxManagerGetPhpFpmSocket:
    """Test suite for _get_php_fpm_socket helper"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    def test_returns_versioned_socket_when_present(self, nginx_manager):
        """Test _get_php_fpm_socket returns versioned path when it exists"""
        def exists_side_effect(path):
            return str(path) == '/run/php/php8.3-fpm.sock'

        with patch.object(Path, 'exists', exists_side_effect):
            socket = nginx_manager._get_php_fpm_socket()

        assert socket == '/run/php/php8.3-fpm.sock'

    def test_falls_back_to_generic_socket(self, nginx_manager):
        """Test _get_php_fpm_socket falls back to generic path"""
        def exists_side_effect(path):
            return str(path) == '/run/php/php-fpm.sock'

        with patch.object(Path, 'exists', exists_side_effect):
            socket = nginx_manager._get_php_fpm_socket()

        assert socket == '/run/php/php-fpm.sock'

    def test_raises_when_no_socket_exists(self, nginx_manager):
        """Test _get_php_fpm_socket raises when neither socket exists"""
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(RuntimeError):
                nginx_manager._get_php_fpm_socket()


class TestNginxManagerCreateSiteConfig:
    """Test suite for create_site_config method"""

    @pytest.fixture
    def nginx_manager(self, mock_config):
        from wslaragon.services.nginx import NginxManager
        return NginxManager(mock_config)

    @pytest.fixture(autouse=True)
    def mock_versioned_fpm_socket(self, nginx_manager):
        """Make PHP site-config tests see the versioned FPM socket."""
        nginx_manager._get_php_fpm_socket = MagicMock(
            return_value='/run/php/php8.3-fpm.sock'
        )

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

    def test_create_site_config_strips_tld_suffix(self, nginx_manager):
        """Test that a site name already including the TLD is normalized"""
        config = nginx_manager.create_site_config("myapp.test", "/var/www/myapp")

        assert "server_name myapp.test" in config
        assert "server_name myapp.test.test" not in config

    def test_create_site_config_with_api_proxies(self, nginx_manager):
        """Test that api_proxies generates proxy location blocks (used with proxy_port)"""
        config = nginx_manager.create_site_config(
            "myapp", "/var/www/myapp", proxy_port=3000,
            api_proxies={"/api": "https://backend.example.com:8443"}
        )

        assert "API proxy: /api -> https://backend.example.com:8443" in config
        assert "set $backend_api https://backend.example.com:8443;" in config
        assert "location /api/ {" in config
        assert "proxy_set_header Host backend.example.com" in config

    def test_create_site_config_with_api_proxies_default_scheme_and_port(self, nginx_manager):
        """Test api_proxies falls back to hostname-only backend without scheme/port"""
        config = nginx_manager.create_site_config(
            "myapp", "/var/www/myapp", astro_ssg=True,
            api_proxies={"/legacy": "backend-host"}
        )

        # When the backend URL has no scheme, urlparse() leaves scheme=''
        # so both backend_scheme and backend_port fall back consistently:
        # scheme defaults to 'https', and the port defaults to 443 to match it.
        assert "set $backend_legacy https://backend-host:443;" in config

    def test_create_site_config_astro_ssg(self, nginx_manager):
        """Test astro_ssg branch serves static files from document root"""
        config = nginx_manager.create_site_config(
            "myapp", "/var/www/myapp/dist", astro_ssg=True
        )

        assert "root /var/www/myapp/dist" in config
        assert "index index.html" in config
        assert "fastcgi_pass" not in config


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


class TestNginxManagerUpdateClientMaxBodySize:
    """Test suite for update_client_max_body_size"""

    @pytest.fixture
    def nginx_manager(self, mock_config, tmp_path):
        from wslaragon.services.nginx import NginxManager
        manager = NginxManager(mock_config)
        # Use a throwaway directory instead of the real /etc/nginx
        manager.config_dir = tmp_path / "nginx"
        return manager

    @patch('wslaragon.services.nginx.subprocess.Popen')
    @patch('wslaragon.services.nginx.subprocess.run')
    def test_update_client_max_body_size_success(self, mock_run, mock_popen, nginx_manager):
        """Test successful update writes drop-in, validates, persists, then reloads"""
        mock_run.return_value = MagicMock(returncode=0)
        write_process = MagicMock()
        write_process.communicate.return_value = ("", "")
        write_process.returncode = 0
        mock_popen.return_value = write_process

        nginx_manager.test_config = MagicMock(return_value=True)
        nginx_manager.reload = MagicMock(return_value=True)

        result = nginx_manager.update_client_max_body_size("1G")

        assert result is True
        nginx_manager.config.set.assert_called_once_with('nginx.client_max_body_size', '1G')
        nginx_manager.reload.assert_called_once()

    @patch('wslaragon.services.nginx.subprocess.Popen')
    @patch('wslaragon.services.nginx.subprocess.run')
    def test_update_client_max_body_size_rolls_back_on_invalid_config(self, mock_run, mock_popen, nginx_manager):
        """Test that a value nginx rejects is rolled back and never persisted"""
        mock_run.return_value = MagicMock(returncode=0)
        write_process = MagicMock()
        write_process.communicate.return_value = ("", "")
        write_process.returncode = 0
        mock_popen.return_value = write_process

        nginx_manager.test_config = MagicMock(return_value=False)
        nginx_manager.reload = MagicMock(return_value=True)

        result = nginx_manager.update_client_max_body_size("garbage")

        assert result is False
        nginx_manager.config.set.assert_not_called()
        nginx_manager.reload.assert_not_called()
        # No previous drop-in existed, so the rollback path must remove the bad one
        rm_calls = [c for c in mock_run.call_args_list if 'rm' in c[0][0]]
        assert len(rm_calls) == 1

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_update_client_max_body_size_fails_when_mkdir_fails(self, mock_run, nginx_manager):
        """Test that a failed sudo mkdir returns False without touching config"""
        mock_run.return_value = MagicMock(returncode=1, stderr="Permission denied")

        result = nginx_manager.update_client_max_body_size("1G")

        assert result is False
        nginx_manager.config.set.assert_not_called()

    @patch('wslaragon.services.nginx.subprocess.Popen')
    @patch('wslaragon.services.nginx.subprocess.run')
    def test_update_client_max_body_size_fails_when_tee_write_fails(self, mock_run, mock_popen, nginx_manager):
        """Test that a failed sudo tee write returns False before validating config"""
        mock_run.return_value = MagicMock(returncode=0)
        write_process = MagicMock()
        write_process.communicate.return_value = ("", "permission denied")
        write_process.returncode = 1
        mock_popen.return_value = write_process

        nginx_manager.test_config = MagicMock(return_value=True)
        nginx_manager.reload = MagicMock(return_value=True)

        result = nginx_manager.update_client_max_body_size("1G")

        assert result is False
        nginx_manager.test_config.assert_not_called()
        nginx_manager.config.set.assert_not_called()

    @patch('wslaragon.services.nginx.subprocess.Popen')
    @patch('wslaragon.services.nginx.subprocess.run')
    def test_update_client_max_body_size_restores_previous_content_on_invalid_config(
        self, mock_run, mock_popen, nginx_manager
    ):
        """Test that an existing drop-in's content is rewritten (not deleted) on rollback"""
        mock_run.return_value = MagicMock(returncode=0)

        # A previous drop-in already exists on disk with prior content
        conf_d = nginx_manager.config_dir / 'conf.d'
        conf_d.mkdir(parents=True)
        dropin = conf_d / 'wslaragon.conf'
        dropin.write_text("# Managed by WSLaragon\nclient_max_body_size 256M;\n")

        write_process = MagicMock()
        write_process.communicate.return_value = ("", "")
        write_process.returncode = 0
        rollback_process = MagicMock()
        rollback_process.communicate.return_value = ("", "")
        rollback_process.returncode = 0
        mock_popen.side_effect = [write_process, rollback_process]

        nginx_manager.test_config = MagicMock(return_value=False)
        nginx_manager.reload = MagicMock(return_value=True)

        result = nginx_manager.update_client_max_body_size("garbage")

        assert result is False
        nginx_manager.config.set.assert_not_called()
        # Rollback must rewrite via tee with the previous content, not `rm`
        assert mock_popen.call_count == 2
        rollback_process.communicate.assert_called_once_with(
            input="# Managed by WSLaragon\nclient_max_body_size 256M;\n"
        )
        rm_calls = [c for c in mock_run.call_args_list if 'rm' in c[0][0]]
        assert len(rm_calls) == 0

    @patch('wslaragon.services.nginx.subprocess.run')
    def test_update_client_max_body_size_returns_false_on_exception(self, mock_run, nginx_manager):
        """Test that an unexpected exception is caught and returns False"""
        mock_run.side_effect = OSError("boom")

        result = nginx_manager.update_client_max_body_size("1G")

        assert result is False
        nginx_manager.config.set.assert_not_called()