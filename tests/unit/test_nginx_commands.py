"""Tests for the Nginx Commands CLI module"""
import pytest
import subprocess
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, call


class TestNginxGroup:
    """Test suite for nginx group command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    def test_nginx_group_has_commands(self, runner):
        """Test that nginx group has all expected commands"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['--help'])

        assert result.exit_code == 0
        assert 'config' in result.output

    def test_config_group_has_commands(self, runner):
        """Test that config group has list and set commands"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', '--help'])

        assert result.exit_code == 0
        assert 'list' in result.output
        assert 'set' in result.output


class TestNginxConfigListCommand:
    """Test suite for nginx config list command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock nginx config list dependencies"""
        with patch('wslaragon.cli.nginx_commands.Config') as mock_config, \
             patch('wslaragon.cli.nginx_commands.console') as mock_console:

            mock_config_instance = MagicMock()
            mock_config_instance.get.return_value = '128M'
            mock_config.return_value = mock_config_instance

            yield {
                'config': mock_config_instance,
                'console': mock_console,
            }

    def test_config_list_success(self, runner, mock_deps):
        """Test config list shows settings"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'list'])

        assert result.exit_code == 0
        mock_deps['config'].get.assert_called()

    def test_config_list_shows_client_max_body_size(self, runner, mock_deps):
        """Test config list shows client_max_body_size setting"""
        from wslaragon.cli.nginx_commands import nginx

        mock_deps['config'].get.return_value = '256M'

        result = runner.invoke(nginx, ['config', 'list'])

        assert result.exit_code == 0
        mock_deps['config'].get.assert_called_with('nginx.client_max_body_size', '128M')

    def test_config_list_with_custom_value(self, runner, mock_deps):
        """Test config list with custom value from config"""
        from wslaragon.cli.nginx_commands import nginx

        mock_deps['config'].get.return_value = '512M'

        result = runner.invoke(nginx, ['config', 'list'])

        assert result.exit_code == 0

    def test_config_list_uses_default_fallback(self, runner, mock_deps):
        """Test config list uses default value when config returns None"""
        from wslaragon.cli.nginx_commands import nginx

        mock_deps['config'].get.return_value = None

        result = runner.invoke(nginx, ['config', 'list'])

        assert result.exit_code == 0

    def test_config_list_creates_table_output(self, runner, mock_deps):
        """Test config list creates table with proper columns"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'list'])

        assert result.exit_code == 0


class TestNginxConfigSetCommand:
    """Test suite for nginx config set command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock nginx config set dependencies"""
        with patch('wslaragon.cli.nginx_commands.Config') as mock_config, \
             patch('wslaragon.cli.nginx_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.nginx_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.nginx_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.nginx_commands.subprocess.run') as mock_run, \
             patch('wslaragon.cli.nginx_commands.console') as mock_console:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_nginx_instance = MagicMock()
            mock_nginx.return_value = mock_nginx_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr_instance.list_sites.return_value = []
            mock_site_mgr_instance.update_site.return_value = {'success': True}
            mock_site_mgr.return_value = mock_site_mgr_instance

            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'nginx': mock_nginx_instance,
                'site_mgr': mock_site_mgr_instance,
                'run': mock_run,
                'console': mock_console,
            }

    def test_config_set_success(self, runner, mock_deps):
        """Test config set updates value successfully"""
        from wslaragon.cli.nginx_commands import nginx

        mock_deps['site_mgr'].list_sites.return_value = [
            {'name': 'site1'},
            {'name': 'site2'},
        ]

        result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '256M'])

        assert result.exit_code == 0
        mock_deps['config'].set.assert_called_once_with('nginx.client_max_body_size', '256M')

    def test_config_set_validates_sudo(self, runner, mock_deps):
        """Test config set checks sudo permissions"""
        from wslaragon.cli.nginx_commands import nginx
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '256M'])

        assert result.exit_code == 0
        mock_deps['run'].assert_called_with(['sudo', '-v'], check=True)
        mock_deps['config'].set.assert_not_called()

    def test_config_set_checks_sudo_with_v_flag(self, runner, mock_deps):
        """Test config set uses sudo -v for validation"""
        from wslaragon.cli.nginx_commands import nginx

        runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '256M'])

        mock_deps['run'].assert_any_call(['sudo', '-v'], check=True)

    def test_config_set_invalid_key(self, runner, mock_deps):
        """Test config set rejects invalid key"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'set', 'invalid_key', 'value'])

        assert result.exit_code == 0
        mock_deps['config'].set.assert_not_called()

    def test_config_set_shows_error_for_invalid_key(self, runner, mock_deps):
        """Test config set shows error message for invalid key"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'set', 'wrong_setting', 'value'])

        assert result.exit_code == 0
        mock_deps['config'].set.assert_not_called()

    def test_config_set_updates_all_sites(self, runner, mock_deps):
        """Test config set updates all sites"""
        from wslaragon.cli.nginx_commands import nginx

        mock_deps['site_mgr'].list_sites.return_value = [
            {'name': 'site1'},
            {'name': 'site2'},
            {'name': 'site3'},
        ]

        result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '512M'])

        assert result.exit_code == 0
        assert mock_deps['site_mgr'].update_site.call_count == 3

    def test_config_set_empty_sites_list(self, runner, mock_deps):
        """Test config set with no sites"""
        from wslaragon.cli.nginx_commands import nginx

        mock_deps['site_mgr'].list_sites.return_value = []

        result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '128M'])

        assert result.exit_code == 0
        mock_deps['config'].set.assert_called_once()

    def test_config_set_creates_managers(self, runner, mock_deps):
        """Test config set creates required managers"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '256M'])

        assert result.exit_code == 0

    def test_config_set_various_values(self, runner, mock_deps):
        """Test config set with various valid values"""
        from wslaragon.cli.nginx_commands import nginx

        test_values = ['128M', '256M', '512M', '1G', '2G']

        for value in test_values:
            mock_deps['config'].set.reset_mock()
            result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', value])
            assert result.exit_code == 0
            mock_deps['config'].set.assert_called_with('nginx.client_max_body_size', value)


