"""Tests for php_commands CLI module"""
import pytest
import subprocess
from click.testing import CliRunner
from unittest.mock import patch, MagicMock


class TestPhpVersionsCommand:
    """Test suite for 'php versions' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.php_commands.Config') as mock_config, \
             patch('wslaragon.cli.php_commands.PHPManager') as mock_php:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_php_instance = MagicMock()
            mock_php.return_value = mock_php_instance
            yield {
                'config': mock_config_instance,
                'php': mock_php_instance,
            }

    def test_php_versions_success(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].get_installed_versions.return_value = ['8.1', '8.2', '8.3']
        mock_deps['php'].get_current_version.return_value = '8.3'

        result = runner.invoke(php, ['versions'])

        assert result.exit_code == 0
        assert '8.1' in result.output
        assert '8.2' in result.output
        assert '8.3' in result.output
        mock_deps['php'].get_installed_versions.assert_called_once()

    def test_php_versions_shows_current_marker(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].get_installed_versions.return_value = ['8.2', '8.3']
        mock_deps['php'].get_current_version.return_value = '8.3'

        result = runner.invoke(php, ['versions'])

        assert result.exit_code == 0
        assert 'Current' in result.output

    def test_php_versions_empty_list(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].get_installed_versions.return_value = []
        mock_deps['php'].get_current_version.return_value = None

        result = runner.invoke(php, ['versions'])

        assert result.exit_code == 0
        assert 'PHP Versions' in result.output

    def test_php_versions_no_current_version(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].get_installed_versions.return_value = ['8.1', '8.2']
        mock_deps['php'].get_current_version.return_value = None

        result = runner.invoke(php, ['versions'])

        assert result.exit_code == 0
        assert 'Available' in result.output

    def test_php_versions_partial_current_match(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].get_installed_versions.return_value = ['8.1', '8.2']
        mock_deps['php'].get_current_version.return_value = '8.1.5'

        result = runner.invoke(php, ['versions'])

        assert result.exit_code == 0
        assert 'Current' in result.output


class TestPhpSwitchCommand:
    """Test suite for 'php switch <version>' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.php_commands.Config') as mock_config, \
             patch('wslaragon.cli.php_commands.PHPManager') as mock_php:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_php_instance = MagicMock()
            mock_php.return_value = mock_php_instance
            yield {
                'config': mock_config_instance,
                'php': mock_php_instance,
            }

    def test_php_switch_success(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].switch_version.return_value = True

        result = runner.invoke(php, ['switch', '8.2'])

        assert result.exit_code == 0
        assert 'Switched to PHP 8.2' in result.output
        mock_deps['php'].switch_version.assert_called_once_with('8.2')

    def test_php_switch_failure(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].switch_version.return_value = False

        result = runner.invoke(php, ['switch', '8.2'])

        assert result.exit_code == 0
        assert 'Failed to switch' in result.output
        mock_deps['php'].switch_version.assert_called_once_with('8.2')

    def test_php_switch_displays_version_in_message(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].switch_version.return_value = True

        result = runner.invoke(php, ['switch', '8.3'])

        assert result.exit_code == 0
        assert '8.3' in result.output


class TestPhpExtensionsCommand:
    """Test suite for 'php extensions' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.php_commands.Config') as mock_config, \
             patch('wslaragon.cli.php_commands.PHPManager') as mock_php:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_php_instance = MagicMock()
            mock_php.return_value = mock_php_instance
            yield {
                'config': mock_config_instance,
                'php': mock_php_instance,
            }

    def test_php_extensions_success(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].get_extensions.return_value = ['curl', 'mbstring', 'mysqli', 'xml']

        result = runner.invoke(php, ['extensions'])

        assert result.exit_code == 0
        assert 'curl' in result.output
        assert 'mbstring' in result.output
        assert 'mysqli' in result.output
        mock_deps['php'].get_extensions.assert_called_once()

    def test_php_extensions_empty_list(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].get_extensions.return_value = []

        result = runner.invoke(php, ['extensions'])

        assert result.exit_code == 0
        assert 'Extension' in result.output

    def test_php_extensions_displays_in_table(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].get_extensions.return_value = ['json', 'openssl']

        result = runner.invoke(php, ['extensions'])

        assert result.exit_code == 0
        assert 'json' in result.output
        assert 'openssl' in result.output


class TestPhpEnableExtCommand:
    """Test suite for 'php enable-ext <ext>' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.php_commands.Config') as mock_config, \
             patch('wslaragon.cli.php_commands.PHPManager') as mock_php:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_php_instance = MagicMock()
            mock_php.return_value = mock_php_instance
            yield {
                'config': mock_config_instance,
                'php': mock_php_instance,
            }

    def test_php_enable_ext_success(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].enable_extension.return_value = True

        result = runner.invoke(php, ['enable-ext', 'mysqli'])

        assert result.exit_code == 0
        assert 'mysqli enabled' in result.output
        mock_deps['php'].enable_extension.assert_called_once_with('mysqli')

    def test_php_enable_ext_failure(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].enable_extension.return_value = False

        result = runner.invoke(php, ['enable-ext', 'mysqli'])

        assert result.exit_code == 0
        assert 'Failed to enable' in result.output
        mock_deps['php'].enable_extension.assert_called_once_with('mysqli')

    def test_php_enable_ext_displays_extension_name(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].enable_extension.return_value = True

        result = runner.invoke(php, ['enable-ext', 'gd'])

        assert result.exit_code == 0
        assert 'gd' in result.output


