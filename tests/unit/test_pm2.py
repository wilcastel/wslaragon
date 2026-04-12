"""Tests for the PM2Manager module"""
import json
import subprocess
from unittest.mock import patch, MagicMock, call

import pytest


class TestPM2ManagerInit:
    """Test suite for PM2Manager initialization"""

    def test_init_without_config(self):
        """Test PM2Manager initializes without config"""
        from wslaragon.services.node.pm2 import PM2Manager
        
        pm2 = PM2Manager()
        
        assert pm2.config is None

    def test_init_with_config(self):
        """Test PM2Manager initializes with config"""
        from wslaragon.services.node.pm2 import PM2Manager
        
        mock_config = MagicMock()
        pm2 = PM2Manager(config=mock_config)
        
        assert pm2.config is mock_config


class TestPM2ManagerRunPM2:
    """Test suite for _run_pm2 method"""

    @pytest.fixture
    def pm2_manager(self):
        """Create a PM2Manager instance"""
        from wslaragon.services.node.pm2 import PM2Manager
        return PM2Manager()

    @patch('subprocess.run')
    def test_run_pm2_success_with_json_output(self, mock_run, pm2_manager):
        """Test _run_pm2 successfully parses JSON output"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{'name': 'app1', 'pm_id': 0}])
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager._run_pm2(['list'])

        assert result['success'] is True
        assert result['data'] == [{'name': 'app1', 'pm_id': 0}]
        assert result['error'] is None
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ['pm2', 'list', '--json']

    @patch('subprocess.run')
    def test_run_pm2_success_with_empty_stdout(self, mock_run, pm2_manager):
        """Test _run_pm2 handles empty stdout on success"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ''
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager._run_pm2(['save'])

        assert result['success'] is True
        assert result['data'] is None
        assert result['error'] == ''

    @patch('subprocess.run')
    def test_run_pm2_error_with_stderr(self, mock_run, pm2_manager):
        """Test _run_pm2 returns error when command fails"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Process not found'
        mock_run.return_value = mock_result

        result = pm2_manager._run_pm2(['stop', 'nonexistent'])

        assert result['success'] is False
        assert result['data'] is None
        assert result['error'] == 'Process not found'

    @patch('subprocess.run')
    def test_run_pm2_error_with_json_output(self, mock_run, pm2_manager):
        """Test _run_pm2 handles JSON output with error return code"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = json.dumps([{'name': 'app1', 'pm_id': 0}])
        mock_result.stderr = 'Some error'
        mock_run.return_value = mock_result

        result = pm2_manager._run_pm2(['list'])

        assert result['success'] is False
        assert result['data'] == [{'name': 'app1', 'pm_id': 0}]
        assert result['error'] == 'Some error'

    @patch('subprocess.run')
    def test_run_pm2_handles_json_decode_error(self, mock_run, pm2_manager):
        """Test _run_pm2 handles non-JSON output gracefully"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'This is plain text, not JSON'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager._run_pm2(['somecommand'])

        assert result['success'] is True
        assert result['data'] is None
        assert 'PM2 output:' in result['error']
        assert 'This is plain text' in result['error']

    @patch('subprocess.run')
    def test_run_pm2_truncates_non_json_output(self, mock_run, pm2_manager):
        """Test _run_pm2 truncates long non-JSON output"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'x' * 500  # Long output
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager._run_pm2(['somecommand'])

        assert result['error'] == "PM2 output: " + 'x' * 200

    @patch('subprocess.run')
    def test_run_pm2_file_not_found(self, mock_run, pm2_manager):
        """Test _run_pm2 handles PM2 not installed"""
        mock_run.side_effect = FileNotFoundError("pm2 not found")

        result = pm2_manager._run_pm2(['list'])

        assert result['success'] is False
        assert "PM2 not found" in result['error']
        assert "npm install -g pm2" in result['error']

    @patch('subprocess.run')
    def test_run_pm2_generic_exception(self, mock_run, pm2_manager):
        """Test _run_pm2 handles generic exceptions"""
        mock_run.side_effect = Exception("Unexpected error")

        result = pm2_manager._run_pm2(['list'])

        assert result['success'] is False
        assert result['error'] == "Unexpected error"

    @patch('subprocess.run')
    @patch('os.environ.copy')
    def test_run_pm2_passes_environment_variables(self, mock_env_copy, mock_run, pm2_manager):
        """Test _run_pm2 passes environment variables to subprocess"""
        mock_env_copy.return_value = {'PATH': '/usr/bin'}
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{}'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        env_vars = {'PORT': '3000', 'NODE_ENV': 'production'}
        result = pm2_manager._run_pm2(['start', 'app.js'], env=env_vars)

        assert result['success'] is True
        call_kwargs = mock_run.call_args[1]
        assert 'env' in call_kwargs
        call_env = call_kwargs['env']
        assert call_env['PORT'] == '3000'
        assert call_env['NODE_ENV'] == 'production'

    @patch('subprocess.run')
    def test_run_pm2_captures_output(self, mock_run, pm2_manager):
        """Test _run_pm2 captures stdout and stderr"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({'pm2_version': '5.0.0'})
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager._run_pm2(['--version'])

        assert result['success'] is True
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs['capture_output'] is True
        assert call_kwargs['text'] is True


class TestPM2ManagerListProcesses:
    """Test suite for list_processes method"""

    @pytest.fixture
    def pm2_manager(self):
        """Create a PM2Manager instance"""
        from wslaragon.services.node.pm2 import PM2Manager
        return PM2Manager()

    @patch('subprocess.run')
    def test_list_processes_success(self, mock_run, pm2_manager):
        """Test list_processes returns process list"""
        processes = [
            {'name': 'app1', 'pm_id': 0, 'pm2_env': {'status': 'online'}},
            {'name': 'app2', 'pm_id': 1, 'pm2_env': {'status': 'online'}}
        ]
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(processes)
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.list_processes()

        assert result == processes
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_list_processes_empty(self, mock_run, pm2_manager):
        """Test list_processes returns empty list when no processes"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([])
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.list_processes()

        assert result == []

    @patch('subprocess.run')
    def test_list_processes_error(self, mock_run, pm2_manager):
        """Test list_processes returns empty list on error"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'PM2 error'
        mock_run.return_value = mock_result

        result = pm2_manager.list_processes()

        assert result == []

    @patch('subprocess.run')
    def test_list_processes_no_json_data(self, mock_run, pm2_manager):
        """Test list_processes handles non-JSON response"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'No processes'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.list_processes()

        assert result == []

    @patch('subprocess.run')
    def test_list_processes_pm2_not_installed(self, mock_run, pm2_manager):
        """Test list_processes when PM2 is not installed"""
        mock_run.side_effect = FileNotFoundError()

        result = pm2_manager.list_processes()

        assert result == []


