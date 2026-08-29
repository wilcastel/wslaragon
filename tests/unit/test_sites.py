"""Tests for the SiteManager module"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest


class TestSiteManager:
    """Test suite for the SiteManager class"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        """Create a SiteManager instance with mocked dependencies"""
        # Create real directories for testing
        config_dir = tmp_path / ".wslaragon"
        config_dir.mkdir(parents=True, exist_ok=True)
        sites_dir = config_dir / "sites"
        sites_dir.mkdir(exist_ok=True)
        web_dir = tmp_path / "web"
        web_dir.mkdir(exist_ok=True)
        
        # Create mock config
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "sites.tld": ".test",
            "sites.document_root": str(web_dir),
            "sites.dir": str(sites_dir),
        }.get(key, default)
        
        # Patch the SSL manager to avoid real SSL operations
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager
            return SiteManager(config, mock_nginx_manager, mock_mysql_manager)

    def test_site_manager_initialization(self, site_manager):
        """Test SiteManager initializes with correct attributes"""
        assert site_manager.tld == ".test"
        assert site_manager.document_root.name == "web"

    def test_site_manager_loads_existing_sites(self, site_manager):
        """Test SiteManager loads existing sites from JSON"""
        assert isinstance(site_manager.sites, dict)


class TestSiteManagerInitDefaults:
    """Test suite for SiteManager.__init__ fallback defaults"""

    def test_document_root_defaults_to_home_web_when_missing(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        """When sites.document_root isn't configured, fall back to <home>/web."""
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager

            config = MagicMock()
            config.home_dir = tmp_path
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.dir": str(tmp_path / "sites"),
                # sites.document_root intentionally absent -> lambda returns default=None
            }.get(key, default)

            sm = SiteManager(config, mock_nginx_manager, mock_mysql_manager)

            assert sm.document_root == tmp_path / "web"


class TestSiteManagerCleanupFailedSiteDirectory:
    """Test suite for _cleanup_failed_site_directory"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager

            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)

            return SiteManager(config, mock_nginx_manager, mock_mysql_manager)

    def test_cleanup_noop_when_dir_is_none(self, site_manager):
        """Test cleanup does nothing when passed None"""
        # Should not raise
        site_manager._cleanup_failed_site_directory(None)

    def test_cleanup_noop_when_dir_does_not_exist(self, site_manager, tmp_path):
        """Test cleanup does nothing when the directory was never created"""
        missing_dir = tmp_path / "web" / "never-created"

        # Should not raise
        site_manager._cleanup_failed_site_directory(missing_dir)

    def test_cleanup_removes_dir_via_rmtree(self, site_manager, tmp_path):
        """Test cleanup removes an existing directory via shutil.rmtree"""
        target = tmp_path / "web" / "orphan"
        target.mkdir(parents=True)

        site_manager._cleanup_failed_site_directory(target)

        assert not target.exists()

    @patch('wslaragon.services.sites.subprocess.run')
    @patch('wslaragon.services.sites.shutil.rmtree')
    def test_cleanup_falls_back_to_sudo_rm_when_rmtree_fails(self, mock_rmtree, mock_run, site_manager, tmp_path):
        """Test cleanup falls back to `sudo rm -rf` when shutil.rmtree raises"""
        target = tmp_path / "web" / "orphan"
        target.mkdir(parents=True)
        mock_rmtree.side_effect = OSError("permission denied")

        site_manager._cleanup_failed_site_directory(target)

        mock_run.assert_called_once_with(['sudo', 'rm', '-rf', str(target)], check=True, timeout=60)

    @patch('wslaragon.services.sites.subprocess.run')
    @patch('wslaragon.services.sites.shutil.rmtree')
    def test_cleanup_logs_when_both_rmtree_and_sudo_fail(self, mock_rmtree, mock_run, site_manager, tmp_path):
        """Test cleanup swallows the error when even the sudo fallback fails"""
        target = tmp_path / "web" / "orphan"
        target.mkdir(parents=True)
        mock_rmtree.side_effect = OSError("permission denied")
        mock_run.side_effect = Exception("sudo also failed")

        # Should not raise despite both cleanup attempts failing
        site_manager._cleanup_failed_site_directory(target)


class TestSiteManagerNormalizeSiteName:
    """Test suite for _normalize_site_name"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager

            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)

            return SiteManager(config, mock_nginx_manager, mock_mysql_manager)

    def test_normalize_strips_tld_suffix(self, site_manager):
        """Test a site name that already includes the TLD is stripped"""
        assert site_manager._normalize_site_name('dash.aaa.test') == 'dash.aaa'

    def test_normalize_leaves_name_without_tld_untouched(self, site_manager):
        """Test a site name without the TLD suffix is unchanged"""
        assert site_manager._normalize_site_name('blog') == 'blog'


