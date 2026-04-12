"""Tests for the node_commands CLI module"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestNodeListCommand:
    """Test suite for 'node list' command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_pm2_manager(self):
        """Mock PM2Manager"""
        with patch('wslaragon.cli.node_commands.PM2Manager') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance

    def test_node_list_empty_processes(self, runner, mock_pm2_manager):
        """Test 'node list' with no processes"""
        mock_pm2_manager.list_processes.return_value = []

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['list'])

        assert result.exit_code == 0
        assert 'No running Node processes found' in result.output
        mock_pm2_manager.list_processes.assert_called_once()

    def test_node_list_with_processes(self, runner, mock_pm2_manager):
        """Test 'node list' with running processes"""
        mock_pm2_manager.list_processes.return_value = [
            {
                'pm_id': 0,
                'name': 'app1',
                'pm2_env': {'status': 'online', 'pm_uptime': 1234567890},
                'monit': {'memory': 104857600}  # 100MB
            },
            {
                'pm_id': 1,
                'name': 'app2',
                'pm2_env': {'status': 'stopped', 'pm_uptime': 1234567890},
                'monit': {'memory': 52428800}  # 50MB
            }
        ]

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['list'])

        assert result.exit_code == 0
        assert 'app1' in result.output
        assert 'app2' in result.output
        mock_pm2_manager.list_processes.assert_called_once()

    def test_node_list_displays_online_status_colored(self, runner, mock_pm2_manager):
        """Test 'node list' shows online status in green"""
        mock_pm2_manager.list_processes.return_value = [
            {
                'pm_id': 0,
                'name': 'online_app',
                'pm2_env': {'status': 'online', 'pm_uptime': 0},
                'monit': {'memory': 10485760}
            }
        ]

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['list'])

        assert result.exit_code == 0
        assert 'online_app' in result.output
        assert 'online' in result.output

    def test_node_list_displays_stopped_status_colored(self, runner, mock_pm2_manager):
        """Test 'node list' shows stopped status in red"""
        mock_pm2_manager.list_processes.return_value = [
            {
                'pm_id': 0,
                'name': 'stopped_app',
                'pm2_env': {'status': 'stopped', 'pm_uptime': 0},
                'monit': {'memory': 10485760}
            }
        ]

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['list'])

        assert result.exit_code == 0
        assert 'stopped_app' in result.output
        assert 'stopped' in result.output

    def test_node_list_handles_missing_fields(self, runner, mock_pm2_manager):
        """Test 'node list' handles processes with missing fields"""
        mock_pm2_manager.list_processes.return_value = [
            {
                'pm_id': 0,
                'name': 'incomplete_app',
            }
        ]

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['list'])

        assert result.exit_code == 0
        assert 'incomplete_app' in result.output

    def test_node_list_formats_memory_in_mb(self, runner, mock_pm2_manager):
        """Test 'node list' correctly formats memory values"""
        mock_pm2_manager.list_processes.return_value = [
            {
                'pm_id': 0,
                'name': 'app',
                'pm2_env': {'status': 'online', 'pm_uptime': 0},
                'monit': {'memory': 15728640}  # 15 MB
            }
        ]

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['list'])

        assert result.exit_code == 0
        assert '15.0 MB' in result.output