class TestPhpDisableExtCommand:
    """Test suite for 'php disable-ext <ext>' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.php_commands.Config') as mock_config, \
             patch('wslaragon.cli.php_commands.PHPManager') as mock_php:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_php_instance = MagicMock()
            mock_php.return_value = mock_php_instance
            yield {
                'config': mock_config_instance,
                'php': mock_php_instance,
            }

    def test_php_disable_ext_success(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].disable_extension.return_value = True

        result = runner.invoke(php, ['disable-ext', 'xdebug'])

        assert result.exit_code == 0
        assert 'xdebug disabled' in result.output
        mock_deps['php'].disable_extension.assert_called_once_with('xdebug')

    def test_php_disable_ext_failure(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].disable_extension.return_value = False

        result = runner.invoke(php, ['disable-ext', 'xdebug'])

        assert result.exit_code == 0
        assert 'Failed to disable' in result.output
        mock_deps['php'].disable_extension.assert_called_once_with('xdebug')

    def test_php_disable_ext_displays_extension_name(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].disable_extension.return_value = True

        result = runner.invoke(php, ['disable-ext', 'opcache'])

        assert result.exit_code == 0
        assert 'opcache' in result.output


class TestPhpConfigListCommand:
    """Test suite for 'php config list' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.php_commands.Config') as mock_config, \
             patch('wslaragon.cli.php_commands.PHPManager') as mock_php:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_php_instance = MagicMock()
            mock_php.return_value = mock_php_instance
            yield {
                'config': mock_config_instance,
                'php': mock_php_instance,
            }

    def test_php_config_list_success(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].read_ini.return_value = {
            'memory_limit': '256M',
            'upload_max_filesize': '128M',
            'post_max_size': '128M',
            'max_execution_time': '60',
            'max_input_time': '60',
            'display_errors': 'Off',
            'date.timezone': 'UTC',
        }

        result = runner.invoke(php, ['config', 'list'])

        assert result.exit_code == 0
        assert 'memory_limit' in result.output
        assert '256M' in result.output
        mock_deps['php'].read_ini.assert_called_once()

    def test_php_config_list_shows_not_set(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].read_ini.return_value = {}

        result = runner.invoke(php, ['config', 'list'])

        assert result.exit_code == 0
        assert 'Not set' in result.output

    def test_php_config_list_displays_all_common_keys(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].read_ini.return_value = {
            'memory_limit': '256M',
            'upload_max_filesize': '128M',
            'post_max_size': '128M',
            'max_execution_time': '60',
            'max_input_time': '60',
            'display_errors': 'Off',
            'date.timezone': 'UTC',
        }

        result = runner.invoke(php, ['config', 'list'])

        assert result.exit_code == 0
        assert 'memory_limit' in result.output
        assert 'upload_max_filesize' in result.output
        assert 'post_max_size' in result.output
        assert 'max_execution_time' in result.output
        assert 'max_input_time' in result.output
        assert 'display_errors' in result.output
        assert 'date.timezone' in result.output