class TestSiteManagerCreateSite:
    """Test suite for create_site method"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager
            
            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
                "ssl.dir": str(tmp_path / "ssl"),
                "ssl.ca_file": str(tmp_path / "ssl" / "rootCA.pem"),
                "ssl.ca_key": str(tmp_path / "ssl" / "rootCA-key.pem"),
                "windows.hosts_file": "/mnt/c/Windows/System32/drivers/etc/hosts",
            }.get(key, default)
            
            sm = SiteManager(config, mock_nginx_manager, mock_mysql_manager)
            return sm

    @patch('subprocess.run')
    def test_create_site_validates_name(self, mock_run, site_manager):
        """Test create_site validates site name"""
        result = site_manager.create_site("invalid name!")
        
        assert result['success'] is False
        assert 'Invalid site name' in result['error']

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_create_site_basic_php(self, mock_exists, mock_run, site_manager):
        """Test creating a basic PHP site"""
        mock_exists.return_value = False
        
        # Mock the nginx add_site call
        site_manager.nginx.add_site.return_value = (True, None)
        
        result = site_manager.create_site('testphp', php=True, ssl=False)
        
        # Basic validation - may fail due to other deps but we check structure
        assert 'success' in result

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_create_site_prevents_duplicate(self, mock_exists, mock_run, site_manager):
        """Test create_site prevents duplicate site names"""
        mock_exists.return_value = False
        
        # Add a site to the registry
        site_manager.sites['existing'] = {
            'name': 'existing',
            'domain': 'existing.test',
            'document_root': '/test/existing',
            'enabled': True
        }
        
        result = site_manager.create_site('existing')
        
        assert result['success'] is False
        assert 'already exists' in result['error']

    @patch('wslaragon.services.sites.get_site_creator', return_value=None)
    def test_create_site_rolls_back_directory_when_nginx_fails(self, _mock_creator, site_manager):
        """Test create_site cleans orphan directory on failure"""
        site_manager.nginx.add_site.return_value = (False, "nginx failed")

        result = site_manager.create_site('rollbackme', php=True, ssl=False)

        assert result['success'] is False
        assert 'Failed to create Nginx configuration' in result['error']
        assert not (site_manager.document_root / 'rollbackme').exists()

    @patch('wslaragon.services.sites.get_site_creator')
    @patch('subprocess.run')
    def test_create_site_astro_uses_dist_as_web_root(self, mock_run, mock_creator, site_manager):
        """Test astro_template sites serve from a dist/ subfolder (SSG output)."""
        mock_creator.return_value.create.return_value = []
        site_manager.nginx.add_site.return_value = (True, None)

        result = site_manager.create_site('myblog', php=False, ssl=False, astro_template='basics')

        assert result['success'] is True
        assert result['site']['web_root'].endswith('/myblog/dist')
        assert result['site']['php'] is False

    @patch('wslaragon.services.sites.SSLManager')
    @patch('wslaragon.services.sites.get_site_creator')
    @patch('subprocess.run')
    def test_create_headless_site_registers_frontend_and_backend(self, mock_run, mock_creator, mock_ssl, site_manager):
        """Test headless site creation registers flat frontend and API sites."""
        mock_creator.return_value.create.return_value = []
        mock_ssl.return_value.setup_ssl_for_site.return_value = {'success': True}
        site_manager.nginx.add_site.return_value = (True, None)
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        result = site_manager.create_headless_site('misitio', backend='wordpress', frontend='astro')

        assert result['success'] is True
        assert 'misitio' in site_manager.sites
        assert 'api.misitio' in site_manager.sites
        assert site_manager.sites['misitio']['document_root'].endswith('/misitio/front')
        assert site_manager.sites['misitio']['web_root'].endswith('/misitio/front/dist')
        assert site_manager.sites['api.misitio']['document_root'].endswith('/misitio/back')
        assert site_manager.sites['api.misitio']['database'] == 'api_misitio_db'

    @patch('wslaragon.services.sites.get_site_creator')
    def test_create_headless_site_rolls_back_root_when_nginx_fails(self, mock_creator, site_manager):
        """Test headless site creation removes root directory on failure."""
        mock_creator.return_value.create.return_value = []
        site_manager.nginx.add_site.side_effect = [(True, None), (False, "nginx failed")]
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        result = site_manager.create_headless_site('rollbackheadless', backend='laravel', frontend='sveltekit', ssl=False)

        assert result['success'] is False
        assert 'Failed to create frontend Nginx configuration' in result['error']
        assert 'rollbackheadless' not in site_manager.sites
        assert 'api.rollbackheadless' not in site_manager.sites
        assert not (site_manager.document_root / 'rollbackheadless').exists()

    @patch('wslaragon.services.sites.get_site_creator')
    def test_create_headless_site_drops_database_on_later_failure(self, mock_creator, site_manager):
        """Test the backend database created for a headless site is dropped if a later step fails."""
        mock_creator.return_value.create.return_value = []
        # First add_site (backend) succeeds, second (frontend) fails
        site_manager.nginx.add_site.side_effect = [(True, None), (False, "nginx failed")]
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        result = site_manager.create_headless_site('dbrollback', backend='wordpress', frontend='astro', ssl=False)

        assert result['success'] is False
        site_manager.mysql.drop_database.assert_called_once_with('api_dbrollback_db')

    @patch('wslaragon.services.sites.get_site_creator')
    def test_create_headless_site_does_not_drop_preexisting_database(self, mock_creator, site_manager):
        """Test a pre-existing database (not created by this call) is left alone on rollback."""
        mock_creator.return_value.create.return_value = []
        site_manager.nginx.add_site.side_effect = [(True, None), (False, "nginx failed")]
        site_manager.mysql.database_exists.return_value = True

        result = site_manager.create_headless_site('dbkeep', backend='wordpress', frontend='astro', ssl=False)

        assert result['success'] is False
        site_manager.mysql.drop_database.assert_not_called()

    def test_create_headless_site_rejects_invalid_site_name(self, site_manager):
        """Test create_headless_site validates the site name before anything else."""
        result = site_manager.create_headless_site('invalid name!', backend='wordpress', frontend='astro')

        assert result['success'] is False
        assert 'Invalid site name' in result['error']

    @patch('wslaragon.services.sites.get_site_creator')
    @patch('subprocess.run')
    def test_create_headless_site_recreate_removes_existing_root_dir(self, mock_run, mock_creator, site_manager):
        """Test recreate=True wipes a pre-existing root directory before scaffolding again."""
        mock_creator.return_value.create.return_value = []
        site_manager.nginx.add_site.return_value = (True, None)
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        root = site_manager.document_root / 'recreateme'
        root.mkdir(parents=True)

        result = site_manager.create_headless_site('recreateme', backend='wordpress', frontend='astro',
                                                     ssl=False, recreate=True)

        assert result['success'] is True
        rm_calls = [c for c in mock_run.call_args_list if 'rm' in c[0][0]]
        assert any(str(root) in c[0][0] for c in rm_calls)

    def test_create_headless_site_rejects_invalid_backend(self, site_manager):
        """Test create_headless_site validates the backend type."""
        result = site_manager.create_headless_site('badbackend', backend='django', frontend='astro')

        assert result['success'] is False
        assert 'Invalid backend' in result['error']

    def test_create_headless_site_rejects_invalid_frontend(self, site_manager):
        """Test create_headless_site validates the frontend type."""
        result = site_manager.create_headless_site('badfrontend', backend='wordpress', frontend='nextjs')

        assert result['success'] is False
        assert 'Invalid frontend' in result['error']

    @patch('wslaragon.services.sites.get_site_creator')
    @patch('subprocess.run')
    def test_create_headless_site_normalizes_sveltkit_alias(self, mock_run, mock_creator, site_manager):
        """Test the common 'sveltkit' misspelling is normalized to 'sveltekit'."""
        mock_creator.return_value.create.return_value = []
        site_manager.nginx.add_site.return_value = (True, None)
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        result = site_manager.create_headless_site('sveltalias', backend='wordpress', frontend='sveltkit', ssl=False)

        assert result['success'] is True
        assert site_manager.sites['sveltalias']['frontend'] == 'sveltekit'

    def test_create_headless_site_rejects_name_collision_without_recreate(self, site_manager):
        """Test create_headless_site refuses to overwrite an existing site without --force."""
        site_manager.sites['collide'] = {'name': 'collide'}

        result = site_manager.create_headless_site('collide', backend='wordpress', frontend='astro')

        assert result['success'] is False
        assert 'Site already exists' in result['error']

    def test_create_headless_site_rejects_existing_root_dir_without_recreate(self, site_manager):
        """Test create_headless_site refuses to reuse a leftover directory without --force."""
        (site_manager.document_root / 'leftover').mkdir(parents=True)

        result = site_manager.create_headless_site('leftover', backend='wordpress', frontend='astro')

        assert result['success'] is False
        assert 'Site directory already exists' in result['error']

    @patch('wslaragon.services.sites.get_site_creator')
    def test_create_headless_site_raises_on_database_creation_failure(self, mock_creator, site_manager):
        """Test create_headless_site fails cleanly when the backend database can't be created."""
        mock_creator.return_value.create.return_value = []
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (False, "Connection refused")

        result = site_manager.create_headless_site('dbfail', backend='wordpress', frontend='astro', ssl=False)

        assert result['success'] is False
        assert 'Failed to create database' in result['error']

    @patch('wslaragon.services.sites.SSLManager')
    @patch('wslaragon.services.sites.get_site_creator')
    def test_create_headless_site_raises_on_ssl_failure(self, mock_creator, mock_ssl, site_manager):
        """Test create_headless_site fails cleanly when SSL provisioning fails."""
        mock_creator.return_value.create.return_value = []
        mock_ssl.return_value.setup_ssl_for_site.return_value = {'success': False, 'error': 'mkcert missing'}
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        result = site_manager.create_headless_site('sslfail', backend='wordpress', frontend='astro', ssl=True)

        assert result['success'] is False
        assert 'Failed to generate SSL' in result['error']

    @patch('wslaragon.services.sites.get_site_creator')
    def test_create_headless_site_raises_on_backend_nginx_failure(self, mock_creator, site_manager):
        """Test create_headless_site fails cleanly when the backend Nginx config fails."""
        mock_creator.return_value.create.return_value = []
        site_manager.nginx.add_site.return_value = (False, "nginx backend failed")
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        result = site_manager.create_headless_site('backendfail', backend='wordpress', frontend='astro', ssl=False)

        assert result['success'] is False
        assert 'Failed to create backend Nginx configuration' in result['error']

    @patch('wslaragon.services.sites.get_site_creator')
    def test_create_headless_site_rollback_swallows_nginx_remove_error(self, mock_creator, site_manager):
        """Test the rollback path swallows exceptions raised by nginx.remove_site."""
        mock_creator.return_value.create.return_value = []
        site_manager.nginx.add_site.side_effect = [(True, None), (False, "nginx frontend failed")]
        site_manager.nginx.remove_site.side_effect = Exception("remove_site boom")
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        # Should not raise despite remove_site blowing up during rollback
        result = site_manager.create_headless_site('rmerr', backend='wordpress', frontend='astro', ssl=False)

        assert result['success'] is False

    @patch('wslaragon.services.sites.get_site_creator')
    def test_create_headless_site_rollback_swallows_drop_database_error(self, mock_creator, site_manager):
        """Test the rollback path swallows exceptions raised by mysql.drop_database."""
        mock_creator.return_value.create.return_value = []
        site_manager.nginx.add_site.side_effect = [(True, None), (False, "nginx frontend failed")]
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)
        site_manager.mysql.drop_database.side_effect = Exception("drop_database boom")

        # Should not raise despite drop_database blowing up during rollback
        result = site_manager.create_headless_site('dberr', backend='wordpress', frontend='astro', ssl=False)

        assert result['success'] is False


