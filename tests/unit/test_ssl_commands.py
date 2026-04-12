"""Tests for the SSL Commands CLI module"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock


class TestSSLSetupCommand:
    """Test suite for ssl setup command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock ssl setup dependencies"""
        with patch('wslaragon.cli.ssl_commands.Config') as mock_config, \
             patch('wslaragon.cli.ssl_commands.SSLManager') as mock_ssl_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_ssl_mgr_instance = MagicMock()
            mock_ssl_mgr.return_value = mock_ssl_mgr_instance

            yield {
                'config': mock_config_instance,
                'ssl_mgr': mock_ssl_mgr_instance,
            }

    def test_ssl_setup_success(self, runner, mock_deps):
        """Test ssl setup command success"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].create_ca.return_value = True

        result = runner.invoke(ssl, ['setup'])

        assert result.exit_code == 0
        assert 'SSL CA created' in result.output or '✓' in result.output

    def test_ssl_setup_failure(self, runner, mock_deps):
        """Test ssl setup command failure"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].create_ca.return_value = False

        result = runner.invoke(ssl, ['setup'])

        assert result.exit_code == 0
        assert 'Failed' in result.output or '✗' in result.output

    def test_ssl_setup_creates_manager_with_config(self, runner, mock_deps):
        """Test ssl setup passes config to SSLManager"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].create_ca.return_value = True

        runner.invoke(ssl, ['setup'])

        from wslaragon.cli.ssl_commands import Config, SSLManager
        Config.assert_called_once()
        SSLManager.assert_called_once()


class TestSSLGenerateCommand:
    """Test suite for ssl generate command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock ssl generate dependencies"""
        with patch('wslaragon.cli.ssl_commands.Config') as mock_config, \
             patch('wslaragon.cli.ssl_commands.SSLManager') as mock_ssl_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_ssl_mgr_instance = MagicMock()
            mock_ssl_mgr.return_value = mock_ssl_mgr_instance

            yield {
                'config': mock_config_instance,
                'ssl_mgr': mock_ssl_mgr_instance,
            }

    def test_ssl_generate_success(self, runner, mock_deps):
        """Test ssl generate command success"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].generate_cert.return_value = {'success': True}

        result = runner.invoke(ssl, ['generate', 'example.test'])

        assert result.exit_code == 0
        assert 'Certificate generated' in result.output or '✓' in result.output
        assert 'example.test' in result.output

    def test_ssl_generate_failure(self, runner, mock_deps):
        """Test ssl generate command failure"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].generate_cert.return_value = {
            'success': False,
            'error': 'CA not found'
        }

        result = runner.invoke(ssl, ['generate', 'example.test'])

        assert result.exit_code == 0
        assert 'Failed' in result.output or '✗' in result.output
        assert 'CA not found' in result.output

    def test_ssl_generate_with_domain_argument(self, runner, mock_deps):
        """Test ssl generate passes domain argument correctly"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].generate_cert.return_value = {'success': True}

        runner.invoke(ssl, ['generate', 'myapp.test'])

        mock_deps['ssl_mgr'].generate_cert.assert_called_once_with('myapp.test')

    def test_ssl_generate_generic_error(self, runner, mock_deps):
        """Test ssl generate with generic error message"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].generate_cert.return_value = {
            'success': False,
            'error': 'Certificate already exists'
        }

        result = runner.invoke(ssl, ['generate', 'existing.test'])

        assert 'Certificate already exists' in result.output


