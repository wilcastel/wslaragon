"""Tests for the ServiceManager module"""
import subprocess
from unittest.mock import patch, MagicMock

import pytest


class TestServiceManager:
    """Test suite for the ServiceManager class"""

    @pytest.fixture
    def service_manager(self):
        """Create a ServiceManager instance"""
        from wslaragon.core.services import ServiceManager
        return ServiceManager()

    def test_service_manager_initializes_services(self, service_manager):
        """Test that ServiceManager initializes with correct services"""
        assert 'nginx' in service_manager.services
        assert 'mysql' in service_manager.services
        assert 'php-fpm' in service_manager.services
        assert 'redis' in service_manager.services

    def test_service_manager_has_correct_ports(self, service_manager):
        """Test that services have correct port configurations"""
        assert service_manager.services['nginx']['port'] == 80
        assert service_manager.services['mysql']['port'] == 3306
        assert service_manager.services['php-fpm']['port'] == 9000
        assert service_manager.services['redis']['port'] == 6379

    def test_service_manager_has_correct_service_names(self, service_manager):
        """Test that services have correct systemd names"""
        assert service_manager.services['nginx']['service'] == 'nginx'
        assert service_manager.services['mysql']['service'] == 'mariadb'
        assert service_manager.services['php-fpm']['service'] == 'php8.3-fpm'


class TestServiceManagerIsRunning:
    """Test suite for is_running method"""

    @pytest.fixture
    def service_manager(self):
        from wslaragon.core.services import ServiceManager
        return ServiceManager()

    @patch('subprocess.run')
    def test_is_running_returns_true_when_service_active(self, mock_run, service_manager):
        """Test is_running returns True when service is active"""
        mock_result = MagicMock()
        mock_result.stdout = "active"
        mock_run.return_value = mock_result

        result = service_manager.is_running('nginx')
        
        assert result is True
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_is_running_returns_false_when_service_inactive(self, mock_run, service_manager):
        """Test is_running returns False when service is not active"""
        mock_result = MagicMock()
        mock_result.stdout = "inactive"
        mock_run.return_value = mock_result

        result = service_manager.is_running('nginx')
        
        assert result is False

    @patch('subprocess.run')
    def test_is_running_returns_false_for_unknown_service(self, mock_run, service_manager):
        """Test is_running returns False for unknown service"""
        result = service_manager.is_running('unknown_service')
        
        assert result is False

    @patch('subprocess.run')
    def test_is_running_handles_exception(self, mock_run, service_manager):
        """Test is_running handles exceptions gracefully"""
        mock_run.side_effect = Exception("Systemctl failed")
        
        result = service_manager.is_running('nginx')
        
        assert result is False


class TestServiceManagerStart:
    """Test suite for start method"""

    @pytest.fixture
    def service_manager(self):
        from wslaragon.core.services import ServiceManager
        return ServiceManager()

    @patch('subprocess.run')
    def test_start_service_returns_true_on_success(self, mock_run, service_manager):
        """Test start returns True on successful execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = service_manager.start('nginx')
        
        assert result is True
        mock_run.assert_called_once()
        # Verify sudo systemctl start was called
        call_args = mock_run.call_args[0][0]
        assert 'sudo' in call_args
        assert 'systemctl' in call_args
        assert 'start' in call_args

    @patch('subprocess.run')
    def test_start_service_returns_false_on_failure(self, mock_run, service_manager):
        """Test start returns False on failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = service_manager.start('nginx')
        
        assert result is False

    @patch('subprocess.run')
    def test_start_unknown_service_returns_false(self, mock_run, service_manager):
        """Test start returns False for unknown service"""
        result = service_manager.start('unknown')
        
        assert result is False


class TestServiceManagerStop:
    """Test suite for stop method"""

    @pytest.fixture
    def service_manager(self):
        from wslaragon.core.services import ServiceManager
        return ServiceManager()

    @patch('subprocess.run')
    def test_stop_service_returns_true_on_success(self, mock_run, service_manager):
        """Test stop returns True on successful execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = service_manager.stop('nginx')
        
        assert result is True

    @patch('subprocess.run')
    def test_stop_service_returns_false_on_failure(self, mock_run, service_manager):
        """Test stop returns False on failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = service_manager.stop('nginx')
        
        assert result is False


class TestServiceManagerRestart:
    """Test suite for restart method"""

    @pytest.fixture
    def service_manager(self):
        from wslaragon.core.services import ServiceManager
        return ServiceManager()

    @patch('subprocess.run')
    def test_restart_service_returns_true_on_success(self, mock_run, service_manager):
        """Test restart returns True on successful execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = service_manager.restart('nginx')
        
        assert result is True
        call_args = mock_run.call_args[0][0]
        assert 'restart' in call_args

    @patch('subprocess.run')
    def test_restart_service_returns_false_on_failure(self, mock_run, service_manager):
        """Test restart returns False on failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = service_manager.restart('nginx')
        
        assert result is False


class TestServiceManagerStatus:
    """Test suite for status method"""

    @pytest.fixture
    def service_manager(self):
        from wslaragon.core.services import ServiceManager
        return ServiceManager()

    @patch('wslaragon.core.services.ServiceManager.is_running')
    def test_status_returns_dict_for_all_services(self, mock_is_running, service_manager):
        """Test status returns a dictionary with all services"""
        mock_is_running.return_value = True
        
        result = service_manager.status()
        
        assert isinstance(result, dict)
        assert 'nginx' in result
        assert 'mysql' in result
        assert 'php-fpm' in result
        assert 'redis' in result

    @patch('wslaragon.core.services.ServiceManager.is_running')
    def test_status_includes_port_info(self, mock_is_running, service_manager):
        """Test status includes port information for each service"""
        mock_is_running.return_value = True
        
        result = service_manager.status()
        
        for service_info in result.values():
            assert 'port' in service_info
            assert 'running' in service_info
            assert 'service' in service_info

    @patch('wslaragon.core.services.ServiceManager.is_running')
    def test_status_reflects_running_state(self, mock_is_running, service_manager):
        """Test status correctly reflects running state"""
        def side_effect(service_name):
            return service_name in ['nginx', 'mysql']
        
        mock_is_running.side_effect = side_effect
        
        result = service_manager.status()
        
        assert result['nginx']['running'] is True
        assert result['mysql']['running'] is True
        assert result['php-fpm']['running'] is False
        assert result['redis']['running'] is False