class TestRegistrationLayout:
    """Slice 4b: pure mapping from computed site metadata to the closed layout
    enum the privileged helper accepts (no root, path, or Nginx content)."""

    @pytest.mark.parametrize("kwargs,expected", [
        (dict(is_astro_ssg=False, use_public=False), "normal-root"),
        (dict(is_astro_ssg=False, use_public=True), "normal-public"),
        (dict(is_astro_ssg=True, use_public=False), "normal-dist"),
        (dict(is_astro_ssg=True, use_public=True), "normal-dist"),
        (dict(is_astro_ssg=False, use_public=False, headless_role="backend"), "headless-backend-root"),
        (dict(is_astro_ssg=False, use_public=True, headless_role="backend"), "headless-backend-public"),
        (dict(is_astro_ssg=False, use_public=False, headless_role="frontend"), "headless-frontend-root"),
        (dict(is_astro_ssg=True, use_public=False, headless_role="frontend"), "headless-frontend-dist"),
    ])
    def test_layout_mapping(self, kwargs, expected):
        from wslaragon.services.sites import registration_layout
        assert registration_layout(**kwargs) == expected


class TestSiteManagerAgentMode:
    """Slice 4b: when a PrivilegeClient is injected, derived host/Nginx/access
    registration is routed through it instead of direct sudo, sites.json is
    committed only after registration succeeds, and a registration failure
    preserves the unprivileged scaffold/certificate/database."""

    @pytest.fixture
    def privilege_client(self):
        from wslaragon.services.agent_privilege import PrivilegeResult
        client = MagicMock()
        client.apply_registration.return_value = PrivilegeResult(True, "ok")
        client.remove_registration.return_value = PrivilegeResult(True, "ok")
        return client

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager, privilege_client):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager

            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
                "ssl.dir": str(tmp_path / "ssl"),
            }.get(key, default)

            return SiteManager(
                config, mock_nginx_manager, mock_mysql_manager,
                privilege_client=privilege_client,
            )

    @patch('wslaragon.services.sites.get_site_creator', return_value=None)
    @patch('subprocess.run')
    def test_create_site_routes_apply_registration_not_nginx(
        self, mock_run, _creator, site_manager, privilege_client
    ):
        result = site_manager.create_site('agentsite', php=True, ssl=False)

        assert result['success'] is True
        privilege_client.apply_registration.assert_called_once_with(
            'agentsite', 'normal-root', ssl=False, php=True, proxy_port=None
        )
        site_manager.nginx.add_site.assert_not_called()
        assert 'agentsite' in site_manager.sites

    @patch('wslaragon.services.sites.get_site_creator', return_value=None)
    @patch('subprocess.run')
    def test_create_site_public_layout(self, mock_run, _creator, site_manager, privilege_client):
        site_manager.create_site('pubsite', php=True, ssl=False, public_dir=True)

        assert privilege_client.apply_registration.call_args[0][1] == 'normal-public'

    @patch('wslaragon.services.sites.get_site_creator')
    @patch('subprocess.run')
    def test_create_site_astro_layout(self, mock_run, mock_creator, site_manager, privilege_client):
        mock_creator.return_value.create.return_value = []

        site_manager.create_site('blogsite', php=False, ssl=False, astro_template='basics')

        assert privilege_client.apply_registration.call_args[0][1] == 'normal-dist'

    @patch('wslaragon.services.sites.SiteManager._cleanup_failed_site_directory')
    @patch('wslaragon.services.sites.get_site_creator', return_value=None)
    @patch('subprocess.run')
    def test_apply_registration_failure_preserves_scaffold(
        self, mock_run, _creator, mock_cleanup, site_manager, privilege_client
    ):
        from wslaragon.services.agent_privilege import PrivilegeResult
        privilege_client.apply_registration.return_value = PrivilegeResult(False, "operation_failed")

        result = site_manager.create_site('failsite', php=True, ssl=False)

        assert result['success'] is False
        assert 'operation_failed' in result['error']
        assert 'failsite' not in site_manager.sites
        assert (site_manager.document_root / 'failsite').exists()
        mock_cleanup.assert_not_called()

    @patch('wslaragon.services.sites.SiteManager.fix_permissions')
    @patch('wslaragon.services.sites.get_site_creator', return_value=None)
    @patch('subprocess.run')
    def test_agent_mode_skips_fix_permissions(self, mock_run, _creator, mock_fix, site_manager):
        site_manager.create_site('permsite', php=True, ssl=False)

        mock_fix.assert_not_called()

    @patch('wslaragon.services.sites.SSLManager')
    @patch('wslaragon.services.sites.get_site_creator', return_value=None)
    @patch('subprocess.run')
    def test_ssl_setup_skips_host_registration(self, mock_run, _creator, mock_ssl, site_manager):
        mock_ssl.return_value.setup_ssl_for_site.return_value = {'success': True}

        site_manager.create_site('sslsite', php=True, ssl=True)

        _, kwargs = mock_ssl.return_value.setup_ssl_for_site.call_args
        assert kwargs.get('register_hosts') is False

    @patch('wslaragon.services.sites.SSLManager')
    @patch('wslaragon.services.sites.get_site_creator')
    @patch('subprocess.run')
    def test_headless_registers_backend_then_frontend(
        self, mock_run, mock_creator, mock_ssl, site_manager, privilege_client
    ):
        mock_creator.return_value.create.return_value = []
        mock_ssl.return_value.setup_ssl_for_site.return_value = {'success': True}
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)

        result = site_manager.create_headless_site('hs', backend='wordpress', frontend='astro', ssl=False)

        assert result['success'] is True
        calls = privilege_client.apply_registration.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == 'api.hs'
        assert calls[0][0][1].startswith('headless-backend')
        assert calls[1][0][0] == 'hs'
        assert calls[1][0][1].startswith('headless-frontend')
        assert 'hs' in site_manager.sites and 'api.hs' in site_manager.sites
        site_manager.nginx.add_site.assert_not_called()

    @patch('wslaragon.services.sites.SSLManager')
    @patch('wslaragon.services.sites.get_site_creator')
    @patch('subprocess.run')
    def test_headless_frontend_failure_removes_backend_only(
        self, mock_run, mock_creator, mock_ssl, site_manager, privilege_client
    ):
        from wslaragon.services.agent_privilege import PrivilegeResult
        mock_creator.return_value.create.return_value = []
        mock_ssl.return_value.setup_ssl_for_site.return_value = {'success': True}
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)
        privilege_client.apply_registration.side_effect = [
            PrivilegeResult(True, "ok"),
            PrivilegeResult(False, "operation_failed"),
        ]

        result = site_manager.create_headless_site('hf', backend='wordpress', frontend='astro', ssl=False)

        assert result['success'] is False
        privilege_client.remove_registration.assert_called_once()
        removed = privilege_client.remove_registration.call_args[0]
        assert removed[0] == 'api.hf'
        assert removed[1].startswith('headless-backend')
        assert 'hf' not in site_manager.sites
        assert 'api.hf' not in site_manager.sites
        assert (site_manager.document_root / 'hf').exists()
        site_manager.mysql.drop_database.assert_not_called()

    @patch('wslaragon.services.sites.get_site_creator', return_value=None)
    @patch('subprocess.run')
    def test_interactive_mode_unchanged_without_client(
        self, mock_run, _creator, tmp_path, mock_nginx_manager, mock_mysql_manager
    ):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager

            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)
            sm = SiteManager(config, mock_nginx_manager, mock_mysql_manager)
        sm.nginx.add_site.return_value = (True, None)

        sm.create_site('classic', php=True, ssl=False)

        sm.nginx.add_site.assert_called_once()


