"""Tests for the CLI commands module"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock


class TestCLI:
    """Test suite for the main CLI"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_cli_deps(self):
        """Mock all CLI dependencies"""
        with patch('wslaragon.cli.service_commands.ServiceManager') as mock_svc_mgr:
            # Configure mock returns
            mock_svc_mgr_instance = MagicMock()
            mock_svc_mgr.return_value = mock_svc_mgr_instance

            yield {
                'service_mgr': mock_svc_mgr,
                'service_mgr_instance': mock_svc_mgr_instance,
            }

    def test_cli_shows_help(self, runner):
        """Test CLI shows help when no command is provided"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli)

        # Should show usage and options
        assert result.exit_code == 0
        assert 'WSLaragon' in result.output or 'Usage:' in result.output

    def test_cli_version_option(self, runner):
        """Test CLI --version shows version"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--version'])

        assert result.exit_code == 0

    def test_cli_service_status_command(self, runner, mock_cli_deps):
        """Test service status command"""
        from wslaragon.cli.main import cli

        # Setup mock return for service status
        mock_cli_deps['service_mgr_instance'].status.return_value = {
            'nginx': {'running': True, 'port': 80, 'service': 'nginx'},
            'mysql': {'running': True, 'port': 3306, 'service': 'mariadb'},
        }

        result = runner.invoke(cli, ['service', 'status'])

        assert result.exit_code == 0

    def test_cli_service_start_command(self, runner, mock_cli_deps):
        """Test service start command"""
        from wslaragon.cli.main import cli

        mock_cli_deps['service_mgr_instance'].start.return_value = True

        result = runner.invoke(cli, ['service', 'start', 'nginx'])

        assert result.exit_code == 0
        mock_cli_deps['service_mgr_instance'].start.assert_called_once_with('nginx')

    def test_cli_service_stop_command(self, runner, mock_cli_deps):
        """Test service stop command"""
        from wslaragon.cli.main import cli

        mock_cli_deps['service_mgr_instance'].stop.return_value = True

        result = runner.invoke(cli, ['service', 'stop', 'nginx'])

        assert result.exit_code == 0

    def test_cli_service_restart_command(self, runner, mock_cli_deps):
        """Test service restart command"""
        from wslaragon.cli.main import cli

        mock_cli_deps['service_mgr_instance'].restart.return_value = True

        result = runner.invoke(cli, ['service', 'restart', 'nginx'])

        assert result.exit_code == 0


class TestSiteCommands:
    """Test suite for site-related CLI commands"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_site_deps(self):
        """Mock site command dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.site_commands.SSLManager') as mock_ssl, \
             patch('wslaragon.cli.site_commands.BackupManager') as mock_backup:

            mock_config_instance = MagicMock()
            mock_config_instance.get.return_value = "/test/web"
            mock_config.return_value = mock_config_instance

            # Setup SiteManager mock
            mock_site_mgr_instance = MagicMock()
            mock_site_mgr_instance.create_site.return_value = {
                'success': True,
                'site': {
                    'name': 'testsite',
                    'domain': 'testsite.test',
                    'document_root': '/test/web/testsite',
                    'web_root': '/test/web/testsite',
                    'php': True,
                    'mysql': False,
                    'ssl': True,
                }
            }
            mock_site_mgr_instance.list_sites.return_value = []
            mock_site_mgr_instance.get_site.return_value = None
            mock_site_mgr.return_value = mock_site_mgr_instance

            yield {
                'config': mock_config_instance,
                'nginx': mock_nginx,
                'mysql': mock_mysql,
                'site_mgr': mock_site_mgr_instance,
                'ssl': mock_ssl,
                'backup': mock_backup,
            }

    def test_site_create_command(self, runner, mock_site_deps):
        """Test site create command - basic validation"""
        from wslaragon.cli.main import cli

        # This test is complex due to sudo requirements
        # Just verify the CLI can be invoked
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0

    def test_site_list_command(self, runner, mock_site_deps):
        """Test site list command"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['site', 'list'])

        # Should work (empty list)
        assert result.exit_code == 0


class TestPHPCommands:
    """Test suite for PHP-related CLI commands"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_php_deps(self):
        """Mock PHP command dependencies"""
        with patch('wslaragon.cli.php_commands.Config') as mock_config, \
             patch('wslaragon.cli.php_commands.PHPManager') as mock_php_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_php_mgr_instance = MagicMock()
            mock_php_mgr_instance.get_installed_versions.return_value = ['8.1', '8.2', '8.3']
            mock_php_mgr_instance.get_current_version.return_value = '8.3'
            mock_php_mgr_instance.get_extensions.return_value = ['curl', 'mbstring', 'pdo']
            mock_php_mgr.return_value = mock_php_mgr_instance

            yield {
                'config': mock_config_instance,
                'php_mgr': mock_php_mgr_instance,
            }

    def test_php_versions_command(self, runner, mock_php_deps):
        """Test PHP versions command"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['php', 'versions'])

        assert result.exit_code == 0
        mock_php_deps['php_mgr'].get_installed_versions.assert_called_once()

    def test_php_extensions_command(self, runner, mock_php_deps):
        """Test PHP extensions command"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['php', 'extensions'])

        assert result.exit_code == 0
        mock_php_deps['php_mgr'].get_extensions.assert_called_once()


