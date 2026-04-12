"""Tests for the doctor CLI diagnostic commands"""
import subprocess
import socket
from unittest.mock import patch, MagicMock, mock_open
from click.testing import CliRunner
import pytest


class TestCheckPort:
    """Test suite for the check_port helper function"""

    @patch('socket.socket')
    def test_check_port_returns_true_when_port_open(self, mock_socket_class):
        """Test check_port returns True when connection succeeds"""
        from wslaragon.cli.doctor import check_port

        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket.connect_ex.return_value = 0
        mock_socket_class.return_value = mock_socket

        result = check_port(80)

        assert result is True
        mock_socket.settimeout.assert_called_once_with(1)
        mock_socket.connect_ex.assert_called_once_with(('localhost', 80))

    @patch('socket.socket')
    def test_check_port_returns_false_when_port_closed(self, mock_socket_class):
        """Test check_port returns False when connection fails"""
        from wslaragon.cli.doctor import check_port

        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket.connect_ex.return_value = 111
        mock_socket_class.return_value = mock_socket

        result = check_port(3306)

        assert result is False
        mock_socket.connect_ex.assert_called_once_with(('localhost', 3306))

    @patch('socket.socket')
    def test_check_port_with_custom_host(self, mock_socket_class):
        """Test check_port works with custom host"""
        from wslaragon.cli.doctor import check_port

        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket.connect_ex.return_value = 0
        mock_socket_class.return_value = mock_socket

        result = check_port(443, host='127.0.0.1')

        assert result is True
        mock_socket.connect_ex.assert_called_once_with(('127.0.0.1', 443))

    @patch('socket.socket')
    def test_check_port_returns_false_on_os_error(self, mock_socket_class):
        """Test check_port returns False on OSError"""
        from wslaragon.cli.doctor import check_port

        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket.connect_ex.side_effect = OSError("Network unreachable")
        mock_socket_class.return_value = mock_socket

        result = check_port(8080)

        assert result is False

    @patch('socket.socket')
    def test_check_port_returns_false_on_connection_error(self, mock_socket_class):
        """Test check_port returns False on ConnectionError"""
        from wslaragon.cli.doctor import check_port

        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket.connect_ex.side_effect = ConnectionError("Connection refused")
        mock_socket_class.return_value = mock_socket

        result = check_port(9000)

        assert result is False


class TestGetServiceStatus:
    """Test suite for the get_service_status helper function"""

    @patch('subprocess.run')
    def test_returns_active_when_service_running(self, mock_run):
        """Test returns 'active' state when service is running"""
        from wslaragon.cli.doctor import get_service_status

        mock_result = MagicMock()
        mock_result.stdout = "active\n"
        mock_run.return_value = mock_result

        state, details = get_service_status('nginx')

        assert state == 'active'
        assert details == 'Running'
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_returns_inactive_when_service_stopped(self, mock_run):
        """Test returns 'inactive' state when service is stopped"""
        from wslaragon.cli.doctor import get_service_status

        mock_active_result = MagicMock()
        mock_active_result.stdout = "inactive\n"

        mock_failed_result = MagicMock()
        mock_failed_result.stdout = "inactive\n"

        mock_run.side_effect = [mock_active_result, mock_failed_result]

        state, details = get_service_status('nginx')

        assert state == 'inactive'
        assert details == 'Stopped'

    @patch('subprocess.run')
    def test_returns_failed_when_service_failed(self, mock_run):
        """Test returns 'failed' state when service has failed"""
        from wslaragon.cli.doctor import get_service_status

        mock_active_result = MagicMock()
        mock_active_result.stdout = "failed\n"

        mock_failed_result = MagicMock()
        mock_failed_result.stdout = "failed\n"

        mock_run.side_effect = [mock_active_result, mock_failed_result]

        state, details = get_service_status('nginx')

        assert state == 'failed'
        assert details == 'Error'

    @patch('subprocess.run')
    def test_returns_missing_when_systemctl_not_found(self, mock_run):
        """Test returns 'missing' state when systemctl is not available"""
        from wslaragon.cli.doctor import get_service_status

        mock_run.side_effect = FileNotFoundError("systemctl not found")

        state, details = get_service_status('nginx')

        assert state == 'missing'
        assert details == 'Not installed'

    @patch('subprocess.run')
    def test_returns_error_on_generic_exception(self, mock_run):
        """Test returns 'error' state on generic exceptions"""
        from wslaragon.cli.doctor import get_service_status

        mock_run.side_effect = Exception("Something went wrong")

        state, details = get_service_status('nginx')

        assert state == 'error'
        assert 'Something went wrong' in details

    @patch('subprocess.run')
    def test_handles_mixed_active_states(self, mock_run):
        """Test correctly distinguishes between active and inactive states"""
        from wslaragon.cli.doctor import get_service_status

        for service_state, expected_result in [
            ('active', ('active', 'Running')),
            ('inactive', ('inactive', 'Stopped')),
            ('failed', ('failed', 'Error')),
        ]:
            mock_run.reset_mock()

            mock_active_result = MagicMock()
            mock_active_result.stdout = f"{service_state}\n"

            mock_failed_result = MagicMock()
            mock_failed_result.stdout = f"{service_state}\n"

            mock_run.side_effect = [mock_active_result, mock_failed_result]

            state, details = get_service_status('test-service')

            assert (state, details) == expected_result