class TestSiteManagerAgentModeTriangulation:
    """Slice 4b TRIANGULATE: failure/edge behaviour of the agent registration path."""

    @pytest.fixture
    def privilege_client(self):
        from wslaragon.services.agent_privilege import PrivilegeResult
        client = MagicMock()
        client.apply_registration.return_value = PrivilegeResult(True, "ok")
        client.remove_registration.return_value = PrivilegeResult(True, "ok")
        return client

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager, privilege_client):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager

            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
                "ssl.dir": str(tmp_path / "ssl"),
            }.get(key, default)
            return SiteManager(
                config, mock_nginx_manager, mock_mysql_manager,
                privilege_client=privilege_client,
            )

    def test_registration_layout_rejects_unknown_headless_role(self):
        from wslaragon.services.sites import registration_layout
        with pytest.raises(ValueError):
            registration_layout(is_astro_ssg=False, use_public=False, headless_role="sidecar")

    @pytest.mark.parametrize("code", ["not_ready", "authorization_denied", "operation_failed"])
    @patch('wslaragon.services.sites.get_site_creator', return_value=None)
    @patch('subprocess.run')
    def test_create_site_surfaces_each_failure_code(
        self, mock_run, _creator, code, site_manager, privilege_client
    ):
        from wslaragon.services.agent_privilege import PrivilegeResult
        privilege_client.apply_registration.return_value = PrivilegeResult(False, code)

        result = site_manager.create_site('coded', php=True, ssl=False)

        assert result['success'] is False
        assert code in result['error']

    @patch('wslaragon.services.sites.SiteManager._save_sites')
    @patch('wslaragon.services.sites.get_site_creator', return_value=None)
    @patch('subprocess.run')
    def test_no_state_commit_before_successful_registration(
        self, mock_run, _creator, mock_save, site_manager, privilege_client
    ):
        from wslaragon.services.agent_privilege import PrivilegeResult
        privilege_client.apply_registration.return_value = PrivilegeResult(False, "operation_failed")

        site_manager.create_site('nocommit', php=True, ssl=False)

        mock_save.assert_not_called()

    @patch('wslaragon.services.sites.SSLManager')
    @patch('wslaragon.services.sites.get_site_creator')
    @patch('subprocess.run')
    def test_headless_backend_registration_failure_does_not_compensate(
        self, mock_run, mock_creator, mock_ssl, site_manager, privilege_client
    ):
        from wslaragon.services.agent_privilege import PrivilegeResult
        mock_creator.return_value.create.return_value = []
        mock_ssl.return_value.setup_ssl_for_site.return_value = {'success': True}
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)
        privilege_client.apply_registration.return_value = PrivilegeResult(False, "operation_failed")

        result = site_manager.create_headless_site('hb', backend='wordpress', frontend='astro', ssl=False)

        assert result['success'] is False
        privilege_client.apply_registration.assert_called_once()
        privilege_client.remove_registration.assert_not_called()
        assert 'hb' not in site_manager.sites and 'api.hb' not in site_manager.sites

    @patch('wslaragon.services.sites.SSLManager')
    @patch('wslaragon.services.sites.get_site_creator')
    @patch('subprocess.run')
    def test_headless_compensation_failure_still_returns_original_error(
        self, mock_run, mock_creator, mock_ssl, site_manager, privilege_client
    ):
        from wslaragon.services.agent_privilege import PrivilegeResult
        mock_creator.return_value.create.return_value = []
        mock_ssl.return_value.setup_ssl_for_site.return_value = {'success': True}
        site_manager.mysql.database_exists.return_value = False
        site_manager.mysql.create_database.return_value = (True, None)
        privilege_client.apply_registration.side_effect = [
            PrivilegeResult(True, "ok"),
            PrivilegeResult(False, "operation_failed"),
        ]
        privilege_client.remove_registration.return_value = PrivilegeResult(False, "operation_failed")

        result = site_manager.create_headless_site('hc', backend='wordpress', frontend='astro', ssl=False)

        assert result['success'] is False
        assert 'operation_failed' in result['error']
        privilege_client.remove_registration.assert_called_once()


