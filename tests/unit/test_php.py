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

    @pytest.fixture(autouse=True)
    def assume_target_fpm_installed(self, php_manager):
        """Most switch_version tests exercise the switch path itself."""
        php_manager._is_fpm_package_installed = MagicMock(return_value=True)

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_success(self, mock_run, php_manager):
        """Test switch_version succeeds"""
        mock_result = MagicMock()
        mock_result.stdout = "inactive\n"
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
    def test_switch_version_always_starts_fpm(self, mock_run, php_manager):
        """Test switch_version always stops all FPM services and starts the target"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager._stop_php_fpm = MagicMock(return_value=True)

        php_manager.switch_version("8.2")

        php_manager._stop_php_fpm.assert_called_once()
        calls = mock_run.call_args_list
        start_calls = [c for c in calls if 'start' in str(c) and 'fpm' in str(c)]
        assert len(start_calls) >= 1

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_starts_fpm_when_not_active(self, mock_run, php_manager):
        """Test switch_version enables and starts FPM even when it was not previously running"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager._stop_php_fpm = MagicMock(return_value=True)

        result = php_manager.switch_version("8.5")

        assert result is True
        php_manager._stop_php_fpm.assert_called_once()
        calls = mock_run.call_args_list
        enable_calls = [c for c in calls if 'enable' in str(c) and 'fpm' in str(c)]
        start_calls = [c for c in calls if 'start' in str(c) and 'fpm' in str(c)]
        assert len(enable_calls) >= 1
        assert len(start_calls) >= 1

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_updates_config(self, mock_run, php_manager):
        """Test switch_version persists new version in config.yaml"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager._stop_php_fpm = MagicMock(return_value=True)

        php_manager.switch_version("8.5")

        php_manager.config.set.assert_any_call('php.version', '8.5')
        php_manager.config.set.assert_any_call('php.ini_file', '/etc/php/8.5/fpm/php.ini')

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_returns_false_on_exception(self, mock_run, php_manager):
        """Test switch_version returns False on exception"""
        mock_run.side_effect = Exception("Error")

        result = php_manager.switch_version("8.2")

        assert result is False

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_rolls_back_fpm_on_start_failure(self, mock_run, php_manager):
        """Test switch_version restarts the previously-running FPM service if the new one fails to start"""
        import subprocess as sp

        def side_effect(cmd, **kwargs):
            if cmd[:3] == ['sudo', 'systemctl', 'start'] and 'php8.3-fpm' in cmd:
                raise sp.CalledProcessError(1, cmd)
            result = MagicMock()
            result.returncode = 0
            result.stdout = "php8.2-fpm.service loaded active running PHP 8.2 FastCGI Process Manager\n"
            return result

        mock_run.side_effect = side_effect

        result = php_manager.switch_version("8.3")

        assert result is False
        rollback_calls = [
            c for c in mock_run.call_args_list
            if c[0][0][:3] == ['sudo', 'systemctl', 'start'] and 'php8.2-fpm.service' in c[0][0]
        ]
        assert len(rollback_calls) >= 1

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_reverts_cli_switch_on_fpm_start_failure(self, mock_run, php_manager):
        """Test switch_version reverts update-alternatives to the previous version on failure"""
        import subprocess as sp

        # mock_config reports 'php.version' as '8.3' — switching to 8.4 and
        # failing should revert the CLI back to 8.3.
        def side_effect(cmd, **kwargs):
            if cmd[:3] == ['sudo', 'systemctl', 'start'] and 'php8.4-fpm' in cmd:
                raise sp.CalledProcessError(1, cmd)
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            return result

        mock_run.side_effect = side_effect

        result = php_manager.switch_version("8.4")

        assert result is False
        revert_calls = [
            c for c in mock_run.call_args_list
            if c[0][0] == ['sudo', 'update-alternatives', '--set', 'php', '/usr/bin/php8.3']
        ]
        assert len(revert_calls) == 1

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_does_not_revert_cli_when_same_version(self, mock_run, php_manager):
        """Test switch_version does not re-run update-alternatives when reverting to the same version"""
        import subprocess as sp

        def side_effect(cmd, **kwargs):
            if cmd[:3] == ['sudo', 'systemctl', 'start'] and 'php8.3-fpm' in cmd:
                raise sp.CalledProcessError(1, cmd)
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            return result

        mock_run.side_effect = side_effect

        result = php_manager.switch_version("8.3")

        assert result is False
        alternatives_calls = [
            c for c in mock_run.call_args_list if 'update-alternatives' in c[0][0]
        ]
        assert len(alternatives_calls) == 1

    @patch('wslaragon.services.php.subprocess.run')
    def test_switch_version_rollback_skips_restarting_target_service(self, mock_run, php_manager):
        """Test that the rollback loop skips the target fpm_service itself (no double-start)"""
        import subprocess as sp

        php_manager._get_php_fpm_services = MagicMock(return_value=['php8.3-fpm', 'php8.2-fpm'])

        def side_effect(cmd, **kwargs):
            if cmd[:3] == ['sudo', 'systemctl', 'start'] and 'php8.3-fpm' in cmd:
                raise sp.CalledProcessError(1, cmd)
            result = MagicMock()
            result.returncode = 0
            return result

        mock_run.side_effect = side_effect

        result = php_manager.switch_version("8.3")

        assert result is False
        target_start_calls = [
            c for c in mock_run.call_args_list
            if c[0][0][:3] == ['sudo', 'systemctl', 'start'] and c[0][0][3] == 'php8.3-fpm'
        ]
        # Only the original (failed) start attempt — rollback must not retry the target itself
        assert len(target_start_calls) == 1

    def test_switch_version_aborts_when_fpm_missing(self, php_manager):
        """Test switch_version aborts before stopping FPM if target package is missing"""
        php_manager._is_fpm_package_installed = MagicMock(return_value=False)
        php_manager._stop_php_fpm = MagicMock(return_value=True)

        result = php_manager.switch_version("8.5")

        assert result is False
        php_manager._stop_php_fpm.assert_not_called()


class TestPHPManagerIsFpmPackageInstalled:
    """Test suite for _is_fpm_package_installed helper"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_returns_true_when_package_is_installed(self, mock_run, php_manager):
        """Test _is_fpm_package_installed returns True when dpkg reports 'ii'"""
        mock_result = MagicMock()
        mock_result.stdout = "ii  php8.5-fpm 8.5.0 amd64\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        assert php_manager._is_fpm_package_installed("8.5") is True

    @patch('wslaragon.services.php.subprocess.run')
    def test_returns_false_when_package_not_installed(self, mock_run, php_manager):
        """Test _is_fpm_package_installed returns False when dpkg finds no 'ii'"""
        mock_result = MagicMock()
        mock_result.stdout = ""  # dpkg -l prints no matching packages
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        assert php_manager._is_fpm_package_installed("8.5") is False

    @patch('wslaragon.services.php.subprocess.run')
    def test_returns_false_on_dpkg_error(self, mock_run, php_manager):
        """Test _is_fpm_package_installed returns False when dpkg fails"""
        mock_run.side_effect = Exception("dpkg failed")

        assert php_manager._is_fpm_package_installed("8.5") is False