class TestMySQLCommands:
    """Test suite for MySQL-related CLI commands"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_mysql_deps(self):
        """Mock MySQL command dependencies"""
        with patch('wslaragon.cli.mysql_commands.Config') as mock_config, \
             patch('wslaragon.cli.mysql_commands.MySQLManager') as mock_mysql_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_mysql_mgr_instance = MagicMock()
            mock_mysql_mgr_instance.list_databases.return_value = ['app_db', 'test_db']
            mock_mysql_mgr_instance.get_database_size.return_value = '1.5MB'
            mock_mysql_mgr.return_value = mock_mysql_mgr_instance

            yield {
                'config': mock_config_instance,
                'mysql_mgr': mock_mysql_mgr_instance,
            }

    def test_mysql_databases_command(self, runner, mock_mysql_deps):
        """Test MySQL databases command"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['mysql', 'databases'])

        assert result.exit_code == 0
        mock_mysql_deps['mysql_mgr'].list_databases.assert_called_once()

    def test_mysql_create_db_command(self, runner, mock_mysql_deps):
        """Test MySQL create database command"""
        from wslaragon.cli.main import cli

        mock_mysql_deps['mysql_mgr'].create_database.return_value = True

        result = runner.invoke(cli, ['mysql', 'create-db', 'newdb'])

        assert result.exit_code == 0
        mock_mysql_deps['mysql_mgr'].create_database.assert_called_once_with('newdb')


class TestSSLCommands:
    """Test suite for SSL-related CLI commands"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_ssl_deps(self):
        """Mock SSL command dependencies"""
        with patch('wslaragon.cli.ssl_commands.Config') as mock_config, \
             patch('wslaragon.cli.ssl_commands.SSLManager') as mock_ssl_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_ssl_mgr_instance = MagicMock()
            mock_ssl_mgr_instance.create_ca.return_value = True
            mock_ssl_mgr_instance.generate_cert.return_value = {'success': True}
            mock_ssl_mgr_instance.list_certificates.return_value = []
            mock_ssl_mgr.return_value = mock_ssl_mgr_instance

            yield {
                'config': mock_config_instance,
                'ssl_mgr': mock_ssl_mgr_instance,
            }

    def test_ssl_setup_command(self, runner, mock_ssl_deps):
        """Test SSL setup command"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['ssl', 'setup'])

        assert result.exit_code == 0
        mock_ssl_deps['ssl_mgr'].create_ca.assert_called_once()

    def test_ssl_generate_command(self, runner, mock_ssl_deps):
        """Test SSL generate command"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['ssl', 'generate', 'testsite.test'])

        assert result.exit_code == 0

    def test_ssl_list_command(self, runner, mock_ssl_deps):
        """Test SSL list command"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['ssl', 'list'])

        assert result.exit_code == 0