class TestSiteManagerListSites:
    """Test suite for list_sites method"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager
            
            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)
            
            return SiteManager(config, mock_nginx_manager, mock_mysql_manager)

    def test_list_sites_returns_empty_when_no_sites(self, site_manager):
        """Test list_sites returns empty list when no sites exist"""
        result = site_manager.list_sites()
        
        assert result == []

    def test_list_sites_returns_all_sites(self, site_manager):
        """Test list_sites returns all registered sites"""
        site_manager.sites = {
            'site1': {'name': 'site1', 'domain': 'site1.test'},
            'site2': {'name': 'site2', 'domain': 'site2.test'},
        }
        
        result = site_manager.list_sites()
        
        assert len(result) == 2


class TestSiteManagerGetSite:
    """Test suite for get_site method"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager
            
            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)
            
            return SiteManager(config, mock_nginx_manager, mock_mysql_manager)

    def test_get_site_returns_none_when_not_found(self, site_manager):
        """Test get_site returns None for non-existent site"""
        result = site_manager.get_site('nonexistent')
        
        assert result is None

    def test_get_site_returns_site_info(self, site_manager):
        """Test get_site returns site information"""
        site_manager.sites = {
            'mysite': {'name': 'mysite', 'domain': 'mysite.test'}
        }
        
        result = site_manager.get_site('mysite')
        
        assert result is not None
        assert result['name'] == 'mysite'


class TestSiteManagerDeleteSite:
    """Test suite for delete_site method"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager
            
            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)
            
            sm = SiteManager(config, mock_nginx_manager, mock_mysql_manager)
            sm.sites = {
                'todelete': {
                    'name': 'todelete',
                    'domain': 'todelete.test',
                    'document_root': str(tmp_path / "web" / "todelete"),
                    'database': 'todelete_db',
                    'db_type': 'mysql',
                }
            }
            return sm

    def test_delete_site_returns_error_when_not_found(self, site_manager):
        """Test delete_site returns error for non-existent site"""
        result = site_manager.delete_site('nonexistent')
        
        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('subprocess.run')
    def test_delete_site_removes_from_registry(self, mock_run, site_manager):
        """Test delete_site removes site from registry"""
        site_manager.nginx.remove_site.return_value = True

        result = site_manager.delete_site('todelete', remove_files=False, remove_database=False)

        assert result['success'] is True
        assert 'todelete' not in site_manager.sites


class TestSiteManagerDeleteHeadlessSite:
    """Test suite for delete_site handling headless frontend/backend pairs"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager

            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)

            sm = SiteManager(config, mock_nginx_manager, mock_mysql_manager)
            root = tmp_path / "web" / "misitio"
            (root / 'front').mkdir(parents=True, exist_ok=True)
            (root / 'back').mkdir(parents=True, exist_ok=True)
            sm.sites = {
                'misitio': {
                    'name': 'misitio', 'document_root': str(root / 'front'),
                    'headless': True, 'role': 'frontend', 'root': str(root),
                    'backend_site': 'api.misitio', 'database': None,
                },
                'api.misitio': {
                    'name': 'api.misitio', 'document_root': str(root / 'back'),
                    'headless': True, 'role': 'backend', 'root': str(root),
                    'frontend_site': 'misitio', 'database': 'api_misitio_db', 'db_type': 'mysql',
                },
            }
            return sm

    @patch('subprocess.run')
    def test_delete_frontend_half_also_deletes_backend(self, mock_run, site_manager):
        """Deleting the frontend of a headless pair must also remove the backend."""
        result = site_manager.delete_site('misitio', remove_files=False, remove_database=False)

        assert result['success'] is True
        assert 'misitio' not in site_manager.sites
        assert 'api.misitio' not in site_manager.sites
        assert site_manager.nginx.remove_site.call_count == 2
        site_manager.nginx.remove_site.assert_any_call('misitio')
        site_manager.nginx.remove_site.assert_any_call('api.misitio')

    @patch('subprocess.run')
    def test_delete_headless_pair_drops_backend_database(self, mock_run, site_manager):
        """remove_database=True must drop the backend's database when deleting either half."""
        result = site_manager.delete_site('misitio', remove_files=False, remove_database=True)

        assert result['success'] is True
        site_manager.mysql.drop_database.assert_called_once_with('api_misitio_db')

    @patch('subprocess.run')
    def test_delete_headless_pair_removes_shared_root_once(self, mock_run, site_manager):
        """remove_files=True must remove the shared root directory exactly once, not per-half."""
        result = site_manager.delete_site('api.misitio', remove_files=True, remove_database=False)

        assert result['success'] is True
        rm_calls = [c for c in mock_run.call_args_list if 'rm' in c[0][0]]
        assert len(rm_calls) == 1
        assert str(Path(site_manager.document_root) / 'misitio') in rm_calls[0][0][0]