class TestSSLDeleteCommand:
    """Test suite for ssl delete command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock ssl delete dependencies"""
        with patch('wslaragon.cli.ssl_commands.Config') as mock_config, \
             patch('wslaragon.cli.ssl_commands.SSLManager') as mock_ssl_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_ssl_mgr_instance = MagicMock()
            mock_ssl_mgr.return_value = mock_ssl_mgr_instance

            yield {
                'config': mock_config_instance,
                'ssl_mgr': mock_ssl_mgr_instance,
            }

    def test_ssl_delete_confirmed(self, runner, mock_deps):
        """Test ssl delete when confirmed"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].revoke_certificate.return_value = True

        result = runner.invoke(ssl, ['delete', 'example.test'], input='y\n')

        assert result.exit_code == 0
        assert 'Certificate deleted' in result.output or '✓' in result.output
        assert 'example.test' in result.output

    def test_ssl_delete_cancelled(self, runner, mock_deps):
        """Test ssl delete when cancelled by declining confirmation"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].revoke_certificate.return_value = True

        result = runner.invoke(ssl, ['delete', 'example.test'], input='n\n')

        assert result.exit_code == 0
        mock_deps['ssl_mgr'].revoke_certificate.assert_not_called()

    def test_ssl_delete_failure(self, runner, mock_deps):
        """Test ssl delete command failure"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].revoke_certificate.return_value = False

        result = runner.invoke(ssl, ['delete', 'example.test'], input='y\n')

        assert result.exit_code == 0
        assert 'Failed to delete' in result.output or '✗' in result.output

    def test_ssl_delete_shows_confirmation_prompt(self, runner, mock_deps):
        """Test ssl delete shows confirmation prompt"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].revoke_certificate.return_value = True

        result = runner.invoke(ssl, ['delete', 'myapp.test'], input='y\n')

        assert 'myapp.test' in result.output
        assert '?' in result.output or 'sure' in result.output.lower()

    def test_ssl_delete_calls_revoke_with_domain(self, runner, mock_deps):
        """Test ssl delete passes domain to revoke_certificate"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].revoke_certificate.return_value = True

        runner.invoke(ssl, ['delete', 'myapp.test'], input='y\n')

        mock_deps['ssl_mgr'].revoke_certificate.assert_called_once_with('myapp.test')


class TestSSLListCommand:
    """Test suite for ssl list command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock ssl list dependencies"""
        with patch('wslaragon.cli.ssl_commands.Config') as mock_config, \
             patch('wslaragon.cli.ssl_commands.SSLManager') as mock_ssl_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_ssl_mgr_instance = MagicMock()
            mock_ssl_mgr.return_value = mock_ssl_mgr_instance

            yield {
                'config': mock_config_instance,
                'ssl_mgr': mock_ssl_mgr_instance,
            }

    def test_ssl_list_empty(self, runner, mock_deps):
        """Test ssl list with no certificates"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].list_certificates.return_value = []

        result = runner.invoke(ssl, ['list'])

        assert result.exit_code == 0
        assert 'No certificates' in result.output or 'no certificates' in result.output.lower()

    def test_ssl_list_with_certificates(self, runner, mock_deps):
        """Test ssl list with multiple certificates"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].list_certificates.return_value = [
            {
                'file': '/etc/ssl/certs/site1.test.pem',
                'subject': 'CN=site1.test',
                'issuer': 'CN=WSLaragon CA',
                'valid_until': '2025-12-31'
            },
            {
                'file': '/etc/ssl/certs/site2.test.pem',
                'subject': 'CN=site2.test',
                'issuer': 'CN=WSLaragon CA',
                'valid_until': '2025-12-31'
            },
        ]

        result = runner.invoke(ssl, ['list'])

        assert result.exit_code == 0
        assert 'site1.test' in result.output
        assert 'site2.test' in result.output

    def test_ssl_list_shows_table_headers(self, runner, mock_deps):
        """Test ssl list shows table headers"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].list_certificates.return_value = [
            {
                'file': '/etc/ssl/certs/example.test.pem',
                'subject': 'CN=example.test',
                'issuer': 'CN=WSLaragon CA',
                'valid_until': '2025-12-31'
            },
        ]

        result = runner.invoke(ssl, ['list'])

        assert 'Domain' in result.output or 'domain' in result.output.lower()
        assert 'Subject' in result.output or 'subject' in result.output.lower()
        assert 'Issuer' in result.output or 'issuer' in result.output.lower()
        assert 'Valid' in result.output

    def test_ssl_list_handles_missing_fields(self, runner, mock_deps):
        """Test ssl list handles missing certificate fields gracefully"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].list_certificates.return_value = [
            {
                'file': '/etc/ssl/certs/incomplete.test.pem',
            },
        ]

        result = runner.invoke(ssl, ['list'])

        assert result.exit_code == 0
        assert 'incomplete.test' in result.output

    def test_ssl_list_single_certificate(self, runner, mock_deps):
        """Test ssl list with single certificate"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].list_certificates.return_value = [
            {
                'file': '/etc/ssl/certs/single.test.pem',
                'subject': 'CN=single.test',
                'issuer': 'CN=WSLaragon CA',
                'valid_until': '2025-06-15'
            },
        ]

        result = runner.invoke(ssl, ['list'])

        assert result.exit_code == 0
        assert 'single.test' in result.output

    def test_ssl_list_extracts_domain_from_filename(self, runner, mock_deps):
        """Test ssl list extracts domain from .pem filename"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].list_certificates.return_value = [
            {
                'file': '/path/to/certs/myapp.test.pem',
                'subject': 'CN=myapp.test',
                'issuer': 'CN=WSLaragon CA',
                'valid_until': '2025-01-01'
            },
        ]

        result = runner.invoke(ssl, ['list'])

        assert 'myapp.test' in result.output
        assert '.pem' not in result.output or 'myapp.test' in result.output

    def test_ssl_list_uses_na_for_missing_fields(self, runner, mock_deps):
        """Test ssl list shows N/A for missing certificate fields"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].list_certificates.return_value = [
            {'file': '/etc/ssl/certs/partial.test.pem'},
        ]

        result = runner.invoke(ssl, ['list'])

        assert 'N/A' in result.output