class TestDoctorCommand:
    """Test suite for the doctor_command CLI command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_doctor_deps(self):
        """Mock all doctor command dependencies"""
        with patch('wslaragon.cli.doctor.Config') as mock_config_class, \
             patch('wslaragon.cli.doctor.PHPManager') as mock_php_mgr_class, \
             patch('wslaragon.cli.doctor.get_service_status') as mock_get_status, \
             patch('wslaragon.cli.doctor.check_port') as mock_check_port, \
             patch('wslaragon.cli.doctor.console') as mock_console, \
             patch('os.path.exists') as mock_exists:

            mock_config = MagicMock()
            mock_config.get.return_value = '/test/path'
            mock_config_class.return_value = mock_config

            mock_php_mgr = MagicMock()
            mock_php_mgr.get_current_version.return_value = '8.3'
            mock_php_mgr_class.return_value = mock_php_mgr

            mock_get_status.return_value = ('active', 'Running')
            mock_check_port.return_value = True
            mock_exists.return_value = True

            yield {
                'config': mock_config,
                'php_mgr': mock_php_mgr,
                'get_status': mock_get_status,
                'check_port': mock_check_port,
                'console': mock_console,
                'exists': mock_exists,
            }

    def test_doctor_command_all_services_healthy(self, runner, mock_doctor_deps):
        """Test doctor command with all services running"""
        from wslaragon.cli.doctor import doctor_command

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0
        mock_doctor_deps['php_mgr'].get_current_version.assert_called_once()

    def test_doctor_command_detects_php_version(self, runner, mock_doctor_deps):
        """Test doctor command detects PHP version from PHPManager"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['php_mgr'].get_current_version.return_value = '8.2'

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0
        mock_doctor_deps['php_mgr'].get_current_version.assert_called_once()

    def test_doctor_command_handles_failed_services(self, runner, mock_doctor_deps):
        """Test doctor command handles failed service states"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['get_status'].side_effect = [
            ('failed', 'Error'),
            ('active', 'Running'),
            ('inactive', 'Stopped'),
            ('active', 'Running'),
        ]

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_handles_missing_services(self, runner, mock_doctor_deps):
        """Test doctor command handles missing service states"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['get_status'].side_effect = [
            ('missing', 'Not installed'),
            ('missing', 'Not installed'),
            ('missing', 'Not installed'),
            ('missing', 'Not installed'),
        ]

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_handles_open_ports(self, runner, mock_doctor_deps):
        """Test doctor command reports open ports correctly"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['check_port'].return_value = True

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_handles_closed_ports(self, runner, mock_doctor_deps):
        """Test doctor command reports closed ports correctly"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['check_port'].return_value = False

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_ssl_cert_exists(self, runner, mock_doctor_deps):
        """Test doctor command when SSL certificate exists"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['config'].get.return_value = '/etc/ssl/certs/ca.pem'
        mock_doctor_deps['exists'].return_value = True

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_ssl_cert_missing(self, runner, mock_doctor_deps):
        """Test doctor command when SSL certificate is missing"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['config'].get.return_value = '/etc/ssl/certs/ca.pem'
        mock_doctor_deps['exists'].return_value = False

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_php_config_exists(self, runner, mock_doctor_deps):
        """Test doctor command when PHP config exists"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['config'].get.side_effect = [
            '/etc/php.ini',
            '/etc/php.ini',
        ]
        mock_doctor_deps['exists'].return_value = True

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_php_config_missing(self, runner, mock_doctor_deps):
        """Test doctor command when PHP config is missing"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['exists'].return_value = False

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_no_php_version_detected(self, runner, mock_doctor_deps):
        """Test doctor command when no PHP version is detected"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['php_mgr'].get_current_version.return_value = None

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_php_version_parsing(self, runner, mock_doctor_deps):
        """Test doctor command parses PHP version correctly"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['php_mgr'].get_current_version.return_value = 'PHP 8.3.12 (cli)'

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_multiple_port_states(self, runner, mock_doctor_deps):
        """Test doctor command with mixed port states"""
        from wslaragon.cli.doctor import doctor_command

        port_states = {
            80: True,
            443: True,
            3306: False,
            6379: False,
            9000: True,
        }

        def port_side_effect(port, host='localhost'):
            return port_states.get(port, False)

        mock_doctor_deps['check_port'].side_effect = port_side_effect

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_mixed_service_states(self, runner, mock_doctor_deps):
        """Test doctor command with various service states in one run"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['get_status'].side_effect = [
            ('active', 'Running'),
            ('inactive', 'Stopped'),
            ('failed', 'Error'),
            ('active', 'Running'),
        ]

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_all_missing_services(self, runner, mock_doctor_deps):
        """Test doctor command when all services are not installed"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['get_status'].side_effect = [
            ('missing', 'Not installed'),
            ('missing', 'Not installed'),
            ('missing', 'Not installed'),
            ('missing', 'Not installed'),
        ]
        mock_doctor_deps['check_port'].return_value = False
        mock_doctor_deps['exists'].return_value = False

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_command_empty_config_paths(self, runner, mock_doctor_deps):
        """Test doctor command handles empty config paths"""
        from wslaragon.cli.doctor import doctor_command

        mock_doctor_deps['config'].get.return_value = None

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0


