"""Tests for service CLI commands"""
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from wslaragon.cli.service_commands import service, status, start, stop, restart


class TestServiceStatusCommand:
    """Test suite for service status command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_status_shows_all_services(self, mock_mgr_class, runner):
        """Test status displays all services"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.status.return_value = {
            'nginx': {'running': True, 'port': 80, 'service': 'nginx'},
            'mysql': {'running': False, 'port': 3306, 'service': 'mariadb'},
            'php-fpm': {'running': True, 'port': 9000, 'service': 'php8.3-fpm'},
            'redis': {'running': False, 'port': 6379, 'service': 'redis-server'}
        }

        result = runner.invoke(service, ['status'])

        assert result.exit_code == 0
        mock_mgr.status.assert_called_once()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_status_shows_running_service_as_running(self, mock_mgr_class, runner):
        """Test status shows running services with checkmark"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.status.return_value = {
            'nginx': {'running': True, 'port': 80, 'service': 'nginx'}
        }

        result = runner.invoke(service, ['status'])

        assert result.exit_code == 0
        assert 'Running' in result.output

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_status_shows_stopped_service_as_stopped(self, mock_mgr_class, runner):
        """Test status shows stopped services with X mark"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.status.return_value = {
            'mysql': {'running': False, 'port': 3306, 'service': 'mariadb'}
        }

        result = runner.invoke(service, ['status'])

        assert result.exit_code == 0
        assert 'Stopped' in result.output

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_status_displays_ports(self, mock_mgr_class, runner):
        """Test status displays port numbers"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.status.return_value = {
            'nginx': {'running': True, 'port': 80, 'service': 'nginx'},
            'mysql': {'running': True, 'port': 3306, 'service': 'mariadb'}
        }

        result = runner.invoke(service, ['status'])

        assert result.exit_code == 0
        assert '80' in result.output
        assert '3306' in result.output

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_status_empty_services(self, mock_mgr_class, runner):
        """Test status handles empty service list"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.status.return_value = {}

        result = runner.invoke(service, ['status'])

        assert result.exit_code == 0


class TestServiceStartCommand:
    """Test suite for service start command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_start_success(self, mock_mgr_class, runner):
        """Test start shows success message"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.start.return_value = True

        result = runner.invoke(service, ['start', 'nginx'])

        assert result.exit_code == 0
        mock_mgr.start.assert_called_once_with('nginx')
        assert 'started' in result.output.lower()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_start_failure(self, mock_mgr_class, runner):
        """Test start shows failure message"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.start.return_value = False

        result = runner.invoke(service, ['start', 'nginx'])

        assert result.exit_code == 0
        mock_mgr.start.assert_called_once_with('nginx')
        assert 'failed' in result.output.lower()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_start_unknown_service_fails(self, mock_mgr_class, runner):
        """Test start unknown service returns failure"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.start.return_value = False

        result = runner.invoke(service, ['start', 'unknown'])

        assert result.exit_code == 0
        mock_mgr.start.assert_called_once_with('unknown')
        assert 'failed' in result.output.lower()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_start_calls_manager_with_correct_service(self, mock_mgr_class, runner):
        """Test start passes correct service name to manager"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.start.return_value = True

        runner.invoke(service, ['start', 'mysql'])
        mock_mgr.start.assert_called_once_with('mysql')

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_start_redis_service(self, mock_mgr_class, runner):
        """Test starting redis service"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.start.return_value = True

        result = runner.invoke(service, ['start', 'redis'])

        assert result.exit_code == 0
        mock_mgr.start.assert_called_once_with('redis')