class TestSiteManagerPortAllocation:
    """Test suite for port allocation logic"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager
            
            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)
            
            return SiteManager(config, mock_nginx_manager, mock_mysql_manager)

    def test_find_next_free_port_starts_at_given_port(self, site_manager):
        """Test _find_next_free_port starts at the given port"""
        # Should not throw an exception
        port = site_manager._find_next_free_port(3000)
        
        assert isinstance(port, int)
        assert port >= 3000

    def test_find_next_free_port_avoids_used_ports(self, site_manager):
        """Test _find_next_free_port avoids ports used by existing sites"""
        site_manager.sites = {
            'site1': {'name': 'site1', 'proxy_port': 3000},
            'site2': {'name': 'site2', 'proxy_port': 3001},
        }
        
        port = site_manager._find_next_free_port(3000)
        
        # Should find next available port
        assert port >= 3002


class TestSiteManagerHelperMethods:
    """Test suite for helper methods"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager
            
            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)
            
            return SiteManager(config, mock_nginx_manager, mock_mysql_manager)

    def test_get_site_url_returns_https_url(self, site_manager):
        """Test get_site_url returns HTTPS URL for SSL sites"""
        site_manager.sites = {
            'mysite': {'name': 'mysite', 'ssl': True}
        }
        
        result = site_manager.get_site_url('mysite')
        
        assert result == 'https://mysite.test'

    def test_get_site_url_returns_http_url_for_non_ssl(self, site_manager):
        """Test get_site_url returns HTTP URL for non-SSL sites"""
        site_manager.sites = {
            'mysite': {'name': 'mysite', 'ssl': False}
        }
        
        result = site_manager.get_site_url('mysite')
        
        assert result == 'http://mysite.test'

    def test_get_site_url_returns_none_for_unknown_site(self, site_manager):
        """Test get_site_url returns None for unknown site"""
        result = site_manager.get_site_url('unknown')

        assert result is None


class TestSiteManagerApiProxies:
    """Test suite for add_api_proxy / remove_api_proxy / list_api_proxies"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager

            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)

            sm = SiteManager(config, mock_nginx_manager, mock_mysql_manager)
            sm.sites = {
                'dash': {
                    'name': 'dash', 'document_root': str(tmp_path / "web" / "dash"),
                    'ssl': True, 'php': False, 'proxy_port': None, 'api_proxies': {},
                }
            }
            return sm

    # --- add_api_proxy ---

    def test_add_api_proxy_site_not_found(self, site_manager):
        result = site_manager.add_api_proxy('missing', '/api', 'https://api.dash.test')

        assert result['success'] is False
        assert 'Site not found' in result['error']

    def test_add_api_proxy_initializes_missing_api_proxies_dict(self, site_manager):
        """A site registered before api_proxies existed shouldn't KeyError."""
        del site_manager.sites['dash']['api_proxies']

        result = site_manager.add_api_proxy('dash', '/api', 'https://api.dash.test')

        assert result['success'] is True
        assert site_manager.sites['dash']['api_proxies'] == {'/api': 'https://api.dash.test'}

    def test_add_api_proxy_normalizes_path_and_backend(self, site_manager):
        """Path gets a leading slash + trailing slash stripped; backend gets https:// prefixed."""
        result = site_manager.add_api_proxy('dash', 'api/', 'api.dash.test')

        assert result['success'] is True
        assert result['path'] == '/api'
        assert result['backend'] == 'https://api.dash.test'
        assert site_manager.sites['dash']['api_proxies']['/api'] == 'https://api.dash.test'

    def test_add_api_proxy_rejects_duplicate_path(self, site_manager):
        site_manager.sites['dash']['api_proxies']['/api'] = 'https://api.dash.test'

        result = site_manager.add_api_proxy('dash', '/api', 'https://other.test')

        assert result['success'] is False
        assert 'already exists' in result['error']

    def test_add_api_proxy_reverts_on_nginx_failure(self, site_manager):
        site_manager.nginx.add_site.return_value = (False, "nginx boom")

        result = site_manager.add_api_proxy('dash', '/api', 'https://api.dash.test')

        assert result['success'] is False
        assert 'Failed to update Nginx config' in result['error']
        assert '/api' not in site_manager.sites['dash']['api_proxies']

    def test_add_api_proxy_handles_exception(self, site_manager):
        site_manager.nginx.remove_site.side_effect = Exception("boom")

        result = site_manager.add_api_proxy('dash', '/api', 'https://api.dash.test')

        assert result['success'] is False
        assert 'boom' in result['error']

    # --- remove_api_proxy ---

    def test_remove_api_proxy_site_not_found(self, site_manager):
        result = site_manager.remove_api_proxy('missing', '/api')

        assert result['success'] is False
        assert 'Site not found' in result['error']

    def test_remove_api_proxy_path_not_found(self, site_manager):
        result = site_manager.remove_api_proxy('dash', '/nope')

        assert result['success'] is False
        assert "No API proxy found at path '/nope'" in result['error']

    def test_remove_api_proxy_success_cleans_up_empty_dict(self, site_manager):
        site_manager.sites['dash']['api_proxies']['/api'] = 'https://api.dash.test'

        result = site_manager.remove_api_proxy('dash', 'api')

        assert result['success'] is True
        assert result['removed_path'] == '/api'
        assert result['removed_backend'] == 'https://api.dash.test'
        assert 'api_proxies' not in site_manager.sites['dash']

    def test_remove_api_proxy_reverts_on_nginx_failure(self, site_manager):
        site_manager.sites['dash']['api_proxies']['/api'] = 'https://api.dash.test'
        site_manager.nginx.add_site.return_value = (False, "nginx boom")

        result = site_manager.remove_api_proxy('dash', '/api')

        assert result['success'] is False
        assert 'Failed to update Nginx config' in result['error']
        assert site_manager.sites['dash']['api_proxies']['/api'] == 'https://api.dash.test'

    def test_remove_api_proxy_handles_exception(self, site_manager):
        site_manager.sites['dash']['api_proxies']['/api'] = 'https://api.dash.test'
        site_manager.nginx.remove_site.side_effect = Exception("boom")

        result = site_manager.remove_api_proxy('dash', '/api')

        assert result['success'] is False
        assert 'boom' in result['error']

    # --- list_api_proxies ---

    def test_list_api_proxies_site_not_found(self, site_manager):
        result = site_manager.list_api_proxies('missing')

        assert result['success'] is False
        assert 'Site not found' in result['error']

    def test_list_api_proxies_returns_configured_proxies(self, site_manager):
        site_manager.sites['dash']['api_proxies']['/api'] = 'https://api.dash.test'

        result = site_manager.list_api_proxies('dash')

        assert result['success'] is True
        assert result['proxies'] == {'/api': 'https://api.dash.test'}

    def test_list_api_proxies_empty_when_none_configured(self, site_manager):
        result = site_manager.list_api_proxies('dash')

        assert result['success'] is True
        assert result['proxies'] == {}