class TestPhpConfigSetCommand:
    """Test suite for 'php config set <key> <value>' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.php_commands.Config') as mock_config, \
             patch('wslaragon.cli.php_commands.PHPManager') as mock_php:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_php_instance = MagicMock()
            mock_php.return_value = mock_php_instance
            yield {
                'config': mock_config_instance,
                'php': mock_php_instance,
            }

    @patch('wslaragon.cli.php_commands.subprocess.run')
    def test_php_config_set_success(self, mock_subprocess, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_deps['php'].update_config.return_value = True

        result = runner.invoke(php, ['config', 'set', 'memory_limit', '512M'])

        assert result.exit_code == 0
        assert 'Updated memory_limit to 512M' in result.output
        mock_deps['php'].update_config.assert_called_once_with('memory_limit', '512M')

    @patch('wslaragon.cli.php_commands.subprocess.run')
    def test_php_config_set_sudo_check(self, mock_subprocess, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_deps['php'].update_config.return_value = True

        runner.invoke(php, ['config', 'set', 'memory_limit', '512M'])

        mock_subprocess.assert_called_with(['sudo', '-v'], check=True)

    @patch('wslaragon.cli.php_commands.subprocess.run')
    def test_php_config_set_no_sudo(self, mock_subprocess, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(php, ['config', 'set', 'memory_limit', '512M'])

        assert result.exit_code == 0
        assert 'requires sudo privileges' in result.output
        mock_deps['php'].update_config.assert_not_called()

    @patch('wslaragon.cli.php_commands.subprocess.run')
    def test_php_config_set_failure(self, mock_subprocess, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_deps['php'].update_config.return_value = False

        result = runner.invoke(php, ['config', 'set', 'memory_limit', '512M'])

        assert result.exit_code == 0
        assert 'Failed to update' in result.output

    @patch('wslaragon.cli.php_commands.subprocess.run')
    def test_php_config_set_shows_restart_message(self, mock_subprocess, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_deps['php'].update_config.return_value = True

        result = runner.invoke(php, ['config', 'set', 'memory_limit', '512M'])

        assert result.exit_code == 0
        assert 'PHP-FPM restarted' in result.output


class TestPhpConfigGetCommand:
    """Test suite for 'php config get <key>' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.php_commands.Config') as mock_config, \
             patch('wslaragon.cli.php_commands.PHPManager') as mock_php:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_php_instance = MagicMock()
            mock_php.return_value = mock_php_instance
            yield {
                'config': mock_config_instance,
                'php': mock_php_instance,
            }

    def test_php_config_get_success(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].read_ini.return_value = {
            'memory_limit': '256M',
            'upload_max_filesize': '128M',
        }

        result = runner.invoke(php, ['config', 'get', 'memory_limit'])

        assert result.exit_code == 0
        assert 'memory_limit' in result.output
        assert '256M' in result.output
        mock_deps['php'].read_ini.assert_called_once()

    def test_php_config_get_not_set(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].read_ini.return_value = {}

        result = runner.invoke(php, ['config', 'get', 'nonexistent_key'])

        assert result.exit_code == 0
        assert 'Not set' in result.output

    def test_php_config_get_missing_key(self, runner, mock_deps):
        from wslaragon.cli.php_commands import php

        mock_deps['php'].read_ini.return_value = {
            'memory_limit': '256M',
        }

        result = runner.invoke(php, ['config', 'get', 'upload_max_filesize'])

        assert result.exit_code == 0
        assert 'Not set' in result.output


class TestPhpCommandGroup:
    """Test suite for php command group"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_php_command_group_help(self, runner):
        from wslaragon.cli.php_commands import php

        result = runner.invoke(php, ['--help'])

        assert result.exit_code == 0
        assert 'versions' in result.output
        assert 'switch' in result.output
        assert 'extensions' in result.output
        assert 'enable-ext' in result.output
        assert 'disable-ext' in result.output

    def test_php_command_without_subcommand(self, runner):
        from wslaragon.cli.php_commands import php

        result = runner.invoke(php, [])

        # Click 8+ groups show help and return exit_code 0 when no subcommand is provided
        assert result.exit_code == 0
        assert 'Usage:' in result.output or 'Commands:' in result.output

    def test_php_config_subgroup_help(self, runner):
        from wslaragon.cli.php_commands import php

        result = runner.invoke(php, ['config', '--help'])

        assert result.exit_code == 0
        assert 'list' in result.output
        assert 'set' in result.output
        assert 'get' in result.output