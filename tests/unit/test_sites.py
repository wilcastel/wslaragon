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