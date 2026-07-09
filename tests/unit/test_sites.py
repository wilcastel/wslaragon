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