class TestPHPManagerGetAllPhpIniPaths:
    """Test suite for _get_all_php_ini_paths method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    def test_returns_existing_fpm_and_cli_ini_paths(self, php_manager):
        """Test that only existing php.ini paths across installed versions are returned"""
        php_manager.get_installed_versions = MagicMock(return_value=['8.1', '8.3'])

        def fake_exists(self):
            return str(self) in (
                '/etc/php/8.1/fpm/php.ini',
                '/etc/php/8.3/cli/php.ini',
            )

        with patch.object(Path, 'exists', fake_exists):
            paths = php_manager._get_all_php_ini_paths()

        assert paths == [Path('/etc/php/8.1/fpm/php.ini'), Path('/etc/php/8.3/cli/php.ini')]

    def test_returns_empty_list_when_no_versions_installed(self, php_manager):
        """Test that no installed versions yields an empty path list"""
        php_manager.get_installed_versions = MagicMock(return_value=[])

        paths = php_manager._get_all_php_ini_paths()

        assert paths == []

    def test_returns_empty_list_when_no_ini_files_exist(self, php_manager):
        """Test that missing ini files on disk are excluded from the result"""
        php_manager.get_installed_versions = MagicMock(return_value=['8.1'])

        with patch.object(Path, 'exists', return_value=False):
            paths = php_manager._get_all_php_ini_paths()

        assert paths == []


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

    @patch('wslaragon.services.php.subprocess.Popen')
    @patch('builtins.open', create=True)
    def test_write_ini_writes_to_given_path_not_default(self, mock_file, mock_popen, php_manager):
        """Test write_ini writes to an explicit ini_path instead of self.php_ini_path"""
        ini_content = "memory_limit = 128M\n"
        mock_file.return_value.__enter__.return_value.readlines.return_value = ini_content.split('\n')

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_process

        other_path = Path('/etc/php/8.1/cli/php.ini')
        result = php_manager.write_ini({'memory_limit': '256M'}, other_path)

        assert result is True
        mock_file.assert_any_call(other_path, 'r')
        popen_call = mock_popen.call_args
        assert str(other_path) in popen_call[0][0]


class TestPHPManagerSetUploadLimits:
    """Test suite for set_upload_limits method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    def test_set_upload_limits_writes_once_per_ini_path(self, php_manager):
        """set_upload_limits should batch all directives into a single write_ini call per path"""
        paths = [Path('/etc/php/8.1/fpm/php.ini'), Path('/etc/php/8.1/cli/php.ini')]
        php_manager._get_all_php_ini_paths = MagicMock(return_value=paths)
        php_manager.write_ini = MagicMock(return_value=True)
        php_manager._restart_php_fpm = MagicMock(return_value=True)

        results = php_manager.set_upload_limits('1G')

        assert php_manager.write_ini.call_count == len(paths)
        expected_directives = {
            'upload_max_filesize': '1G',
            'post_max_size': '1G',
            'memory_limit': '1G',
            'max_execution_time': '600',
            'max_input_time': '600',
        }
        for call, path in zip(php_manager.write_ini.call_args_list, paths):
            assert call[0][0] == expected_directives
            assert call[0][1] == path
        assert results == {str(p): True for p in paths}

    def test_set_upload_limits_restarts_fpm(self, php_manager):
        """set_upload_limits should restart PHP-FPM after writing"""
        php_manager._get_all_php_ini_paths = MagicMock(return_value=[Path('/etc/php/8.1/fpm/php.ini')])
        php_manager.write_ini = MagicMock(return_value=True)
        php_manager._restart_php_fpm = MagicMock(return_value=True)

        php_manager.set_upload_limits('512M')

        php_manager._restart_php_fpm.assert_called_once()