class TestNodeStartCommand:
    """Test suite for 'node start' command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock all dependencies for start command"""
        with patch('wslaragon.cli.node_commands.PM2Manager') as mock_pm2, \
             patch('wslaragon.cli.node_commands.Config') as mock_config, \
             patch('wslaragon.cli.node_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.node_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.node_commands.SiteManager') as mock_site_mgr:
            
            mock_pm2_instance = MagicMock()
            mock_pm2.return_value = mock_pm2_instance
            
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            
            mock_nginx_instance = MagicMock()
            mock_nginx.return_value = mock_nginx_instance
            
            mock_mysql_instance = MagicMock()
            mock_mysql.return_value = mock_mysql_instance
            
            mock_site_mgr_instance = MagicMock()
            mock_site_mgr.return_value = mock_site_mgr_instance

            yield {
                'pm2': mock_pm2_instance,
                'config': mock_config_instance,
                'nginx': mock_nginx_instance,
                'mysql': mock_mysql_instance,
                'site_mgr': mock_site_mgr_instance,
            }

    def test_node_start_site_not_found(self, runner, mock_deps):
        """Test 'node start' with non-existent site"""
        mock_deps['site_mgr'].get_site.return_value = None

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'nonexistent'])

        assert result.exit_code == 0
        assert "Site 'nonexistent' not found" in result.output

    def test_node_start_site_no_proxy_port(self, runner, mock_deps):
        """Test 'node start' with site not configured as app"""
        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'regular_site',
            'document_root': '/var/www/site',
            'proxy_port': None,
        }

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'regular_site'])

        assert result.exit_code == 0
        assert 'not configured as an App' in result.output

    def test_node_start_with_app_js(self, runner, mock_deps, tmp_path):
        """Test 'node start' finds and starts app.js"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True)
        app_js = web_root / "app.js"
        app_js.write_text("console.log('test');")

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'testsite',
            'document_root': str(web_root),
            'proxy_port': 3000,
        }
        mock_deps['pm2'].start_process.return_value = {'success': True}
        mock_deps['pm2'].save.return_value = {'success': True}

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'testsite'])

        assert result.exit_code == 0
        assert "Process 'testsite' started" in result.output
        mock_deps['pm2'].start_process.assert_called_once()
        mock_deps['pm2'].save.assert_called_once()

    def test_node_start_with_package_json_fallback(self, runner, mock_deps, tmp_path):
        """Test 'node start' falls back to npm start when package.json exists"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True)
        package_json = web_root / "package.json"
        package_json.write_text('{"name": "test"}')

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'testsite',
            'document_root': str(web_root),
            'proxy_port': 3000,
        }
        mock_deps['pm2']._run_pm2.return_value = {'success': True}
        mock_deps['pm2'].save.return_value = {'success': True}

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'testsite'])

        assert result.exit_code == 0
        assert 'npm start' in result.output.lower() or 'Process' in result.output

    def test_node_start_with_python_main(self, runner, mock_deps, tmp_path):
        """Test 'node start' starts Python main.py"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True)
        main_py = web_root / "main.py"
        main_py.write_text("print('hello')")

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'testsite',
            'document_root': str(web_root),
            'proxy_port': 8000,
        }
        mock_deps['pm2'].start_process.return_value = {'success': True}
        mock_deps['pm2'].save.return_value = {'success': True}

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'testsite'])

        assert result.exit_code == 0
        mock_deps['pm2'].start_process.assert_called_once()
        call_args = mock_deps['pm2'].start_process.call_args
        assert call_args[1]['interpreter'] == 'python3'

    def test_node_start_no_entry_point(self, runner, mock_deps, tmp_path):
        """Test 'node start' fails when no entry point found"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True)

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'testsite',
            'document_root': str(web_root),
            'proxy_port': 3000,
        }

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'testsite'])

        assert result.exit_code == 0
        assert 'No entry point' in result.output

    def test_node_start_failure(self, runner, mock_deps, tmp_path):
        """Test 'node start' handles start failure"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True)
        app_js = web_root / "app.js"
        app_js.write_text("console.log('test');")

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'testsite',
            'document_root': str(web_root),
            'proxy_port': 3000,
        }
        mock_deps['pm2'].start_process.return_value = {
            'success': False,
            'error': 'Port already in use'
        }

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'testsite'])

        assert result.exit_code == 0
        assert 'Failed to start' in result.output
        assert 'Port already in use' in result.output

    def test_node_start_priority_order(self, runner, mock_deps, tmp_path):
        """Test that app.js takes priority over main.py"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True)
        app_js = web_root / "app.js"
        app_js.write_text("console.log('test');")
        main_py = web_root / "main.py"
        main_py.write_text("print('hello')")

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'testsite',
            'document_root': str(web_root),
            'proxy_port': 3000,
        }
        mock_deps['pm2'].start_process.return_value = {'success': True}
        mock_deps['pm2'].save.return_value = {'success': True}

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'testsite'])

        assert result.exit_code == 0
        # Should call start_process (for .js) not with interpreter='python3'
        call_args = mock_deps['pm2'].start_process.call_args
        assert 'interpreter' not in call_args[1] or call_args[1].get('interpreter') is None


