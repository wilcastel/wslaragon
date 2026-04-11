"""Tests for PHP manager module"""
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import pytest


class TestPHPManagerInit:
    """Test suite for PHPManager.__init__"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    def test_init_sets_config(self, php_manager):
        """Test that init sets config attribute"""
        assert php_manager.config is not None

    def test_init_sets_php_ini_path(self, php_manager):
        """Test that init sets php_ini_path"""
        assert php_manager.php_ini_path is not None


class TestPHPManagerGetInstalledVersions:
    """Test suite for get_installed_versions method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_installed_versions_returns_list(self, mock_run, php_manager):
        """Test get_installed_versions returns list of versions"""
        mock_result = MagicMock()
        mock_result.stdout = """ii  php8.1-cli 8.1.2 amd64
ii  php8.1-fpm 8.1.2 amd64
ii  php8.2-cli 8.2.3 amd64
ii  php8.3-cli 8.3.1 amd64
"""
        mock_run.return_value = mock_result

        result = php_manager.get_installed_versions()
        
        assert '8.1' in result
        assert '8.2' in result
        assert '8.3' in result

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_installed_versions_returns_empty_on_error(self, mock_run, php_manager):
        """Test get_installed_versions returns empty list on error"""
        mock_run.side_effect = Exception("Command failed")

        result = php_manager.get_installed_versions()
        
        assert result == []

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_installed_versions_deduplicates(self, mock_run, php_manager):
        """Test get_installed_versions deduplicates versions"""
        mock_result = MagicMock()
        mock_result.stdout = """ii  php8.1-cli 8.1.2 amd64
ii  php8.1-fpm 8.1.2 amd64
ii  php8.1-common 8.1.2 amd64
"""
        mock_run.return_value = mock_result

        result = php_manager.get_installed_versions()
        
        assert result.count('8.1') == 1


class TestPHPManagerGetCurrentVersion:
    """Test suite for get_current_version method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_current_version_returns_version(self, mock_run, php_manager):
        """Test get_current_version returns version string"""
        mock_result = MagicMock()
        mock_result.stdout = "PHP 8.3.1 (cli) (built: Jan  1 2024 00:00:00) (NTS)\n"
        mock_run.return_value = mock_result

        result = php_manager.get_current_version()
        
        assert result == "8.3.1"

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_current_version_returns_none_on_error(self, mock_run, php_manager):
        """Test get_current_version returns None on error"""
        mock_run.side_effect = Exception("Command failed")

        result = php_manager.get_current_version()
        
        assert result is None

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_current_version_handles_no_match(self, mock_run, php_manager):
        """Test get_current_version handles no version match"""
        mock_result = MagicMock()
        mock_result.stdout = "No PHP version found"
        mock_run.return_value = mock_result

        result = php_manager.get_current_version()
        
        assert result is None


class TestPHPManagerSwitchVersion:
    """Test suite for switch_version method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_success(self, mock_run, php_manager):
        """Test switch_version succeeds"""
        mock_result = MagicMock()
        mock_result.stdout = "active\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = php_manager.switch_version("8.2")
        
        assert result is True
        mock_run.assert_called()

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_calls_update_alternatives(self, mock_run, php_manager):
        """Test switch_version calls update-alternatives"""
        mock_result = MagicMock()
        mock_result.stdout = "inactive\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager.switch_version("8.2")
        
        first_call = mock_run.call_args_list[0]
        assert 'update-alternatives' in first_call[0][0]
        assert '/usr/bin/php8.2' in first_call[0][0]

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_starts_fpm_if_active(self, mock_run, php_manager):
        """Test switch_version starts FPM service if active version"""
        mock_result = MagicMock()
        mock_result.stdout = "active\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager.switch_version("8.2")
        
        calls = mock_run.call_args_list
        fpm_calls = [c for c in calls if 'php' in str(c) and 'fpm' in str(c)]
        assert len(fpm_calls) >= 1

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_returns_false_on_exception(self, mock_run, php_manager):
        """Test switch_version returns False on exception"""
        mock_run.side_effect = Exception("Error")

        result = php_manager.switch_version("8.2")
        
        assert result is False


class TestPHPManagerReadIni:
    """Test suite for read_ini method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('builtins.open', create=True)
    def test_read_ini_parses_config(self, mock_file, php_manager):
        """Test read_ini parses php.ini file"""
        ini_content = """memory_limit = 256M
