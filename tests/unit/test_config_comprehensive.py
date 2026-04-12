"""Comprehensive tests for Config class - testing actual implementation."""
import os
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from wslaragon.core.config import Config


class TestConfigInit:
    """Test Config initialization."""

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_init_creates_directories(self, mock_load_dotenv, mock_home, tmp_path):
        """Test __init__ creates all required directories."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.config_dir.exists()
        assert config.sites_dir.exists()
        assert config.ssl_dir.exists()
        assert config.logs_dir.exists()
        assert config.config_dir == tmp_path / ".wslaragon"

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_init_creates_default_config(self, mock_load_dotenv, mock_home, tmp_path):
        """Test __init__ creates default config when file missing."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.config_file.exists()
        assert config.get('php.version') == '8.3'
        assert config.get('sites.tld') == '.test'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_init_loads_existing_config(self, mock_load_dotenv, mock_home, tmp_path):
        """Test __init__ loads existing config file."""
        mock_home.return_value = tmp_path
        config_dir = tmp_path / ".wslaragon"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        existing_config = {
            "php": {"version": "8.2"},
            "sites": {"tld": ".local", "document_root": "/custom/path"}
        }
        config_file = config_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(existing_config, f)
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('php.version') == '8.2'
        assert config.get('sites.tld') == '.local'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    @patch('wslaragon.core.config.os.getenv')
    def test_init_env_vars_override(self, mock_getenv, mock_load_dotenv, mock_home, tmp_path):
        """Test environment variables override config values."""
        mock_home.return_value = tmp_path
        
        env_values = {
            'DB_USER': 'custom_user',
            'DB_PASSWORD': 'custom_pass',
            'DOCUMENT_ROOT': '/custom/docroot'
        }
        
        def getenv_side_effect(key, default=''):
            return env_values.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        config = Config()
        
        assert config.get('mysql.user') == 'custom_user'
        assert config.get('mysql.password') == 'custom_pass'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_init_env_vars_override_existing_config(self, mock_load_dotenv, mock_home, tmp_path):
        """Test env vars override values even when config.yaml exists."""
        mock_home.return_value = tmp_path
        config_dir = tmp_path / ".wslaragon"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        existing_config = {
            "php": {"version": "8.3"},
            "mysql": {"user": "old_user", "password": "old_pass"},
            "sites": {"tld": ".test"}
        }
        config_file = config_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(existing_config, f)
        
        with patch.dict(os.environ, {'DB_USER': 'new_user', 'DB_PASSWORD': 'new_pass'}):
            config = Config()
        
        assert config.get('mysql.user') == 'new_user'
        assert config.get('mysql.password') == 'new_pass'


class TestEnsureDirs:
    """Test _ensure_dirs method."""

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_ensure_dirs_creates_all(self, mock_load_dotenv, mock_home, tmp_path):
        """Test _ensure_dirs creates config, sites, ssl, logs directories."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert (tmp_path / ".wslaragon").exists()
        assert (tmp_path / ".wslaragon" / "sites").exists()
        assert (tmp_path / ".wslaragon" / "ssl").exists()
        assert (tmp_path / ".wslaragon" / "logs").exists()

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_ensure_dirs_idempotent(self, mock_load_dotenv, mock_home, tmp_path):
        """Test _ensure_dirs is idempotent - can be called multiple times."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            config._ensure_dirs()
            config._ensure_dirs()
        
        assert config.config_dir.exists()