class TestNodeStopCommand:
    """Test suite for 'node stop' command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_pm2_manager(self):
        """Mock PM2Manager"""
        with patch('wslaragon.cli.node_commands.PM2Manager') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance

    def test_node_stop_success(self, runner, mock_pm2_manager):
        """Test 'node stop' successfully stops a process"""
        mock_pm2_manager.stop_process.return_value = {'success': True}
        mock_pm2_manager.save.return_value = {'success': True}

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['stop', 'myapp'])

        assert result.exit_code == 0
        assert "Process 'myapp' stopped" in result.output
        mock_pm2_manager.stop_process.assert_called_once_with('myapp')
        mock_pm2_manager.save.assert_called_once()

    def test_node_stop_process_not_found(self, runner, mock_pm2_manager):
        """Test 'node stop' handles non-existent process"""
        mock_pm2_manager.stop_process.return_value = {
            'success': False,
            'error': 'Process not found'
        }

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['stop', 'nonexistent'])

        assert result.exit_code == 0
        assert 'Failed to stop' in result.output
        assert 'Process not found' in result.output

    def test_node_stop_pm2_error(self, runner, mock_pm2_manager):
        """Test 'node stop' handles PM2 errors"""
        mock_pm2_manager.stop_process.return_value = {
            'success': False,
            'error': 'PM2 daemon not running'
        }

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['stop', 'myapp'])

        assert result.exit_code == 0
        assert 'Failed to stop' in result.output


class TestNodeDeleteCommand:
    """Test suite for 'node delete' command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_pm2_manager(self):
        """Mock PM2Manager"""
        with patch('wslaragon.cli.node_commands.PM2Manager') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance

    def test_node_delete_success(self, runner, mock_pm2_manager):
        """Test 'node delete' successfully deletes a process"""
        mock_pm2_manager.delete_process.return_value = {'success': True}
        mock_pm2_manager.save.return_value = {'success': True}

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['delete', 'myapp'])

        assert result.exit_code == 0
        assert "Process 'myapp' deleted" in result.output
        mock_pm2_manager.delete_process.assert_called_once_with('myapp')
        mock_pm2_manager.save.assert_called_once()

    def test_node_delete_process_not_found(self, runner, mock_pm2_manager):
        """Test 'node delete' handles non-existent process"""
        mock_pm2_manager.delete_process.return_value = {
            'success': False,
            'error': 'Process not found'
        }

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['delete', 'nonexistent'])

        assert result.exit_code == 0
        assert 'Failed to delete' in result.output
        assert 'Process not found' in result.output

    def test_node_delete_pm2_error(self, runner, mock_pm2_manager):
        """Test 'node delete' handles PM2 errors"""
        mock_pm2_manager.delete_process.return_value = {
            'success': False,
            'error': 'Cannot delete running process'
        }

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['delete', 'myapp'])

        assert result.exit_code == 0
        assert 'Failed to delete' in result.output


class TestNodeRestartCommand:
    """Test suite for 'node restart' command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_pm2_manager(self):
        """Mock PM2Manager"""
        with patch('wslaragon.cli.node_commands.PM2Manager') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance

    def test_node_restart_success(self, runner, mock_pm2_manager):
        """Test 'node restart' successfully restarts a process"""
        mock_pm2_manager.restart_process.return_value = {'success': True}

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['restart', 'myapp'])

        assert result.exit_code == 0
        assert "Process 'myapp' restarted" in result.output
        mock_pm2_manager.restart_process.assert_called_once_with('myapp')

    def test_node_restart_process_not_found(self, runner, mock_pm2_manager):
        """Test 'node restart' handles non-existent process"""
        mock_pm2_manager.restart_process.return_value = {
            'success': False,
            'error': 'Process not found'
        }

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['restart', 'nonexistent'])

        assert result.exit_code == 0
        assert 'Failed to restart' in result.output
        assert 'Process not found' in result.output

    def test_node_restart_pm2_error(self, runner, mock_pm2_manager):
        """Test 'node restart' handles PM2 errors"""
        mock_pm2_manager.restart_process.return_value = {
            'success': False,
            'error': 'PM2 daemon error'
        }

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['restart', 'myapp'])

        assert result.exit_code == 0
        assert 'Failed to restart' in result.output


class TestNodeCommandGroup:
    """Test suite for node command group"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    def test_node_command_group_help(self, runner):
        """Test 'node --help' shows available subcommands"""
        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['--help'])

        assert result.exit_code == 0
        assert 'list' in result.output
        assert 'start' in result.output
        assert 'stop' in result.output
        assert 'delete' in result.output
        assert 'restart' in result.output

    def test_node_command_without_subcommand(self, runner):
        """Test 'node' without subcommand shows help"""
        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, [])

        # Click 8+ groups show help and return exit_code 0 when no subcommand is provided
        assert result.exit_code == 0
        assert "Usage:" in result.output or "Commands:" in result.output

    @patch('wslaragon.cli.node_commands.PM2Manager')
    def test_all_commands_use_pm2manager(self, mock_pm2_class, runner):
        """Test all commands properly instantiate PM2Manager"""
        mock_pm2_instance = MagicMock()
        mock_pm2_instance.list_processes.return_value = []
        mock_pm2_instance.stop_process.return_value = {'success': True}
        mock_pm2_instance.save.return_value = {'success': True}
        mock_pm2_class.return_value = mock_pm2_instance

        from wslaragon.cli.node_commands import node

        runner.invoke(node, ['list'])
        assert mock_pm2_class.call_count == 1
        
        mock_pm2_class.reset_mock()
        runner.invoke(node, ['stop', 'test'])
        assert mock_pm2_class.call_count == 1