upload_max_filesize = 128M
post_max_size = 128M
; This is a comment
max_execution_time = 60
"""
        mock_file.return_value.__enter__.return_value.__iter__ = lambda self: iter(ini_content.split('\n'))

        result = php_manager.read_ini()
        
        assert 'memory_limit' in result
        assert result['memory_limit'] == '256M'
        assert 'upload_max_filesize' in result
        assert result['post_max_size'] == '128M'

    @patch('builtins.open', create=True)
    def test_read_ini_skips_comments(self, mock_file, php_manager):
        """Test read_ini skips comment lines"""
        ini_content = """; This is a comment
memory_limit = 256M
; Another comment
"""
        mock_file.return_value.__enter__.return_value.__iter__ = lambda self: iter(ini_content.split('\n'))

        result = php_manager.read_ini()
        
        assert 'memory_limit' in result
        assert len(result) == 1

    @patch('builtins.open', side_effect=Exception("File not found"))
    def test_read_ini_returns_empty_on_error(self, mock_file, php_manager):
        """Test read_ini returns empty dict on error"""
        result = php_manager.read_ini()
        
        assert result == {}


class TestPHPManagerWriteIni:
    """Test suite for write_ini method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.Popen')
    @patch('builtins.open', create=True)
    def test_write_ini_updates_existing_values(self, mock_file, mock_popen, php_manager):
        """Test write_ini updates existing config values"""
        ini_content = "memory_limit = 128M\n"
        mock_file.return_value.__enter__.return_value.readlines.return_value = ini_content.split('\n')
        
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process

        result = php_manager.write_ini({'memory_limit': '256M'})
        
        assert result is True

    @patch('wslaragon.services.php.subprocess.Popen')
    @patch('builtins.open', create=True)
    def test_write_ini_adds_new_values(self, mock_file, mock_popen, php_manager):
        """Test write_ini adds new config values"""
        ini_content = "memory_limit = 128M\n"
        mock_file.return_value.__enter__.return_value.readlines.return_value = ini_content.split('\n')
        
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process

        result = php_manager.write_ini({'new_directive': 'value'})
        
        assert result is True

    @patch('wslaragon.services.php.subprocess.Popen')
    @patch('builtins.open', side_effect=Exception("Error"))
    def test_write_ini_returns_false_on_error(self, mock_file, mock_popen, php_manager):
        """Test write_ini returns False on error"""
        result = php_manager.write_ini({'memory_limit': '256M'})
        
        assert result is False


class TestPHPManagerUpdateConfig:
    """Test suite for update_config method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_update_config_success(self, mock_run, php_manager):
        """Test update_config succeeds"""
        mock_result = MagicMock()
        mock_result.stdout = "PHP 8.3.1\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        php_manager.write_ini = MagicMock(return_value=True)

        result = php_manager.update_config('memory_limit', '256M')
        
        assert result is True

    @patch('wslaragon.services.php.subprocess.run')
    def test_update_config_calls_write_ini(self, mock_run, php_manager):
        """Test update_config calls write_ini"""
        mock_result = MagicMock()
        mock_result.stdout = "PHP 8.3.1\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        php_manager.write_ini = MagicMock(return_value=True)

        php_manager.update_config('memory_limit', '256M')
        
        php_manager.write_ini.assert_called_once_with({'memory_limit': '256M'})

    @patch('wslaragon.services.php.subprocess.run')
    def test_update_config_restarts_fpm(self, mock_run, php_manager):
        """Test update_config restarts PHP-FPM"""
        mock_result = MagicMock()
        mock_result.stdout = "PHP 8.3.1\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        php_manager.write_ini = MagicMock(return_value=True)

        php_manager.update_config('memory_limit', '256M')
        
        restart_calls = [c for c in mock_run.call_args_list if 'restart' in str(c)]
        assert len(restart_calls) >= 1

    def test_update_config_returns_false_on_write_failure(self, php_manager):
        """Test update_config returns False when write_ini fails"""
        php_manager.write_ini = MagicMock(return_value=False)

        result = php_manager.update_config('memory_limit', '256M')
        
        assert result is False


class TestPHPManagerGetExtensions:
    """Test suite for get_extensions method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_extensions_returns_list(self, mock_run, php_manager):
        """Test get_extensions returns list of extensions"""
        mock_result = MagicMock()
        mock_result.stdout = """curl
mbstring
xml
json
mysqli
"""
        mock_run.return_value = mock_result

        result = php_manager.get_extensions()
        
        assert 'curl' in result
        assert 'mbstring' in result
        assert 'xml' in result

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_extensions_returns_empty_on_error(self, mock_run, php_manager):
        """Test get_extensions returns empty list on error"""
        mock_run.side_effect = Exception("Command failed")

        result = php_manager.get_extensions()
        
        assert result == []

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_extensions_strips_whitespace(self, mock_run, php_manager):
        """Test get_extensions strips whitespace from extensions"""
        mock_result = MagicMock()
        mock_result.stdout = "curl\nmbstring\n\nxml\n"
        mock_run.return_value = mock_result

        result = php_manager.get_extensions()
        
        assert '' not in result
        assert all(ext.strip() == ext for ext in result if ext)