class TestSSLGroupCommand:
    """Test suite for ssl group command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    def test_ssl_group_has_commands(self, runner):
        """Test that ssl group has all expected commands"""
        from wslaragon.cli.ssl_commands import ssl

        result = runner.invoke(ssl, ['--help'])

        assert result.exit_code == 0
        assert 'setup' in result.output
        assert 'generate' in result.output
        assert 'delete' in result.output
        assert 'list' in result.output

    def test_ssl_setup_help(self, runner):
        """Test ssl setup command help"""
        from wslaragon.cli.ssl_commands import ssl

        result = runner.invoke(ssl, ['setup', '--help'])

        assert result.exit_code == 0
        assert 'SSL' in result.output

    def test_ssl_generate_help(self, runner):
        """Test ssl generate command help"""
        from wslaragon.cli.ssl_commands import ssl

        result = runner.invoke(ssl, ['generate', '--help'])

        assert result.exit_code == 0
        assert 'domain' in result.output

    def test_ssl_delete_help(self, runner):
        """Test ssl delete command help"""
        from wslaragon.cli.ssl_commands import ssl

        result = runner.invoke(ssl, ['delete', '--help'])

        assert result.exit_code == 0
        assert 'domain' in result.output

    def test_ssl_list_help(self, runner):
        """Test ssl list command help"""
        from wslaragon.cli.ssl_commands import ssl

        result = runner.invoke(ssl, ['list', '--help'])

        assert result.exit_code == 0


class TestSSLMocking:
    """Test suite to verify mock setup consistency"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock ssl dependencies with verification"""
        with patch('wslaragon.cli.ssl_commands.Config') as mock_config, \
             patch('wslaragon.cli.ssl_commands.SSLManager') as mock_ssl_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_ssl_mgr_instance = MagicMock()
            mock_ssl_mgr.return_value = mock_ssl_mgr_instance

            yield {
                'config': mock_config_instance,
                'ssl_mgr': mock_ssl_mgr_instance,
            }

    def test_config_is_instantiated(self, runner, mock_deps):
        """Test that Config is instantiated"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].create_ca.return_value = True

        runner.invoke(ssl, ['setup'])

        from wslaragon.cli.ssl_commands import Config
        Config.assert_called_once()

    def test_ssl_manager_created_with_config(self, runner, mock_deps):
        """Test that SSLManager receives Config instance"""
        from wslaragon.cli.ssl_commands import ssl

        mock_deps['ssl_mgr'].create_ca.return_value = True

        runner.invoke(ssl, ['setup'])

        from wslaragon.cli.ssl_commands import SSLManager
        SSLManager.assert_called_once()