class TestNodeStartEdgeCases:
    """Edge case tests for 'node start' command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock all dependencies for start command"""
        with patch('wslaragon.cli.node_commands.PM2Manager') as mock_pm2, \
             patch('wslaragon.cli.node_commands.Config') as mock_config, \
             patch('wslaragon.cli.node_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.node_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.node_commands.SiteManager') as mock_site_mgr:
            
            mock_pm2_instance = MagicMock()
            mock_pm2.return_value = mock_pm2_instance
            
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            
            mock_nginx_instance = MagicMock()
            mock_nginx.return_value = mock_nginx_instance
            
            mock_mysql_instance = MagicMock()
            mock_mysql.return_value = mock_mysql_instance
            
            mock_site_mgr_instance = MagicMock()
            mock_site_mgr.return_value = mock_site_mgr_instance

            yield {
                'pm2': mock_pm2_instance,
                'config': mock_config_instance,
                'nginx': mock_nginx_instance,
                'mysql': mock_mysql_instance,
                'site_mgr': mock_site_mgr_instance,
            }

    def test_node_start_uses_port_from_site_config(self, runner, mock_deps, tmp_path):
        """Test 'node start' uses proxy_port from site configuration"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True)
        app_js = web_root / "app.js"
        app_js.write_text("console.log('test');")

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'testsite',
            'document_root': str(web_root),
            'proxy_port': 8080,  # Custom port
        }
        mock_deps['pm2'].start_process.return_value = {'success': True}
        mock_deps['pm2'].save.return_value = {'success': True}

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'testsite'])

        assert result.exit_code == 0
        assert 'port 8080' in result.output
        
        call_args = mock_deps['pm2'].start_process.call_args
        assert call_args[0][2] == 8080  # Third argument is port

    def test_node_start_handles_missing_pm2_env(self, runner, mock_deps, tmp_path):
        """Test 'node start' handles PM2 not installed"""
        web_root = tmp_path / "web" / "testsite"
        web_root.mkdir(parents=True)
        app_js = web_root / "app.js"
        app_js.write_text("console.log('test');")

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'testsite',
            'document_root': str(web_root),
            'proxy_port': 3000,
        }
        mock_deps['pm2'].start_process.return_value = {
            'success': False,
            'error': "PM2 not found. Install it with 'npm install -g pm2'"
        }

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'testsite'])

        assert result.exit_code == 0
        assert 'Failed to start' in result.output
        assert 'PM2 not found' in result.output

    def test_node_start_creates_correct_process_name(self, runner, mock_deps, tmp_path):
        """Test 'node start' uses site name as process name"""
        web_root = tmp_path / "web" / "myapp"
        web_root.mkdir(parents=True)
        app_js = web_root / "app.js"
        app_js.write_text("console.log('test');")

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'myapp',
            'document_root': str(web_root),
            'proxy_port': 3000,
        }
        mock_deps['pm2'].start_process.return_value = {'success': True}
        mock_deps['pm2'].save.return_value = {'success': True}

        from wslaragon.cli.node_commands import node

        result = runner.invoke(node, ['start', 'myapp'])

        assert result.exit_code == 0
        call_args = mock_deps['pm2'].start_process.call_args
        assert call_args[0][0] == 'myapp'  # First argument is site_name
        assert call_args[1]['cwd'] == str(web_root)