class TestSudoKeepAlive:
    """Test suite for the SudoKeepAlive context manager."""

    @patch('wslaragon.services.sites.subprocess.run')
    def test_sudo_keep_alive_emits_refresh(self, mock_run):
        """SudoKeepAlive must periodically run `sudo -n -v` while active."""
        from wslaragon.services.sites import SudoKeepAlive

        keeper = SudoKeepAlive(interval=15)
        keeper._stop_event.is_set = MagicMock(side_effect=[False, True])
        keeper._loop()

        mock_run.assert_called_once_with(['sudo', '-n', '-v'], capture_output=True, check=False)

    @patch('wslaragon.services.sites.threading.Thread')
    @patch('wslaragon.services.sites.subprocess.run')
    def test_sudo_keep_alive_starts_daemon_thread_in_context(self, mock_run, mock_thread):
        """Entering the context manager starts a daemon refresh thread."""
        from wslaragon.services.sites import SudoKeepAlive

        with SudoKeepAlive(interval=15):
            pass

        mock_thread.assert_called_once()
        assert mock_thread.call_args.kwargs.get('daemon') is True
        mock_thread.return_value.start.assert_called_once()
        mock_thread.return_value.join.assert_called_once()


class TestSiteManagerFixPermissions:
    """Test suite for fix_permissions method"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager

            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)

            sm = SiteManager(config, mock_nginx_manager, mock_mysql_manager)
            doc_root = tmp_path / "web" / "mysite"
            doc_root.mkdir(parents=True)
            sm.sites = {
                'mysite': {
                    'name': 'mysite',
                    'document_root': str(doc_root),
                }
            }
            return sm

    @patch('wslaragon.services.sites.shutil.which')
    @patch('wslaragon.services.sites.subprocess.run')
    def test_apply_permissions_uses_setfacl_when_available(self, mock_run, mock_which, site_manager):
        """When setfacl is installed, use POSIX ACLs to grant www-data read access."""
        mock_which.return_value = '/usr/bin/setfacl'
        mock_run.return_value = MagicMock(returncode=0)

        result = site_manager.fix_permissions('mysite')

        assert result['success'] is True
        setfacl_calls = [c for c in mock_run.call_args_list if 'setfacl' in c[0][0]]
        assert len(setfacl_calls) == 1
        assert setfacl_calls[0][0][0] == [
            'sudo', 'setfacl', '-R', '-m', 'u:www-data:rx',
            site_manager.sites['mysite']['document_root']
        ]

    @patch('wslaragon.services.sites.shutil.which')
    @patch('wslaragon.services.sites.subprocess.run')
    def test_wordpress_docroot_gets_writable_acl(self, mock_run, mock_which, site_manager):
        """WordPress core updates write to wp-admin/, wp-includes/ and root
        files, so the whole docroot must be writable by www-data."""
        mock_which.return_value = '/usr/bin/setfacl'
        mock_run.return_value = MagicMock(returncode=0)
        doc_root = Path(site_manager.sites['mysite']['document_root'])
        (doc_root / 'wp-config.php').write_text("<?php\ndefine('ABSPATH', __DIR__ . '/');\n")

        result = site_manager.fix_permissions('mysite')

        assert result['success'] is True
        calls = [c[0][0] for c in mock_run.call_args_list]
        # Whole docroot gets rwX (not only wp-content)
        assert [
            'sudo', 'setfacl', '-R', '-m', 'u:www-data:rwX', str(doc_root)
        ] in calls
        # The generic read-only rx pass must not be applied to WordPress
        assert not any('u:www-data:rx' in call for call in calls)
        # Default ACLs on docroot dirs so new files inherit write access
        assert [
            'sudo', 'find', str(doc_root), '-type', 'd', '-exec',
            'setfacl', '-m', 'd:u:www-data:rwX', '{}', '+',
        ] in calls
        wp_content = doc_root / 'wp-content'
        assert (wp_content / 'plugins').exists()
        assert (wp_content / 'uploads').exists()
        assert (wp_content / 'upgrade').exists()

    @patch('wslaragon.services.sites.shutil.which')
    @patch('wslaragon.services.sites.subprocess.run')
    def test_apply_permissions_chmod_fallback(self, mock_run, mock_which, site_manager):
        """When setfacl is unavailable, fall back to chmod o+rx."""
        mock_which.return_value = None
        mock_run.return_value = MagicMock(returncode=0)

        result = site_manager.fix_permissions('mysite')

        assert result['success'] is True
        chmod_calls = [c for c in mock_run.call_args_list if 'chmod' in c[0][0]]
        assert any('o+rx' in c[0][0] for c in chmod_calls)

    @patch('wslaragon.services.sites.shutil.which')
    @patch('wslaragon.services.sites.subprocess.run')
    def test_wordpress_chmod_fallback_is_group_writable_on_docroot(self, mock_run, mock_which, site_manager):
        """Without setfacl, WordPress uses group-writable modes on the whole
        docroot and never o+w."""
        mock_which.return_value = None
        mock_run.return_value = MagicMock(returncode=0)
        doc_root = Path(site_manager.sites['mysite']['document_root'])
        (doc_root / 'wp-config.php').write_text("<?php\n")

        result = site_manager.fix_permissions('mysite')

        assert result['success'] is True
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert ['sudo', 'find', str(doc_root), '-type', 'd', '-exec', 'chmod', '2775', '{}', '+'] in calls
        assert ['sudo', 'find', str(doc_root), '-type', 'f', '-exec', 'chmod', '664', '{}', '+'] in calls
        # 2775 already grants others r-x on dirs, so the generic o+rx pass
        # must not run for WordPress
        assert ['sudo', 'chmod', '-R', 'o+rx', str(doc_root)] not in calls
        assert not any('o+w' in call for call in calls)

    @patch('wslaragon.services.sites.shutil.which')
    @patch('wslaragon.services.sites.subprocess.run')
    def test_laravel_docroot_readonly_but_storage_and_cache_writable(self, mock_run, mock_which, site_manager):
        """Regression: the recursive rx pass on the docroot must not strip
        www-data write from storage/ and bootstrap/cache/ — those get rwX
        applied AFTER the base rx pass."""
        mock_which.return_value = '/usr/bin/setfacl'
        mock_run.return_value = MagicMock(returncode=0)
        doc_root = Path(site_manager.sites['mysite']['document_root'])
        (doc_root / 'artisan').write_text("#!/usr/bin/env php\n")

        result = site_manager.fix_permissions('mysite')

        assert result['success'] is True
        calls = [c[0][0] for c in mock_run.call_args_list]
        storage = str(doc_root / 'storage')
        cache = str(doc_root / 'bootstrap' / 'cache')

        rx_call = ['sudo', 'setfacl', '-R', '-m', 'u:www-data:rx', str(doc_root)]
        storage_rwx = ['sudo', 'setfacl', '-R', '-m', 'u:www-data:rwX', storage]
        cache_rwx = ['sudo', 'setfacl', '-R', '-m', 'u:www-data:rwX', cache]
        assert rx_call in calls
        assert storage_rwx in calls
        assert cache_rwx in calls
        # Docroot itself must NOT get rwX
        assert ['sudo', 'setfacl', '-R', '-m', 'u:www-data:rwX', str(doc_root)] not in calls
        # Escalation happens AFTER the base rx pass so it is not overwritten
        assert calls.index(storage_rwx) > calls.index(rx_call)
        assert calls.index(cache_rwx) > calls.index(rx_call)
        # Default ACLs so new log/cache/session files inherit write access
        assert ['sudo', 'find', storage, '-type', 'd', '-exec', 'setfacl', '-m', 'd:u:www-data:rwX', '{}', '+'] in calls
        assert ['sudo', 'find', cache, '-type', 'd', '-exec', 'setfacl', '-m', 'd:u:www-data:rwX', '{}', '+'] in calls
        # Writable dirs are created with parents when missing
        assert (doc_root / 'storage').is_dir()
        assert (doc_root / 'bootstrap' / 'cache').is_dir()

    @patch('wslaragon.services.sites.shutil.which')
    @patch('wslaragon.services.sites.subprocess.run')
    def test_laravel_chmod_fallback_scopes_write_to_storage_and_cache(self, mock_run, mock_which, site_manager):
        """Without setfacl, Laravel gets o+rx on the docroot and group-writable
        modes only on storage/ and bootstrap/cache/."""
        mock_which.return_value = None
        mock_run.return_value = MagicMock(returncode=0)
        doc_root = Path(site_manager.sites['mysite']['document_root'])
        (doc_root / 'artisan').write_text("#!/usr/bin/env php\n")

        result = site_manager.fix_permissions('mysite')

        assert result['success'] is True
        calls = [c[0][0] for c in mock_run.call_args_list]
        storage = str(doc_root / 'storage')
        cache = str(doc_root / 'bootstrap' / 'cache')
        assert ['sudo', 'chmod', '-R', 'o+rx', str(doc_root)] in calls
        for target in (storage, cache):
            assert ['sudo', 'find', target, '-type', 'd', '-exec', 'chmod', '2775', '{}', '+'] in calls
            assert ['sudo', 'find', target, '-type', 'f', '-exec', 'chmod', '664', '{}', '+'] in calls
        # Group-writable modes must NOT leak onto the whole docroot
        assert ['sudo', 'find', str(doc_root), '-type', 'd', '-exec', 'chmod', '2775', '{}', '+'] not in calls
        assert not any('o+w' in call for call in calls)

    @pytest.mark.parametrize('marker,writable_dirs', [
        ('wp-config.php', ['wp-content/plugins', 'wp-content/uploads', 'wp-content/upgrade']),
        ('artisan', ['storage', 'bootstrap/cache']),
    ])
    @patch('wslaragon.services.sites.shutil.which')
    @patch('wslaragon.services.sites.subprocess.run')
    def test_writable_dirs_exist_before_chown(self, mock_run, mock_which, site_manager, marker, writable_dirs):
        """Regression: directories created by fix_permissions itself must exist
        BEFORE the recursive chown runs, otherwise they keep the invoking
        user's primary group and the chmod fallback grants group-write to the
        wrong group — www-data stays read-only while the command reports
        success."""
        mock_which.return_value = None
        doc_root = Path(site_manager.sites['mysite']['document_root'])
        (doc_root / marker).write_text("<?php\n")

        missing_at_chown = []

        def spy(cmd, **kwargs):
            if 'chown' in cmd:
                for rel in writable_dirs:
                    if not (doc_root / rel).exists():
                        missing_at_chown.append(rel)
            return MagicMock(returncode=0)

        mock_run.side_effect = spy

        result = site_manager.fix_permissions('mysite')

        assert result['success'] is True
        assert any('chown' in c[0][0] for c in mock_run.call_args_list)
        assert missing_at_chown == []

    @patch('wslaragon.services.sites.shutil.which')
    @patch('wslaragon.services.sites.subprocess.run')
    def test_generic_site_gets_no_write_acl_anywhere(self, mock_run, mock_which, site_manager):
        """Static/Node/Python/phpMyAdmin sites keep read-only www-data access:
        no rwX and no default ACLs may leak onto any path."""
        mock_which.return_value = '/usr/bin/setfacl'
        mock_run.return_value = MagicMock(returncode=0)
        doc_root = Path(site_manager.sites['mysite']['document_root'])

        result = site_manager.fix_permissions('mysite')

        assert result['success'] is True
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert ['sudo', 'setfacl', '-R', '-m', 'u:www-data:rx', str(doc_root)] in calls
        assert not any('u:www-data:rwX' in call for call in calls)
        assert not any('d:u:www-data:rwX' in call for call in calls)

    @patch('wslaragon.services.sites.shutil.which')
    @patch('wslaragon.services.sites.subprocess.run')
    def test_apply_permissions_returns_error_on_failure(self, mock_run, mock_which, site_manager):
        """fix_permissions must surface subprocess failures."""
        mock_which.return_value = None
        import subprocess as sp
        mock_run.side_effect = sp.CalledProcessError(1, 'chmod')

        result = site_manager.fix_permissions('mysite')

        assert result['success'] is False


class TestSiteManagerIsValidSiteName:
    """Test suite for _is_valid_site_name edge cases"""

    @pytest.fixture
    def site_manager(self, tmp_path, mock_nginx_manager, mock_mysql_manager):
        with patch('wslaragon.services.sites.SSLManager'):
            from wslaragon.services.sites import SiteManager

            config = MagicMock()
            config.get.side_effect = lambda key, default=None: {
                "sites.tld": ".test",
                "sites.document_root": str(tmp_path / "web"),
                "sites.dir": str(tmp_path / "sites"),
            }.get(key, default)

            return SiteManager(config, mock_nginx_manager, mock_mysql_manager)

    def test_rejects_empty_name(self, site_manager):
        assert site_manager._is_valid_site_name('') is False

    def test_rejects_name_starting_with_dot(self, site_manager):
        assert site_manager._is_valid_site_name('.hidden') is False

    def test_rejects_name_ending_with_hyphen(self, site_manager):
        assert site_manager._is_valid_site_name('mysite-') is False

    def test_rejects_consecutive_dots(self, site_manager):
        assert site_manager._is_valid_site_name('my..site') is False

    def test_rejects_label_starting_with_hyphen(self, site_manager):
        assert site_manager._is_valid_site_name('api.-bad.site') is False

    def test_rejects_label_ending_with_hyphen(self, site_manager):
        assert site_manager._is_valid_site_name('api.bad-.site') is False

    def test_accepts_valid_subdomain_name(self, site_manager):
        assert site_manager._is_valid_site_name('api.v2.myapp') is True