class TestLoadConfig:
    """Test _load_config method."""

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_load_config_missing_file(self, mock_load_dotenv, mock_home, tmp_path):
        """Test _load_config creates default when file missing."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('php.version') == '8.3'
        assert config.get('nginx.client_max_body_size') == '128M'
        assert config.get('mysql.user') == 'root'
        assert config.config_file.exists()

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_load_config_existing_file(self, mock_load_dotenv, mock_home, tmp_path):
        """Test _load_config reads existing YAML file."""
        mock_home.return_value = tmp_path
        config_dir = tmp_path / ".wslaragon"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        
        custom_config = {
            "php": {"version": "8.1"},
            "nginx": {"config_dir": "/custom/nginx"},
            "custom_section": {"key": "value"}
        }
        with open(config_file, 'w') as f:
            yaml.dump(custom_config, f)
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('php.version') == '8.1'
        assert config.get('nginx.config_dir') == '/custom/nginx'
        assert config.get('custom_section.key') == 'value'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_load_config_corrupted_yaml(self, mock_load_dotenv, mock_home, tmp_path):
        """Test _load_config handles corrupted YAML file gracefully."""
        mock_home.return_value = tmp_path
        config_dir = tmp_path / ".wslaragon"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        
        # Write invalid YAML
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [[")
        
        with patch.dict(os.environ, {}, clear=True):
            # This should raise a YAMLError which we need to handle
            # For now, we expect it to propagate since Config doesn't catch it
            with pytest.raises(yaml.YAMLError):
                Config()

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_load_config_empty_file(self, mock_load_dotenv, mock_home, tmp_path):
        """Test _load_config handles empty config file - currently raises TypeError."""
        mock_home.return_value = tmp_path
        config_dir = tmp_path / ".wslaragon"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.yaml"
        
        config_file.touch()  # Create empty file
        
        # Empty YAML returnsNone, code expects dict - this is a known limitation
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(TypeError):
                Config()


class TestSave:
    """Test save method."""

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_save_writes_yaml(self, mock_load_dotenv, mock_home, tmp_path):
        """Test save writes config to YAML file."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        config.set('custom.key', 'test_value')
        
        # Verify file was written
        assert config.config_file.exists()
        with open(config.config_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded['custom']['key'] == 'test_value'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_save_preserves_nested_structure(self, mock_load_dotenv, mock_home, tmp_path):
        """Test save preserves nested config structure."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        config.set('php.version', '8.4')
        config.set('php.custom_setting', 'enabled')
        config.save()
        
        with open(config.config_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded['php']['version'] == '8.4'
        assert loaded['php']['custom_setting'] == 'enabled'
        assert 'nginx' in loaded  # Other sections preserved


class TestGet:
    """Test get method."""

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_get_simple_key(self, mock_load_dotenv, mock_home, tmp_path):
        """Test get with top-level key."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        # Need to manually set a top-level key since default config is nested
        config.config['top_level'] = 'value'
        
        assert config.get('top_level') == 'value'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_get_nested_key(self, mock_load_dotenv, mock_home, tmp_path):
        """Test get with nested key using dot notation."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('php.version') == '8.3'
        assert config.get('nginx.config_dir') == '/etc/nginx'
        assert config.get('ssl.ca_file') == str(tmp_path / ".wslaragon" / "ssl" / "rootCA.pem")

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_get_deeply_nested_key(self, mock_load_dotenv, mock_home, tmp_path):
        """Test get with deeply nested key."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        config.config['level1'] = {'level2': {'level3': {'level4': 'deep_value'}}}
        
        assert config.get('level1.level2.level3.level4') == 'deep_value'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_get_missing_key_returns_default(self, mock_load_dotenv, mock_home, tmp_path):
        """Test get returns default for missing keys."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('nonexistent') is None
        assert config.get('nonexistent', 'default_val') == 'default_val'
        assert config.get('php.nonexistent', 'fallback') == 'fallback'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_get_missing_nested_key_returns_default(self, mock_load_dotenv, mock_home, tmp_path):
        """Test get returns default for missing nested keys."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('deep.nonexistent.key', 'fallback') == 'fallback'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_get_null_value_returns_default(self, mock_load_dotenv, mock_home, tmp_path):
        """Test get returns default when value is None."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        config.config['null_key'] = None
        
        assert config.get('null_key', 'default') == 'default'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_get_non_dict_intermediate(self, mock_load_dotenv, mock_home, tmp_path):
        """Test get handles non-dict intermediate values."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        config.config['string_val'] = 'not_a_dict'
        
        # Trying to get nested key from string should return default
        assert config.get('string_val.nested', 'default') == 'default'


class TestSet:
    """Test set method."""

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_set_simple_key(self, mock_load_dotenv, mock_home, tmp_path):
        """Test set with top-level key."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        config.set('new_key', 'new_value')
        
        assert config.config['new_key'] == 'new_value'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_set_nested_key(self, mock_load_dotenv, mock_home, tmp_path):
        """Test set with nested key using dot notation."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        config.set('custom.section.key', 'value')
        
        assert config.config['custom']['section']['key'] == 'value'
        assert config.get('custom.section.key') == 'value'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_set_creates_nested_structure(self, mock_load_dotenv, mock_home, tmp_path):
        """Test set creates intermediate nested dicts."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        config.set('a.b.c.d.e', 'deep_value')
        
        assert config.config['a']['b']['c']['d']['e'] == 'deep_value'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_set_overwrites_existing(self, mock_load_dotenv, mock_home, tmp_path):
        """Test set overwrites existing values."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        original = config.get('php.version')
        config.set('php.version', '8.4')
        
        assert config.get('php.version') == '8.4'
        assert original != '8.4'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_set_saves_to_file(self, mock_load_dotenv, mock_home, tmp_path):
        """Test set automatically saves config to file."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        config.set('test.auto_save', 'yes')
        
        # Read file directly
        with open(config.config_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded['test']['auto_save'] == 'yes'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_set_on_non_dict_breaks(self, mock_load_dotenv, mock_home, tmp_path):
        """Test set on non-dict intermediate values handles gracefully."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        # Set a string value
        config.config['test_string'] = 'string_value'
        
        # Try to set nested under the string - should not crash
        config.set('test_string.nested', 'value')
        
        # The string should still exist (set doesn't overwrite it)
        assert config.config['test_string'] == 'string_value'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_set_deep_path_through_non_dict_breaks(self, mock_load_dotenv, mock_home, tmp_path):
        """Test set breaks out of loop when hitting non-dict in deep path."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        # Create a non-dict at a.b
        config.config['a'] = {'b': 'string_value'}
        
        # Try to set a.b.c.d - should break at a.b since it's not a dict
        config.set('a.b.c.d', 'value')
        
        # Should not modify the existing string
        assert config.config['a']['b'] == 'string_value'


class TestConfigIntegration:
    """Integration tests for Config class."""

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_full_lifecycle(self, mock_load_dotenv, mock_home, tmp_path):
        """Test full Config lifecycle: create, read, update, save."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            # Create new config
            config = Config()
            
            # Verify defaults
            assert config.get('php.version') == '8.3'
            
            # Modify values
            config.set('php.version', '8.2')
            config.set('custom.new_setting', 'enabled')
            
            # Verify in-memory
            assert config.get('php.version') == '8.2'
            assert config.get('custom.new_setting') == 'enabled'
            
            # Create new instance - should load from file
            config2 = Config()
            
            assert config2.get('php.version') == '8.2'
            assert config2.get('custom.new_setting') == 'enabled'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_concurrent_get_set_operations(self, mock_load_dotenv, mock_home, tmp_path):
        """Test multiple get/set operations maintain consistency."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        # Set multiple values
        config.set('app.name', 'WSLaragon')
        config.set('app.version', '1.0.0')
        config.set('app.debug', True)
        
        # Verify all
        assert config.get('app.name') == 'WSLaragon'
        assert config.get('app.version') == '1.0.0'
        assert config.get('app.debug') is True
        
        # Modify and verify
        config.set('app.debug', False)
        assert config.get('app.debug') is False


class TestConfigDefaultValues:
    """Test default configuration values."""

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_default_php_config(self, mock_load_dotenv, mock_home, tmp_path):
        """Test default PHP configuration values."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('php.version') == '8.3'
        assert config.get('php.ini_file') == '/etc/php/8.3/fpm/php.ini'
        assert config.get('php.extensions_dir') == '/usr/lib/php/20230831'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_default_nginx_config(self, mock_load_dotenv, mock_home, tmp_path):
        """Test default Nginx configuration values."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('nginx.config_dir') == '/etc/nginx'
        assert config.get('nginx.sites_available') == '/etc/nginx/sites-available'
        assert config.get('nginx.sites_enabled') == '/etc/nginx/sites-enabled'
        assert config.get('nginx.client_max_body_size') == '128M'

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_default_mysql_config(self, mock_load_dotenv, mock_home, tmp_path):
        """Test default MySQL configuration values."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('mysql.data_dir') == '/var/lib/mysql'
        assert config.get('mysql.config_file') == '/etc/mysql/mariadb.conf.d/50-server.cnf'
        assert config.get('mysql.user') == 'root'
        assert config.get('mysql.password') == ''

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_default_ssl_config(self, mock_load_dotenv, mock_home, tmp_path):
        """Test default SSL configuration values."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        ssl_dir = tmp_path / ".wslaragon" / "ssl"
        assert config.get('ssl.dir') == str(ssl_dir)
        assert config.get('ssl.ca_file') == str(ssl_dir / "rootCA.pem")
        assert config.get('ssl.ca_key') == str(ssl_dir / "rootCA-key.pem")

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_default_sites_config(self, mock_load_dotenv, mock_home, tmp_path):
        """Test default sites configuration values."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('sites.tld') == '.test'
        assert config.get('sites.document_root') == str(tmp_path / "web")

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_default_windows_config(self, mock_load_dotenv, mock_home, tmp_path):
        """Test default Windows configuration values."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.get('windows.hosts_file') == '/mnt/c/Windows/System32/drivers/etc/hosts'


class TestConfigPathAttributes:
    """Test Config path attributes."""

    @patch('wslaragon.core.config.Path.home')
    @patch('wslaragon.core.config.load_dotenv')
    def test_path_attributes(self, mock_load_dotenv, mock_home, tmp_path):
        """Test Config path attributes are set correctly."""
        mock_home.return_value = tmp_path
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
        
        assert config.config_dir == tmp_path / ".wslaragon"
        assert config.config_file == tmp_path / ".wslaragon" / "config.yaml"
        assert config.sites_dir == tmp_path / ".wslaragon" / "sites"
        assert config.ssl_dir == tmp_path / ".wslaragon" / "ssl"
        assert config.logs_dir == tmp_path / ".wslaragon" / "logs"