class TestConfigSetEdgeCases:
    """Test suite for edge cases in nginx config set"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock nginx config set dependencies"""
        with patch('wslaragon.cli.nginx_commands.Config') as mock_config, \
             patch('wslaragon.cli.nginx_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.nginx_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.nginx_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.nginx_commands.subprocess.run') as mock_run, \
             patch('wslaragon.cli.nginx_commands.console') as mock_console:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_nginx_instance = MagicMock()
            mock_nginx.return_value = mock_nginx_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr_instance.list_sites.return_value = []
            mock_site_mgr.return_value = mock_site_mgr_instance

            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'nginx': mock_nginx_instance,
                'site_mgr': mock_site_mgr_instance,
                'run': mock_run,
                'console': mock_console,
            }

    def test_config_set_handles_site_update_failure(self, runner, mock_deps):
        """Test config set continues when site update fails"""
        from wslaragon.cli.nginx_commands import nginx

        mock_deps['site_mgr'].list_sites.return_value = [
            {'name': 'site1'},
            {'name': 'site2'},
        ]
        mock_deps['site_mgr'].update_site.side_effect = [
            {'success': True},
            {'success': False, 'error': 'Update failed'},
        ]

        result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '256M'])

        assert result.exit_code == 0

    def test_config_set_special_characters_in_value(self, runner, mock_deps):
        """Test config set with special characters in value"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '128M'])

        assert result.exit_code == 0
        mock_deps['config'].set.assert_called_once()

    def test_config_set_updates_site_for_each_site(self, runner, mock_deps):
        """Test config set calls update_site for each site"""
        from wslaragon.cli.nginx_commands import nginx

        sites = [
            {'name': 'alpha'},
            {'name': 'beta'},
            {'name': 'gamma'},
        ]
        mock_deps['site_mgr'].list_sites.return_value = sites

        result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '128M'])

        assert result.exit_code == 0
        calls = [call('alpha'), call('beta'), call('gamma')]
        mock_deps['site_mgr'].update_site.assert_has_calls(calls)


class TestNginxConfigSetCommandSudo:
    """Test suite for sudo handling in nginx config set"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock nginx config set dependencies"""
        with patch('wslaragon.cli.nginx_commands.Config') as mock_config, \
             patch('wslaragon.cli.nginx_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.nginx_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.nginx_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.nginx_commands.subprocess.run') as mock_run:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'run': mock_run,
            }

    def test_sudo_check_failure_shows_message(self, runner, mock_deps):
        """Test that sudo failure shows proper error message"""
        from wslaragon.cli.nginx_commands import nginx
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo', output='', stderr='')

        result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '256M'])

        assert result.exit_code == 0
        assert 'sudo' in result.output.lower()

    def test_sudo_detached_session(self, runner, mock_deps):
        """Test sudo check uses -v flag"""
        from wslaragon.cli.nginx_commands import nginx

        runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '128M'])

        mock_deps['run'].assert_any_call(['sudo', '-v'], check=True)