class TestPM2ManagerStartProcess:
    """Test suite for start_process method"""

    @pytest.fixture
    def pm2_manager(self):
        """Create a PM2Manager instance"""
        from wslaragon.services.node.pm2 import PM2Manager
        return PM2Manager()

    @patch('subprocess.run')
    def test_start_process_basic(self, mock_run, pm2_manager):
        """Test start_process with basic parameters"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{'name': 'testapp', 'pm_id': 0}])
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.start_process('testapp', '/path/to/app.js', 3000)

        assert result['success'] is True
        call_args = mock_run.call_args[0][0]
        assert 'start' in call_args
        assert '/path/to/app.js' in call_args
        assert '--name' in call_args
        assert 'testapp' in call_args
        assert '--env' in call_args
        assert 'PORT=3000' in call_args

    @patch('subprocess.run')
    def test_start_process_with_cwd(self, mock_run, pm2_manager):
        """Test start_process with working directory"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{'name': 'testapp', 'pm_id': 0}])
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.start_process(
            'testapp', '/path/to/app.js', 3000, cwd='/app/directory'
        )

        assert result['success'] is True
        call_args = mock_run.call_args[0][0]
        assert '--cwd' in call_args
        assert '/app/directory' in call_args

    @patch('subprocess.run')
    def test_start_process_with_python_interpreter(self, mock_run, pm2_manager):
        """Test start_process with Python interpreter"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{'name': 'testapp', 'pm_id': 0}])
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.start_process(
            'testapp', '/path/to/main.py', 5000, interpreter='python3'
        )

        assert result['success'] is True
        call_args = mock_run.call_args[0][0]
        assert '--interpreter' in call_args
        assert 'python3' in call_args

    @patch('subprocess.run')
    def test_start_process_skips_node_interpreter(self, mock_run, pm2_manager):
        """Test start_process does not add --interpreter for Node.js"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{'name': 'testapp', 'pm_id': 0}])
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.start_process(
            'testapp', '/path/to/app.js', 3000, interpreter='node'
        )

        assert result['success'] is True
        call_args = mock_run.call_args[0][0]
        assert '--interpreter' not in call_args

    @patch('subprocess.run')
    def test_start_process_with_all_options(self, mock_run, pm2_manager):
        """Test start_process with all optional parameters"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{'name': 'myapp', 'pm_id': 0}])
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.start_process(
            'myapp',
            '/path/to/main.py',
            8000,
            interpreter='python3',
            cwd='/app/directory'
        )

        assert result['success'] is True
        call_args = mock_run.call_args[0][0]
        assert 'start' in call_args
        assert '/path/to/main.py' in call_args
        assert '--name' in call_args
        assert 'myapp' in call_args
        assert '--cwd' in call_args
        assert '--interpreter' in call_args
        assert 'python3' in call_args

    @patch('subprocess.run')
    def test_start_process_error(self, mock_run, pm2_manager):
        """Test start_process handles error"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Script not found'
        mock_run.return_value = mock_result

        result = pm2_manager.start_process('testapp', '/nonexistent/app.js', 3000)

        assert result['success'] is False
        assert 'Script not found' in result['error']

    @patch('subprocess.run')
    def test_start_process_sets_port_env(self, mock_run, pm2_manager):
        """Test start_process sets PORT environment variable"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{}'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        pm2_manager.start_process('app', '/path/app.js', 8080)

        call_kwargs = mock_run.call_args[1]
        assert 'env' in call_kwargs
        assert call_kwargs['env']['PORT'] == '8080'

    @patch('subprocess.run')
    def test_start_process_pm2_not_installed(self, mock_run, pm2_manager):
        """Test start_process when PM2 is not installed"""
        mock_run.side_effect = FileNotFoundError()

        result = pm2_manager.start_process('testapp', '/path/app.js', 3000)

        assert result['success'] is False
        assert "PM2 not found" in result['error']


class TestPM2ManagerStopProcess:
    """Test suite for stop_process method"""

    @pytest.fixture
    def pm2_manager(self):
        """Create a PM2Manager instance"""
        from wslaragon.services.node.pm2 import PM2Manager
        return PM2Manager()

    @patch('subprocess.run')
    def test_stop_process_success(self, mock_run, pm2_manager):
        """Test stop_process successfully stops a process"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{'name': 'testapp', 'pm_id': 0}])
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.stop_process('testapp')

        assert result['success'] is True
        call_args = mock_run.call_args[0][0]
        assert 'stop' in call_args
        assert 'testapp' in call_args

    @patch('subprocess.run')
    def test_stop_process_not_found(self, mock_run, pm2_manager):
        """Test stop_process handles non-existent process"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Process testapp not found'
        mock_run.return_value = mock_result

        result = pm2_manager.stop_process('nonexistent')

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('subprocess.run')
    def test_stop_process_pm2_not_installed(self, mock_run, pm2_manager):
        """Test stop_process when PM2 is not installed"""
        mock_run.side_effect = FileNotFoundError()

        result = pm2_manager.stop_process('testapp')

        assert result['success'] is False
        assert "PM2 not found" in result['error']


class TestPM2ManagerRestartProcess:
    """Test suite for restart_process method"""

    @pytest.fixture
    def pm2_manager(self):
        """Create a PM2Manager instance"""
        from wslaragon.services.node.pm2 import PM2Manager
        return PM2Manager()

    @patch('subprocess.run')
    def test_restart_process_success(self, mock_run, pm2_manager):
        """Test restart_process successfully restarts a process"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{'name': 'testapp', 'pm_id': 0}])
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.restart_process('testapp')

        assert result['success'] is True
        call_args = mock_run.call_args[0][0]
        assert 'restart' in call_args
        assert 'testapp' in call_args

    @patch('subprocess.run')
    def test_restart_process_error(self, mock_run, pm2_manager):
        """Test restart_process handles error"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Process not found'
        mock_run.return_value = mock_result

        result = pm2_manager.restart_process('nonexistent')

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('subprocess.run')
    def test_restart_process_pm2_not_installed(self, mock_run, pm2_manager):
        """Test restart_process when PM2 is not installed"""
        mock_run.side_effect = FileNotFoundError()

        result = pm2_manager.restart_process('testapp')

        assert result['success'] is False
        assert "PM2 not found" in result['error']


class TestPM2ManagerDeleteProcess:
    """Test suite for delete_process method"""

    @pytest.fixture
    def pm2_manager(self):
        """Create a PM2Manager instance"""
        from wslaragon.services.node.pm2 import PM2Manager
        return PM2Manager()

    @patch('subprocess.run')
    def test_delete_process_success(self, mock_run, pm2_manager):
        """Test delete_process successfully deletes a process"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([])
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.delete_process('testapp')

        assert result['success'] is True
        call_args = mock_run.call_args[0][0]
        assert 'delete' in call_args
        assert 'testapp' in call_args

    @patch('subprocess.run')
    def test_delete_process_not_found(self, mock_run, pm2_manager):
        """Test delete_process handles non-existent process"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Process not found'
        mock_run.return_value = mock_result

        result = pm2_manager.delete_process('nonexistent')

        assert result['success'] is False

    @patch('subprocess.run')
    def test_delete_process_pm2_not_installed(self, mock_run, pm2_manager):
        """Test delete_process when PM2 is not installed"""
        mock_run.side_effect = FileNotFoundError()

        result = pm2_manager.delete_process('testapp')

        assert result['success'] is False
        assert "PM2 not found" in result['error']


class TestPM2ManagerSave:
    """Test suite for save method"""

    @pytest.fixture
    def pm2_manager(self):
        """Create a PM2Manager instance"""
        from wslaragon.services.node.pm2 import PM2Manager
        return PM2Manager()

    @patch('subprocess.run')
    def test_save_success(self, mock_run, pm2_manager):
        """Test save successfully saves process list"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ''
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager.save()

        assert result['success'] is True
        call_args = mock_run.call_args[0][0]
        assert 'save' in call_args

    @patch('subprocess.run')
    def test_save_error(self, mock_run, pm2_manager):
        """Test save handles error"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Failed to save'
        mock_run.return_value = mock_result

        result = pm2_manager.save()

        assert result['success'] is False
        assert 'Failed to save' in result['error']

    @patch('subprocess.run')
    def test_save_pm2_not_installed(self, mock_run, pm2_manager):
        """Test save when PM2 is not installed"""
        mock_run.side_effect = FileNotFoundError()

        result = pm2_manager.save()

        assert result['success'] is False
        assert "PM2 not found" in result['error']


class TestPM2ManagerIntegration:
    """Integration-style tests for multiple PM2 operations"""

    @pytest.fixture
    def pm2_manager(self):
        """Create a PM2Manager instance"""
        from wslaragon.services.node.pm2 import PM2Manager
        return PM2Manager()

    @patch('subprocess.run')
    def test_start_stop_delete_workflow(self, mock_run, pm2_manager):
        """Test typical workflow: start, stop, delete"""
        start_result = MagicMock()
        start_result.returncode = 0
        start_result.stdout = json.dumps([{'name': 'app', 'pm_id': 0}])
        start_result.stderr = ''
        
        stop_result = MagicMock()
        stop_result.returncode = 0
        stop_result.stdout = json.dumps([{'name': 'app', 'pm_id': 0}])
        stop_result.stderr = ''
        
        delete_result = MagicMock()
        delete_result.returncode = 0
        delete_result.stdout = '[]'
        delete_result.stderr = ''
        
        mock_run.side_effect = [start_result, stop_result, delete_result]

        r1 = pm2_manager.start_process('app', '/app/app.js', 3000)
        assert r1['success'] is True

        r2 = pm2_manager.stop_process('app')
        assert r2['success'] is True

        r3 = pm2_manager.delete_process('app')
        assert r3['success'] is True

        assert mock_run.call_count == 3

    @patch('subprocess.run')
    def test_json_parse_error_non_json_stdout(self, mock_run, pm2_manager):
        """Test handling of non-JSON stdout with special characters"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success: process started\n[INFO] Running...'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        result = pm2_manager._run_pm2(['start', 'app.js'])

        assert result['success'] is True
        assert result['data'] is None
        assert 'PM2 output:' in result['error']