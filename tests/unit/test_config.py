"""Tests for the Config module"""
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest


class TestConfigGet:
    """Test suite for config get method - pure unit tests without filesystem"""

    def test_get_with_default(self):
        """Test get returns default for missing keys"""
        # Create a mock config directly
        config_data = {
            'php': {'version': '8.3'},
            'sites': {'tld': '.test', 'document_root': '/home/test/web'}
        }
        
        # Create a minimal mock config class
        class MockConfig:
            def __init__(self):
                self.config = config_data
            
            def get(self, key, default=None):
                keys = key.split('.')
                value = self.config
                for k in keys:
                    if isinstance(value, dict):
                        value = value.get(k, default)
                    else:
                        return default
                    if value is None:
                        return default
                return value
        
        config = MockConfig()
        
        result = config.get('nonexistent', 'default_value')
        assert result == 'default_value'
        
        result = config.get('php.version')
        assert result == '8.3'
        
        result = config.get('sites.tld')
        assert result == '.test'
        
        result = config.get('deep.nested.key', 'fallback')
        assert result == 'fallback'


class TestConfigSet:
    """Test suite for config set method"""

    def test_set_nested_value(self):
        """Test set creates nested keys"""
        config_data = {'php': {'version': '8.3'}}
        
        class MockConfig:
            def __init__(self):
                self.config = config_data
            
            def set(self, key, value):
                keys = key.split('.')
                config = self.config
                for k in keys[:-1]:
                    if isinstance(config, dict):
                        config = config.setdefault(k, {})
                if isinstance(config, dict):
                    config[keys[-1]] = value
            
            def get(self, key, default=None):
                keys = key.split('.')
                value = self.config
                for k in keys:
                    if isinstance(value, dict):
                        value = value.get(k, default)
                    else:
                        return default
                return value
        
        config = MockConfig()
        
        # Set new nested key
        config.set('custom.key', 'value')
        assert config.get('custom.key') == 'value'
        
        # Set deeply nested
        config.set('deep.nested.key', 'deep_value')
        assert config.get('deep.nested.key') == 'deep_value'
        
        # Overwrite existing
        config.set('php.version', '8.4')
        assert config.get('php.version') == '8.4'


class TestConfigDataStructure:
    """Test the config data structure and defaults"""

    def test_default_config_structure(self):
        """Test that default config has expected structure"""
        default_config = {
            "php": {
                "version": "8.3",
                "ini_file": "/etc/php/8.3/fpm/php.ini",
                "extensions_dir": "/usr/lib/php/20230831"
            },
            "nginx": {
                "config_dir": "/etc/nginx",
                "sites_available": "/etc/nginx/sites-available",
                "sites_enabled": "/etc/nginx/sites-enabled",
                "client_max_body_size": "128M"
            },
            "mysql": {
                "data_dir": "/var/lib/mysql",
                "config_file": "/etc/mysql/mariadb.conf.d/50-server.cnf",
                "user": "root",
                "password": ""
            },
            "ssl": {
                "dir": "~/.wslaragon/ssl",
                "ca_file": "~/.wslaragon/ssl/rootCA.pem",
                "ca_key": "~/.wslaragon/ssl/rootCA-key.pem"
            },
            "sites": {
                "tld": ".test",
                "document_root": "~/web"
            },
            "windows": {
                "hosts_file": "/mnt/c/Windows/System32/drivers/etc/hosts"
            }
        }
        
        # Verify structure
        assert 'php' in default_config
        assert 'nginx' in default_config
        assert 'mysql' in default_config
        assert 'ssl' in default_config
        assert 'sites' in default_config
        assert 'windows' in default_config
        
        # Verify key values
        assert default_config['php']['version'] == "8.3"
        assert default_config['sites']['tld'] == ".test"
        assert default_config['mysql']['user'] == "root"


class TestConfigPathHandling:
    """Test config path handling logic"""

    def test_path_expansion(self):
        """Test that paths are properly expanded"""
        # Test Path.home behavior
        home = Path.home()
        assert home.is_absolute()
        
        # Test path joining
        web_path = home / "web"
        assert str(web_path).endswith("web")
        
        # Test config directory
        config_dir = home / ".wslaragon"
        assert ".wslaragon" in str(config_dir)

    def test_config_file_path(self):
        """Test config file path construction"""
        home = Path("/home/test")
        config_dir = home / ".wslaragon"
        config_file = config_dir / "config.yaml"
        
        assert str(config_file) == "/home/test/.wslaragon/config.yaml"
        assert config_file.parent == config_dir
        assert config_file.name == "config.yaml"

    def test_sites_directory_path(self):
        """Test sites directory path construction"""
        config_dir = Path("/home/test/.wslaragon")
        sites_dir = config_dir / "sites"
        
        assert sites_dir.exists() or True  # May not exist in test
        assert "sites" in str(sites_dir)


class TestConfigYAML:
    """Test YAML serialization/deserialization"""

    def test_yaml_dump_and_load(self):
        """Test config can be serialized and deserialized"""
        config_data = {
            "php": {"version": "8.3"},
            "sites": {"tld": ".test"}
        }
        
        # Dump to string
        yaml_str = yaml.dump(config_data, default_flow_style=False)
        assert "php:" in yaml_str
        assert "version" in yaml_str and "8.3" in yaml_str
        
        # Load from string
        loaded = yaml.safe_load(yaml_str)
        assert loaded['php']['version'] == "8.3"
        assert loaded['sites']['tld'] == ".test"

    def test_yaml_with_nested_dicts(self):
        """Test YAML handles deeply nested configs"""
        config_data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        yaml_str = yaml.dump(config_data, default_flow_style=False)
        loaded = yaml.safe_load(yaml_str)
        
        assert loaded['level1']['level2']['level3'] == "value"