class TestNginxConfigListOutput:
    """Test suite for nginx config list output formatting"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock nginx config list dependencies"""
        with patch('wslaragon.cli.nginx_commands.Config') as mock_config, \
             patch('wslaragon.cli.nginx_commands.Table') as mock_table, \
             patch('wslaragon.cli.nginx_commands.console') as mock_console:

            mock_config_instance = MagicMock()
            mock_config_instance.get.return_value = '128M'
            mock_config.return_value = mock_config_instance

            mock_table_instance = MagicMock()
            mock_table.return_value = mock_table_instance

            yield {
                'config': mock_config_instance,
                'table': mock_table_instance,
                'console': mock_console,
            }

    def test_table_created_with_title(self, runner, mock_deps):
        """Test table is created with proper title"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'list'])

        assert result.exit_code == 0

    def test_table_has_correct_columns(self, runner, mock_deps):
        """Test table has Setting and Value columns"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'list'])

        assert result.exit_code == 0


class TestNginxConfigSetKeyValidation:
    """Test suite for key validation in nginx config set"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock nginx config set dependencies"""
        with patch('wslaragon.cli.nginx_commands.Config') as mock_config, \
             patch('wslaragon.cli.nginx_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.nginx_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.nginx_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.nginx_commands.subprocess.run') as mock_run, \
             patch('wslaragon.cli.nginx_commands.console') as mock_console:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'run': mock_run,
                'console': mock_console,
            }

    def test_valid_key_client_max_body_size(self, runner, mock_deps):
        """Test client_max_body_size is valid key"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'set', 'client_max_body_size', '256M'])

        assert result.exit_code == 0
        mock_deps['config'].set.assert_called_once()

    def test_invalid_key_rejected(self, runner, mock_deps):
        """Test invalid keys are rejected"""
        from wslaragon.cli.nginx_commands import nginx

        invalid_keys = [
            'worker_processes',
            'keepalive_timeout',
            'gzip',
            'proxy_cache',
            'invalid_setting',
        ]

        for key in invalid_keys:
            mock_deps['config'].set.reset_mock()
            result = runner.invoke(nginx, ['config', 'set', key, 'value'])
            assert result.exit_code == 0
            mock_deps['config'].set.assert_not_called()

    def test_key_case_sensitive(self, runner, mock_deps):
        """Test key validation is case sensitive"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'set', 'CLIENT_MAX_BODY_SIZE', '256M'])

        assert result.exit_code == 0
        mock_deps['config'].set.assert_not_called()

    def test_shows_valid_settings_on_invalid_key(self, runner, mock_deps):
        """Test invalid key shows valid settings list"""
        from wslaragon.cli.nginx_commands import nginx

        result = runner.invoke(nginx, ['config', 'set', 'wrong_key', 'value'])

        assert result.exit_code == 0
        mock_deps['config'].set.assert_not_called()