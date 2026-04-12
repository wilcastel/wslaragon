# Pytest configuration and fixtures
import os
import sys
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def pytest_addoption(parser):
    """Register custom pytest options"""
    parser.addoption("--run-slow", action="store_true", default=False, help="Run slow integration tests")


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "integration: mark a test as an integration test")


def pytest_collection_modifyitems(config, items):
    """Skip slow integration tests unless --run-slow is passed"""
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="Need --run-slow option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def mock_config(tmp_path):
    """Mock configuration for tests using temp directories"""
    config_dir = tmp_path / ".wslaragon"
    config_dir.mkdir(parents=True, exist_ok=True)
    sites_dir = config_dir / "sites"
    sites_dir.mkdir(exist_ok=True)
    ssl_dir = config_dir / "ssl"
    ssl_dir.mkdir(exist_ok=True)
    logs_dir = config_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    config = MagicMock()
    config.config_dir = config_dir
    config.config_file = config_dir / "config.yaml"
    config.sites_dir = sites_dir
    config.ssl_dir = ssl_dir
    config.logs_dir = logs_dir
    
    config.get.side_effect = lambda key, default=None: {
        "php.version": "8.3",
        "php.ini_file": "/etc/php/8.3/fpm/php.ini",
        "php.extensions_dir": "/usr/lib/php/20230831",
        "nginx.config_dir": "/etc/nginx",
        "nginx.sites_available": "/etc/nginx/sites-available",
        "nginx.sites_enabled": "/etc/nginx/sites-enabled",
        "nginx.client_max_body_size": "128M",
        "mysql.data_dir": "/var/lib/mysql",
        "mysql.config_file": "/etc/mysql/mariadb.conf.d/50-server.cnf",
        "mysql.user": "root",
        "mysql.password": "test_password",
        "ssl.dir": str(ssl_dir),
        "ssl.ca_file": str(ssl_dir / "rootCA.pem"),
        "ssl.ca_key": str(ssl_dir / "rootCA-key.pem"),
        "sites.tld": ".test",
        "sites.document_root": str(tmp_path / "web"),
        "sites.dir": str(sites_dir),
        "windows.hosts_file": "/mnt/c/Windows/System32/drivers/etc/hosts",
        "supabase.postgres_port": 5433,
        "supabase.postgres_password": "postgres",
        "supabase.api_port": 8081,
    }.get(key, default)
    config.set = MagicMock()
    config.save = MagicMock()
    return config


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for tests"""
    return tmp_path


@pytest.fixture
def mock_site_data():
    """Mock site data structure"""
    return {
        "testsite": {
            "name": "testsite",
            "domain": "testsite.test",
            "document_root": "/home/test/web/testsite",
            "web_root": "/home/test/web/testsite",
            "php": True,
            "mysql": True,
            "ssl": True,
            "proxy_port": None,
            "database": "testsite_db",
            "db_type": "mysql",
            "created_at": "2024-01-01T00:00:00",
            "enabled": True,
        }
    }


@pytest.fixture
def mock_sites_file(tmp_path, mock_site_data):
    """Create a temporary sites.json file"""
    sites_file = tmp_path / "sites.json"
    with open(sites_file, "w") as f:
        json.dump(mock_site_data, f)
    return sites_file


@pytest.fixture
def mock_nginx_manager():
    """Mock Nginx manager"""
    nginx = MagicMock()
    nginx.add_site.return_value = (True, None)
    nginx.remove_site.return_value = (True, None)
    nginx.enable_site.return_value = True
    nginx.disable_site.return_value = True
    return nginx


@pytest.fixture
def mock_mysql_manager():
    """Mock MySQL manager"""
    mysql = MagicMock()
    mysql.create_database.return_value = (True, None)
    mysql.drop_database.return_value = True
    mysql.database_exists.return_value = False
    mysql.get_database_size.return_value = "1.5MB"
    return mysql


@pytest.fixture
def mock_ssl_manager():
    """Mock SSL manager"""
    ssl = MagicMock()
    ssl.setup_ssl_for_site.return_value = {'success': True}
    ssl.create_ca.return_value = True
    ssl.generate_cert.return_value = {'success': True}
    return ssl


@pytest.fixture
def mock_site_manager():
    """Mock Site manager"""
    site_manager = MagicMock()
    site_manager.get_site.return_value = None
    site_manager.create_site.return_value = {'success': True, 'site': {}}
    site_manager.delete_site.return_value = {'success': True}
    site_manager.list_sites.return_value = []
    site_manager.fix_permissions.return_value = None
    return site_manager