class TestServiceStopCommand:
    """Test suite for service stop command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_stop_success(self, mock_mgr_class, runner):
        """Test stop shows success message"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.stop.return_value = True

        result = runner.invoke(service, ['stop', 'nginx'])

        assert result.exit_code == 0
        mock_mgr.stop.assert_called_once_with('nginx')
        assert 'stopped' in result.output.lower()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_stop_failure(self, mock_mgr_class, runner):
        """Test stop shows failure message"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.stop.return_value = False

        result = runner.invoke(service, ['stop', 'nginx'])

        assert result.exit_code == 0
        mock_mgr.stop.assert_called_once_with('nginx')
        assert 'failed' in result.output.lower()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_stop_unknown_service_fails(self, mock_mgr_class, runner):
        """Test stop unknown service returns failure"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.stop.return_value = False

        result = runner.invoke(service, ['stop', 'unknown'])

        assert result.exit_code == 0
        mock_mgr.stop.assert_called_once_with('unknown')
        assert 'failed' in result.output.lower()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_stop_mysql_service(self, mock_mgr_class, runner):
        """Test stopping mysql service"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.stop.return_value = True

        result = runner.invoke(service, ['stop', 'mysql'])

        assert result.exit_code == 0
        mock_mgr.stop.assert_called_once_with('mysql')

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_stop_php_fpm_service(self, mock_mgr_class, runner):
        """Test stopping php-fpm service"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.stop.return_value = True

        result = runner.invoke(service, ['stop', 'php-fpm'])

        assert result.exit_code == 0
        mock_mgr.stop.assert_called_once_with('php-fpm')


class TestServiceRestartCommand:
    """Test suite for service restart command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_restart_success(self, mock_mgr_class, runner):
        """Test restart shows success message"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.restart.return_value = True

        result = runner.invoke(service, ['restart', 'nginx'])

        assert result.exit_code == 0
        mock_mgr.restart.assert_called_once_with('nginx')
        assert 'restarted' in result.output.lower()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_restart_failure(self, mock_mgr_class, runner):
        """Test restart shows failure message"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.restart.return_value = False

        result = runner.invoke(service, ['restart', 'nginx'])

        assert result.exit_code == 0
        mock_mgr.restart.assert_called_once_with('nginx')
        assert 'failed' in result.output.lower()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_restart_unknown_service_fails(self, mock_mgr_class, runner):
        """Test restart unknown service returns failure"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.restart.return_value = False

        result = runner.invoke(service, ['restart', 'unknown'])

        assert result.exit_code == 0
        mock_mgr.restart.assert_called_once_with('unknown')
        assert 'failed' in result.output.lower()

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_restart_redis_service(self, mock_mgr_class, runner):
        """Test restarting redis service"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.restart.return_value = True

        result = runner.invoke(service, ['restart', 'redis'])

        assert result.exit_code == 0
        mock_mgr.restart.assert_called_once_with('redis')


class TestServiceGroupCommand:
    """Test suite for service group command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_service_group_help(self, runner):
        """Test service group shows help"""
        result = runner.invoke(service, ['--help'])

        assert result.exit_code == 0
        assert 'Service management' in result.output

    def test_service_group_shows_subcommands(self, runner):
        """Test service group lists available subcommands"""
        result = runner.invoke(service, ['--help'])

        assert result.exit_code == 0
        assert 'status' in result.output
        assert 'start' in result.output
        assert 'stop' in result.output
        assert 'restart' in result.output

    def test_service_start_requires_argument(self, runner):
        """Test start command requires service name argument"""
        result = runner.invoke(service, ['start'])

        assert result.exit_code != 0

    def test_service_stop_requires_argument(self, runner):
        """Test stop command requires service name argument"""
        result = runner.invoke(service, ['stop'])

        assert result.exit_code != 0

    def test_service_restart_requires_argument(self, runner):
        """Test restart command requires service name argument"""
        result = runner.invoke(service, ['restart'])

        assert result.exit_code != 0

    @patch('wslaragon.cli.service_commands.ServiceManager')
    def test_multiple_services_in_status(self, mock_mgr_class, runner):
        """Test status handles multiple services correctly"""
        mock_mgr = MagicMock()
        mock_mgr_class.return_value = mock_mgr
        mock_mgr.status.return_value = {
            'nginx': {'running': True, 'port': 80, 'service': 'nginx'},
            'mysql': {'running': True, 'port': 3306, 'service': 'mariadb'},
            'php-fpm': {'running': False, 'port': 9000, 'service': 'php8.3-fpm'},
            'redis': {'running': False, 'port': 6379, 'service': 'redis-server'}
        }

        result = runner.invoke(service, ['status'])

        assert result.exit_code == 0
        assert 'nginx' in result.output
        assert 'mysql' in result.output
        assert 'php-fpm' in result.output
        assert 'redis' in result.output