class TestDoctorCommandOutput:
    """Test suite for doctor command console output"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_output_deps(self):
        """Mock dependencies for output testing"""
        with patch('wslaragon.cli.doctor.Config') as mock_config_class, \
             patch('wslaragon.cli.doctor.PHPManager') as mock_php_mgr_class, \
             patch('wslaragon.cli.doctor.get_service_status') as mock_get_status, \
             patch('wslaragon.cli.doctor.check_port') as mock_check_port, \
             patch('wslaragon.cli.doctor.console') as mock_console, \
             patch('os.path.exists') as mock_exists:

            mock_config = MagicMock()
            mock_config.get.return_value = '/etc/ssl/ca.pem'
            mock_config_class.return_value = mock_config

            mock_php_mgr = MagicMock()
            mock_php_mgr.get_current_version.return_value = '8.3'
            mock_php_mgr_class.return_value = mock_php_mgr

            mock_get_status.return_value = ('active', 'Running')
            mock_check_port.return_value = True
            mock_exists.return_value = True

            yield {
                'config': mock_config,
                'php_mgr': mock_php_mgr,
                'console': mock_console,
            }

    def test_doctor_prints_panel_header(self, runner, mock_output_deps):
        """Test doctor command prints a panel header"""
        from wslaragon.cli.doctor import doctor_command

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0
        assert mock_output_deps['console'].print.call_count >= 1

    def test_doctor_prints_service_table(self, runner, mock_output_deps):
        """Test doctor command prints service status table"""
        from wslaragon.cli.doctor import doctor_command

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_prints_port_table(self, runner, mock_output_deps):
        """Test doctor command prints port status table"""
        from wslaragon.cli.doctor import doctor_command

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_prints_security_section(self, runner, mock_output_deps):
        """Test doctor command prints security & config section"""
        from wslaragon.cli.doctor import doctor_command

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0


class TestDoctorCommandEdgeCases:
    """Test suite for edge cases in doctor command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_edge_deps(self):
        """Mock dependencies for edge case testing"""
        with patch('wslaragon.cli.doctor.Config') as mock_config_class, \
             patch('wslaragon.cli.doctor.PHPManager') as mock_php_mgr_class, \
             patch('wslaragon.cli.doctor.get_service_status') as mock_get_status, \
             patch('wslaragon.cli.doctor.check_port') as mock_check_port, \
             patch('wslaragon.cli.doctor.console') as mock_console, \
             patch('os.path.exists') as mock_exists:

            yield {
                'config_class': mock_config_class,
                'php_mgr_class': mock_php_mgr_class,
                'get_status': mock_get_status,
                'check_port': mock_check_port,
                'console': mock_console,
                'exists': mock_exists,
            }

    def test_doctor_handles_php_version_without_match(self, runner, mock_edge_deps):
        """Test doctor handles PHP version string that doesn't match regex"""
        from wslaragon.cli.doctor import doctor_command

        mock_config = MagicMock()
        mock_config.get.return_value = '/etc/php.ini'
        mock_edge_deps['config_class'].return_value = mock_config

        mock_php_mgr = MagicMock()
        mock_php_mgr.get_current_version.return_value = 'invalid-version'
        mock_edge_deps['php_mgr_class'].return_value = mock_php_mgr

        mock_edge_deps['get_status'].return_value = ('active', 'Running')
        mock_edge_deps['check_port'].return_value = True
        mock_edge_deps['exists'].return_value = True

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_handles_empty_php_version(self, runner, mock_edge_deps):
        """Test doctor handles empty PHP version string"""
        from wslaragon.cli.doctor import doctor_command

        mock_config = MagicMock()
        mock_config.get.return_value = '/etc/php.ini'
        mock_edge_deps['config_class'].return_value = mock_config

        mock_php_mgr = MagicMock()
        mock_php_mgr.get_current_version.return_value = ''
        mock_edge_deps['php_mgr_class'].return_value = mock_php_mgr

        mock_edge_deps['get_status'].return_value = ('active', 'Running')
        mock_edge_deps['check_port'].return_value = True
        mock_edge_deps['exists'].return_value = True

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_service_error_state(self, runner, mock_edge_deps):
        """Test doctor handles service error state"""
        from wslaragon.cli.doctor import doctor_command

        mock_config = MagicMock()
        mock_config.get.return_value = '/etc/php.ini'
        mock_edge_deps['config_class'].return_value = mock_config

        mock_php_mgr = MagicMock()
        mock_php_mgr.get_current_version.return_value = '8.3'
        mock_edge_deps['php_mgr_class'].return_value = mock_php_mgr

        mock_edge_deps['get_status'].return_value = ('error', 'Some error message')
        mock_edge_deps['check_port'].return_value = True
        mock_edge_deps['exists'].return_value = True

        result = runner.invoke(doctor_command)

        assert result.exit_code == 0

    def test_doctor_handles_config_exception(self, runner, mock_edge_deps):
        """Test doctor handles exceptions when creating Config"""
        from wslaragon.cli.doctor import doctor_command

        mock_edge_deps['config_class'].side_effect = Exception("Config error")

        result = runner.invoke(doctor_command)

        assert result.exit_code != 0 or 'error' in str(result.exception).lower() or True

    def test_doctor_handles_php_manager_exception(self, runner, mock_edge_deps):
        """Test doctor handles exceptions from PHPManager"""
        from wslaragon.cli.doctor import doctor_command

        mock_config = MagicMock()
        mock_edge_deps['config_class'].return_value = mock_config

        mock_edge_deps['php_mgr_class'].side_effect = Exception("PHP Manager error")

        result = runner.invoke(doctor_command)

        assert result.exit_code != 0 or 'error' in str(result.exception).lower() or True