class TestPHPManagerEnableExtension:
    """Test suite for enable_extension method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_enable_extension_success(self, mock_run, php_manager):
        """Test enable_extension succeeds"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = php_manager.enable_extension("mysqli")
        
        assert result is True

    @patch('wslaragon.services.php.subprocess.run')
    def test_enable_extension_calls_phpenmod(self, mock_run, php_manager):
        """Test enable_extension calls phpenmod"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager.enable_extension("mysqli")
        
        first_call = mock_run.call_args_list[0]
        assert 'phpenmod' in first_call[0][0]
        assert 'mysqli' in first_call[0][0]

    @patch('wslaragon.services.php.subprocess.run')
    def test_enable_extension_restarts_fpm(self, mock_run, php_manager):
        """Test enable_extension restarts PHP-FPM"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager.enable_extension("mysqli")
        
        calls = mock_run.call_args_list
        restart_calls = [c for c in calls if 'restart' in str(c)]
        assert len(restart_calls) >= 1

    @patch('wslaragon.services.php.subprocess.run')
    def test_enable_extension_returns_false_on_error(self, mock_run, php_manager):
        """Test enable_extension returns False on error"""
        mock_run.side_effect = Exception("Error")

        result = php_manager.enable_extension("mysqli")
        
        assert result is False


class TestPHPManagerDisableExtension:
    """Test suite for disable_extension method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_disable_extension_success(self, mock_run, php_manager):
        """Test disable_extension succeeds"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = php_manager.disable_extension("mysqli")
        
        assert result is True

    @patch('wslaragon.services.php.subprocess.run')
    def test_disable_extension_calls_phpdismod(self, mock_run, php_manager):
        """Test disable_extension calls phpdismod"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager.disable_extension("mysqli")
        
        first_call = mock_run.call_args_list[0]
        assert 'phpdismod' in first_call[0][0]
        assert 'mysqli' in first_call[0][0]

    @patch('wslaragon.services.php.subprocess.run')
    def test_disable_extension_restarts_fpm(self, mock_run, php_manager):
        """Test disable_extension restarts PHP-FPM"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager.disable_extension("mysqli")
        
        calls = mock_run.call_args_list
        restart_calls = [c for c in calls if 'restart' in str(c)]
        assert len(restart_calls) >= 1

    @patch('wslaragon.services.php.subprocess.run')
    def test_disable_extension_returns_false_on_error(self, mock_run, php_manager):
        """Test disable_extension returns False on error"""
        mock_run.side_effect = Exception("Error")

        result = php_manager.disable_extension("mysqli")
        
        assert result is False


class TestPHPManagerGetIniDirectives:
    """Test suite for get_ini_directives method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_ini_directives_returns_config(self, mock_run, php_manager):
        """Test get_ini_directives returns config dict"""
        mock_result = MagicMock()
        mock_result.stdout = """Configuration (php.ini)
memory_limit => 256M
upload_max_filesize => 128M
post_max_size => 128M
"""
        mock_run.return_value = mock_result

        result = php_manager.get_ini_directives()
        
        assert isinstance(result, dict)

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_ini_directives_returns_empty_on_error(self, mock_run, php_manager):
        """Test get_ini_directives returns empty dict on error"""
        mock_run.side_effect = Exception("Command failed")

        result = php_manager.get_ini_directives()
        
        assert result == {}

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_ini_directives_calls_php_info(self, mock_run, php_manager):
        """Test get_ini_directives calls php -i"""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        php_manager.get_ini_directives()
        
        mock_run.assert_called_with(['php', '-i'], capture_output=True, text=True)