class TestPHPManagerUpdateConfigAllVersions:
    """Test suite for update_config_all_versions method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    def test_update_config_all_versions_writes_via_write_ini(self, php_manager):
        """update_config_all_versions should delegate to write_ini per path"""
        paths = [Path('/etc/php/8.1/fpm/php.ini'), Path('/etc/php/8.2/fpm/php.ini')]
        php_manager._get_all_php_ini_paths = MagicMock(return_value=paths)
        php_manager.write_ini = MagicMock(return_value=True)
        php_manager._restart_php_fpm = MagicMock(return_value=True)

        results = php_manager.update_config_all_versions('memory_limit', '256M')

        for call, path in zip(php_manager.write_ini.call_args_list, paths):
            assert call[0][0] == {'memory_limit': '256M'}
            assert call[0][1] == path
        assert results == {str(p): True for p in paths}


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

    @patch('wslaragon.services.php.subprocess.run')
    def test_update_config_fallback_on_called_process_error(self, mock_run, php_manager):
        """Test update_config falls back to _restart_php_fpm on CalledProcessError"""
        php_manager.write_ini = MagicMock(return_value=True)
        php_manager._restart_php_fpm = MagicMock(return_value=True)

        # get_current_version returns a version
        version_result = MagicMock()
        version_result.stdout = "PHP 8.2.5\n"
        # systemctl restart raises CalledProcessError
        restart_error = subprocess.CalledProcessError(1, 'systemctl restart')

        mock_run.side_effect = [version_result, restart_error]

        result = php_manager.update_config('memory_limit', '256M')
        
        assert result is True
        php_manager._restart_php_fpm.assert_called_once()

    @patch('wslaragon.services.php.subprocess.run')
    def test_update_config_fallback_when_no_version(self, mock_run, php_manager):
        """Test update_config falls back to _restart_php_fpm when version is None"""
        mock_result = MagicMock()
        mock_result.stdout = ""  # No PHP version found
        mock_run.return_value = mock_result
        
        php_manager.write_ini = MagicMock(return_value=True)
        php_manager._restart_php_fpm = MagicMock(return_value=True)

        result = php_manager.update_config('memory_limit', '256M')
        
        assert result is True
        php_manager._restart_php_fpm.assert_called_once()

    def test_update_config_exception_returns_false(self, php_manager):
        """Test update_config returns False on unexpected exception"""
        php_manager.write_ini = MagicMock(side_effect=Exception("Unexpected error"))

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

        # Mock the helper to avoid needing systemctl output
        php_manager._restart_php_fpm = MagicMock(return_value=True)

        result = php_manager.enable_extension("mysqli")

        assert result is True

    @patch('wslaragon.services.php.subprocess.run')
    def test_enable_extension_calls_phpenmod(self, mock_run, php_manager):
        """Test enable_extension calls phpenmod"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager._restart_php_fpm = MagicMock(return_value=True)

        php_manager.enable_extension("mysqli")

        first_call = mock_run.call_args_list[0]
        assert 'phpenmod' in first_call[0][0]
        assert 'mysqli' in first_call[0][0]

    def test_enable_extension_restarts_fpm(self, php_manager):
        """Test enable_extension restarts PHP-FPM via helper"""
        with patch('wslaragon.services.php.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = php_manager.enable_extension("mysqli")

            assert result is True
            # Verify phpenmod was called
            calls = mock_run.call_args_list
            phpenmod_calls = [c for c in calls if 'phpenmod' in str(c)]
            assert len(phpenmod_calls) >= 1

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

        # Mock the helper to avoid needing systemctl output
        php_manager._restart_php_fpm = MagicMock(return_value=True)

        result = php_manager.disable_extension("mysqli")

        assert result is True

    @patch('wslaragon.services.php.subprocess.run')
    def test_disable_extension_calls_phpdismod(self, mock_run, php_manager):
        """Test disable_extension calls phpdismod"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        php_manager._restart_php_fpm = MagicMock(return_value=True)

        php_manager.disable_extension("mysqli")

        first_call = mock_run.call_args_list[0]
        assert 'phpdismod' in first_call[0][0]
        assert 'mysqli' in first_call[0][0]

    def test_disable_extension_restarts_fpm(self, php_manager):
        """Test disable_extension restarts PHP-FPM via helper"""
        with patch('wslaragon.services.php.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = php_manager.disable_extension("mysqli")

            assert result is True
            # Verify phpdismod was called
            calls = mock_run.call_args_list
            phpdismod_calls = [c for c in calls if 'phpdismod' in str(c)]
            assert len(phpdismod_calls) >= 1

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


class TestPHPManagerGetFpmServices:
    """Test suite for _get_php_fpm_services helper method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_php_fpm_services_finds_services(self, mock_run, php_manager):
        """Test _get_php_fpm_services finds running PHP-FPM services"""
        mock_result = MagicMock()
        mock_result.stdout = """php8.1-fpm.service  loaded active running  PHP 8.1 FPM
php8.2-fpm.service  loaded active running  PHP 8.2 FPM
nginx.service       loaded active running  A high performance web server
"""
        mock_run.return_value = mock_result

        result = php_manager._get_php_fpm_services()
        
        assert 'php8.1-fpm.service' in result
        assert 'php8.2-fpm.service' in result
        assert 'nginx.service' not in result

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_php_fpm_services_empty(self, mock_run, php_manager):
        """Test _get_php_fpm_services returns empty when no services found"""
        mock_result = MagicMock()
        mock_result.stdout = "nginx.service  loaded active running  A high performance web server\n"
        mock_run.return_value = mock_result

        result = php_manager._get_php_fpm_services()
        
        assert result == []

    @patch('wslaragon.services.php.subprocess.run')
    def test_get_php_fpm_services_exception(self, mock_run, php_manager):
        """Test _get_php_fpm_services returns empty on exception"""
        mock_run.side_effect = Exception("systemctl not found")

        result = php_manager._get_php_fpm_services()
        
        assert result == []


class TestPHPManagerRestartPhpFpm:
    """Test suite for _restart_php_fpm helper method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_restart_php_fpm_success(self, mock_run, php_manager):
        """Test _restart_php_fpm restarts all found services"""
        # First call: systemctl list-units
        list_result = MagicMock()
        list_result.stdout = "php8.2-fpm.service  loaded active running  PHP 8.2 FPM\n"
        # Second call: sudo systemctl restart
        restart_result = MagicMock()
        restart_result.returncode = 0
        
        mock_run.side_effect = [list_result, restart_result]

        result = php_manager._restart_php_fpm()
        
        assert result is True
        assert mock_run.call_count == 2

    @patch('wslaragon.services.php.subprocess.run')
    def test_restart_php_fpm_no_services(self, mock_run, php_manager):
        """Test _restart_php_fpm returns True when no services found"""
        list_result = MagicMock()
        list_result.stdout = ""
        mock_run.return_value = list_result

        result = php_manager._restart_php_fpm()
        
        assert result is True
        assert mock_run.call_count == 1  # Only the list-units call

    @patch('wslaragon.services.php.subprocess.run')
    def test_restart_php_fpm_partial_failure(self, mock_run, php_manager):
        """Test _restart_php_fpm returns False when one service fails to restart"""
        list_result = MagicMock()
        list_result.stdout = "php8.1-fpm.service  loaded active running  PHP 8.1 FPM\nphp8.2-fpm.service  loaded active running  PHP 8.2 FPM\n"
        restart_ok = MagicMock()
        restart_ok.returncode = 0
        
        mock_run.side_effect = [list_result, restart_ok, subprocess.CalledProcessError(1, 'systemctl')]

        result = php_manager._restart_php_fpm()
        
        assert result is False

    @patch('wslaragon.services.php.subprocess.run')
    def test_restart_php_fpm_unexpected_exception(self, mock_run, php_manager):
        """Test _restart_php_fpm handles unexpected exceptions"""
        list_result = MagicMock()
        list_result.stdout = "php8.2-fpm.service  loaded active running  PHP 8.2 FPM\n"
        restart_ok = MagicMock()
        restart_ok.returncode = 0
        
        mock_run.side_effect = [list_result, Exception("Unexpected error")]

        result = php_manager._restart_php_fpm()
        
        assert result is False


class TestPHPManagerStopPhpFpm:
    """Test suite for _stop_php_fpm helper method"""

    @pytest.fixture
    def php_manager(self, mock_config):
        from wslaragon.services.php import PHPManager
        return PHPManager(mock_config)

    @patch('wslaragon.services.php.subprocess.run')
    def test_stop_php_fpm_success(self, mock_run, php_manager):
        """Test _stop_php_fpm stops all found services"""
        list_result = MagicMock()
        list_result.stdout = "php8.2-fpm.service  loaded active running  PHP 8.2 FPM\n"
        stop_result = MagicMock()
        
        mock_run.side_effect = [list_result, stop_result]

        result = php_manager._stop_php_fpm()
        
        assert result is True
        assert mock_run.call_count == 2

    @patch('wslaragon.services.php.subprocess.run')
    def test_stop_php_fpm_no_services(self, mock_run, php_manager):
        """Test _stop_php_fpm returns True when no services found"""
        list_result = MagicMock()
        list_result.stdout = ""
        mock_run.return_value = list_result

        result = php_manager._stop_php_fpm()
        
        assert result is True

    @patch('wslaragon.services.php.subprocess.run')
    def test_stop_php_fpm_exception(self, mock_run, php_manager):
        """Test _stop_php_fpm returns False on exception"""
        list_result = MagicMock()
        list_result.stdout = "php8.2-fpm.service  loaded active running  PHP 8.2 FPM\n"
        
        mock_run.side_effect = [list_result, Exception("Stop failed")]

        result = php_manager._stop_php_fpm()
        
        assert result is False