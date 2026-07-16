"""Tests for the Site Commands CLI module"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, call


class TestSiteCreateCommand:
    """Test suite for site create command"""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock site create dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.site_commands.subprocess.run') as mock_run:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

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
                    'proxy_port': None,
                }
            }
            mock_site_mgr_instance.create_headless_site.return_value = {
                'success': True,
                'site': {
                    'name': 'misitio',
                    'domain': 'misitio.test',
                    'document_root': '/test/web/misitio/front',
                    'web_root': '/test/web/misitio/front/dist',
                    'php': False,
                    'mysql': False,
                    'ssl': True,
                    'proxy_port': None,
                    'headless': True,
                    'frontend': 'astro',
                    'backend': 'wordpress',
                },
                'backend_site': {
                    'name': 'api.misitio',
                    'domain': 'api.misitio.test',
                    'document_root': '/test/web/misitio/back',
                    'web_root': '/test/web/misitio/back',
                }
            }
            mock_site_mgr.return_value = mock_site_mgr_instance

            # Mock sudo check
            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'nginx': mock_nginx,
                'mysql': mock_mysql,
                'site_mgr': mock_site_mgr_instance,
                'run': mock_run,
            }

    def test_site_create_basic(self, runner, mock_deps):
        """Test basic site creation"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['create', 'testsite'])

        # Should attempt to create site
        assert result.exit_code == 0

    def test_site_create_calls_sudo_check(self, runner, mock_deps):
        """Test that site create checks sudo permissions"""
        from wslaragon.cli.site_commands import site

        runner.invoke(site, ['create', 'testsite'])

        # Should call sudo -v
        mock_deps['run'].assert_called()

    def test_site_create_fails_without_sudo(self, runner, mock_deps):
        """Test that site create fails without sudo"""
        from wslaragon.cli.site_commands import site
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(site, ['create', 'testsite'])

        assert 'sudo' in result.output.lower() or result.exit_code != 0

    def test_site_create_with_php_flag(self, runner, mock_deps):
        """Test site creation with --php flag"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['create', 'testsite', '--php'])

        assert result.exit_code == 0

    def test_site_create_with_mysql_flag(self, runner, mock_deps):
        """Test site creation with --mysql flag"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite',
                'domain': 'testsite.test',
                'document_root': '/test/web/testsite',
                'php': True,
                'mysql': True,
                'ssl': True,
                'database': 'testsite_db',
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--mysql'])

        assert result.exit_code == 0

    def test_site_create_with_ssl_disabled(self, runner, mock_deps):
        """Test site creation with --no-ssl"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite',
                'domain': 'testsite.test',
                'document_root': '/test/web/testsite',
                'php': True,
                'mysql': False,
                'ssl': False,
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--no-ssl'])

        assert result.exit_code == 0

    def test_site_create_with_custom_database(self, runner, mock_deps):
        """Test site creation with custom database name"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite',
                'domain': 'testsite.test',
                'document_root': '/test/web/testsite',
                'php': True,
                'mysql': True,
                'ssl': True,
                'database': 'custom_db',
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--mysql', '--database', 'custom_db'])

        assert result.exit_code == 0

    def test_site_create_with_public_dir(self, runner, mock_deps):
        """Test site creation with --public flag"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['create', 'testsite', '--public'])

        assert result.exit_code == 0

    def test_site_create_with_proxy_port(self, runner, mock_deps):
        """Test site creation with --proxy option"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite',
                'domain': 'testsite.test',
                'document_root': '/test/web/testsite',
                'web_root': '/test/web/testsite',
                'php': False,
                'mysql': False,
                'ssl': True,
                'proxy_port': 3000,
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--proxy', '3000'])

        assert result.exit_code == 0

    def test_site_create_html_type(self, runner, mock_deps):
        """Test site creation with --html flag"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['create', 'testsite', '--html'])

        assert result.exit_code == 0

    def test_site_create_wordpress_type(self, runner, mock_deps):
        """Test site creation with --wordpress flag"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite',
                'domain': 'testsite.test',
                'document_root': '/test/web/testsite',
                'web_root': '/test/web/testsite',
                'php': True,
                'mysql': True,
                'ssl': True,
                'database': 'testsite_db',
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--wordpress'])

        assert result.exit_code == 0

    @patch('wslaragon.cli.site_commands.SudoKeepAlive')
    def test_site_create_uses_sudo_keep_alive(self, mock_keep_alive, runner, mock_deps):
        """Site create must wrap the operation in SudoKeepAlive context manager."""
        from wslaragon.cli.site_commands import site

        mock_keep_alive.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_keep_alive.return_value.__exit__ = MagicMock(return_value=False)

        result = runner.invoke(site, ['create', 'testsite'])

        assert result.exit_code == 0
        mock_keep_alive.assert_called_once()
        mock_keep_alive.return_value.__enter__.assert_called_once()
        mock_keep_alive.return_value.__exit__.assert_called_once()

    @patch('wslaragon.cli.site_commands.SudoKeepAlive')
    def test_site_create_headless_uses_sudo_keep_alive(self, mock_keep_alive, runner, mock_deps):
        """Headless site create must also wrap the operation in SudoKeepAlive."""
        from wslaragon.cli.site_commands import site

        mock_keep_alive.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_keep_alive.return_value.__exit__ = MagicMock(return_value=False)

        result = runner.invoke(site, [
            'create', '--headless', '--backend=wordpress', '--frontend=astro', '--url=misitio'
        ])

        assert result.exit_code == 0
        mock_keep_alive.assert_called_once()
        mock_keep_alive.return_value.__enter__.assert_called_once()
        mock_keep_alive.return_value.__exit__.assert_called_once()

    def test_site_create_headless_calls_headless_manager(self, runner, mock_deps):
        """Test headless site creation dispatches to create_headless_site."""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, [
            'create', '--headless', '--backend=wordpress', '--frontend=astro', '--url=misitio'
        ])

        assert result.exit_code == 0
        mock_deps['site_mgr'].create_headless_site.assert_called_once_with(
            'misitio', backend='wordpress', frontend='astro', ssl=True,
            database_name=None, recreate=False
        )

    def test_site_create_headless_requires_url(self, runner, mock_deps):
        """Test headless site creation requires --url."""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, [
            'create', '--headless', '--backend=wordpress', '--frontend=astro'
        ])

        assert result.exit_code == 0
        assert '--url is required' in result.output
        mock_deps['site_mgr'].create_headless_site.assert_not_called()

    def test_site_create_headless_requires_backend_and_frontend(self, runner, mock_deps):
        """Test headless site creation requires both --backend and --frontend."""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['create', '--headless', '--url=misitio'])

        assert result.exit_code == 0
        assert '--backend and --frontend are required' in result.output
        mock_deps['site_mgr'].create_headless_site.assert_not_called()

    def test_site_create_missing_name_for_non_headless(self, runner, mock_deps):
        """Test that a non-headless create without NAME reports a friendly error."""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['create'])

        assert result.exit_code == 0
        assert "Missing argument 'NAME'" in result.output
        mock_deps['site_mgr'].create_site.assert_not_called()

    def test_site_create_astro_forces_php_off(self, runner, mock_deps):
        """Test that --astro overrides --php to disable PHP (SSG sites serve dist/ directly)."""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite', 'domain': 'testsite.test', 'document_root': '/test/web/testsite',
                'php': False, 'mysql': False, 'ssl': True, 'proxy_port': None,
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--astro', '--php'])

        assert result.exit_code == 0
        assert mock_deps['site_mgr'].create_site.call_args.kwargs['php'] is False

    def test_site_create_phpmyadmin_disables_mysql_by_default(self, runner, mock_deps):
        """Test that --phpmyadmin defaults mysql to False since it manages existing DBs."""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite', 'domain': 'testsite.test', 'document_root': '/test/web/testsite',
                'php': True, 'mysql': False, 'ssl': True, 'proxy_port': None,
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--phpmyadmin'])

        assert result.exit_code == 0
        assert mock_deps['site_mgr'].create_site.call_args.kwargs['mysql'] is False

    def test_site_create_headless_accepts_sveltkit_alias(self, runner, mock_deps):
        """Test headless site creation accepts the common sveltkit spelling alias."""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, [
            'create', '--headless', '--backend=wordpress', '--frontend=sveltkit', '--url=misitio'
        ])

        assert result.exit_code == 0
        mock_deps['site_mgr'].create_headless_site.assert_called_once_with(
            'misitio', backend='wordpress', frontend='sveltekit', ssl=True,
            database_name=None, recreate=False
        )

    def test_site_create_literal_name_headless_creates_normal_site(self, runner, mock_deps):
        """A site literally named 'headless' (no --headless flag) must not be hijacked."""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'headless', 'domain': 'headless.test', 'document_root': '/var/www/headless',
                'php': True, 'proxy_port': None, 'mysql': False, 'ssl': True,
            }
        }

        result = runner.invoke(site, ['create', 'headless', '--no-mysql'])

        assert result.exit_code == 0
        mock_deps['site_mgr'].create_site.assert_called_once()
        assert mock_deps['site_mgr'].create_site.call_args[0][0] == 'headless'
        mock_deps['site_mgr'].create_headless_site.assert_not_called()

    def test_site_create_laravel_type(self, runner, mock_deps):
        """Test site creation with --laravel flag"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite',
                'domain': 'testsite.test',
                'document_root': '/test/web/testsite',
                'web_root': '/test/web/testsite',
                'php': True,
                'mysql': True,
                'ssl': True,
                'database': 'testsite_db',
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--laravel=11'])

        assert result.exit_code == 0

    def test_site_create_node_type(self, runner, mock_deps):
        """Test site creation with --node flag"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite',
                'domain': 'testsite.test',
                'document_root': '/test/web/testsite',
                'web_root': '/test/web/testsite',
                'php': False,
                'mysql': False,
                'ssl': True,
                'proxy_port': 3000,
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--node'])

        assert result.exit_code == 0

    def test_site_create_python_type(self, runner, mock_deps):
        """Test site creation with --python flag"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite',
                'domain': 'testsite.test',
                'document_root': '/test/web/testsite',
                'web_root': '/test/web/testsite',
                'php': False,
                'mysql': False,
                'ssl': True,
                'proxy_port': 8000,
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--python'])

        assert result.exit_code == 0

    def test_site_create_vite_type(self, runner, mock_deps):
        """Test site creation with --vite flag"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite',
                'domain': 'testsite.test',
                'document_root': '/test/web/testsite',
                'web_root': '/test/web/testsite',
                'php': False,
                'mysql': False,
                'ssl': True,
                'proxy_port': 5173,
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--vite', 'react'])

        assert result.exit_code == 0

    def test_site_create_with_postgres(self, runner, mock_deps):
        """Test site creation with --postgres flag"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': True,
            'site': {
                'name': 'testsite',
                'domain': 'testsite.test',
                'document_root': '/test/web/testsite',
                'web_root': '/test/web/testsite',
                'php': True,
                'mysql': False,
                'ssl': True,
                'db_type': 'postgres',
                'database': 'testsite_db',
            }
        }

        result = runner.invoke(site, ['create', 'testsite', '--laravel=11', '--postgres'])

        assert result.exit_code == 0

    def test_site_create_with_force(self, runner, mock_deps):
        """Test site creation with --force flag"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['create', 'testsite', '--force'])

        assert result.exit_code == 0

    def test_site_create_shows_error_on_failure(self, runner, mock_deps):
        """Test site creation shows error on failure"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].create_site.return_value = {
            'success': False,
            'error': 'Site already exists'
        }

        result = runner.invoke(site, ['create', 'testsite'])

        assert 'error' in result.output.lower() or 'failed' in result.output.lower() or result.exit_code != 0


class TestSiteListCommand:
    """Test suite for site list command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock site list dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr.return_value = mock_site_mgr_instance

            yield {
                'config': mock_config_instance,
                'site_mgr': mock_site_mgr_instance,
            }

    def test_site_list_empty(self, runner, mock_deps):
        """Test site list with no sites"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].list_sites.return_value = []

        result = runner.invoke(site, ['list'])

        assert result.exit_code == 0
        assert 'no sites' in result.output.lower()

    def test_site_list_with_sites(self, runner, mock_deps):
        """Test site list with multiple sites"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].list_sites.return_value = [
            {'name': 'site1', 'domain': 'site1.test', 'php': True, 'mysql': True, 'ssl': True, 'enabled': True},
            {'name': 'site2', 'domain': 'site2.test', 'php': False, 'mysql': False, 'ssl': False, 'enabled': False},
        ]

        result = runner.invoke(site, ['list'])

        assert result.exit_code == 0
        assert 'site1' in result.output
        assert 'site2' in result.output

    def test_site_list_shows_enabled_status(self, runner, mock_deps):
        """Test site list shows enabled/disabled status"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].list_sites.return_value = [
            {'name': 'enabled_site', 'domain': 'enabled.test', 'php': True, 'mysql': False, 'ssl': True, 'enabled': True},
            {'name': 'disabled_site', 'domain': 'disabled.test', 'php': True, 'mysql': False, 'ssl': False, 'enabled': False},
        ]

        result = runner.invoke(site, ['list'])

        assert 'Enabled' in result.output or 'enabled' in result.output
        assert 'Disabled' in result.output or 'disabled' in result.output

    def test_site_list_shows_proxy_port(self, runner, mock_deps):
        """Test site list shows proxy port for Node/Python sites"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].list_sites.return_value = [
            {'name': 'nodeapp', 'domain': 'nodeapp.test', 'php': False, 'mysql': False, 'ssl': True, 'enabled': True, 'proxy_port': 3000},
        ]

        result = runner.invoke(site, ['list'])

        assert result.exit_code == 0
        assert '3000' in result.output or 'Proxy' in result.output


class TestSiteDeleteCommand:
    """Test suite for site delete command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock site delete dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.site_commands.subprocess.run') as mock_run:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr.return_value = mock_site_mgr_instance

            # Mock sudo check
            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'site_mgr': mock_site_mgr_instance,
                'run': mock_run,
            }

    def test_site_delete_requires_confirmation(self, runner, mock_deps):
        """Test site delete requires confirmation"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = {'name': 'testsite'}
        mock_deps['site_mgr'].delete_site.return_value = {'success': True}

        # Don't provide input - should abort
        result = runner.invoke(site, ['delete', 'testsite'], input='n\n')

        # Should prompt for confirmation
        assert result.exit_code != 0 or 'confirm' in result.output.lower() or 'sure' in result.output.lower()

    def test_site_delete_confirmed(self, runner, mock_deps):
        """Test site delete when confirmed"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = {'name': 'testsite'}
        mock_deps['site_mgr'].delete_site.return_value = {'success': True}

        # 'delete' asks two questions: remove files?, then confirm delete?
        result = runner.invoke(site, ['delete', 'testsite'], input='y\ny\n')

        assert result.exit_code == 0

    def test_site_delete_not_found(self, runner, mock_deps):
        """Test site delete when site not found"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = None

        result = runner.invoke(site, ['delete', 'nonexistent'])

        assert 'not found' in result.output.lower()

    def test_site_delete_with_remove_files(self, runner, mock_deps):
        """Test site delete answering 'yes' to the remove-files prompt"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = {'name': 'testsite'}
        mock_deps['site_mgr'].delete_site.return_value = {'success': True}

        result = runner.invoke(site, ['delete', 'testsite'], input='y\ny\n')

        assert result.exit_code == 0
        mock_deps['site_mgr'].delete_site.assert_called_once_with('testsite', True, False)

    def test_site_delete_with_remove_database(self, runner, mock_deps):
        """Test site delete with --remove-database option"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = {'name': 'testsite', 'database': 'testsite_db'}
        mock_deps['site_mgr'].delete_site.return_value = {'success': True}

        result = runner.invoke(site, ['delete', 'testsite', '--remove-database'], input='y\ny\n')

        assert result.exit_code == 0

    def test_site_delete_headless_warns_about_paired_site(self, runner, mock_deps):
        """Deleting one half of a headless pair warns the user and offers to remove the shared root."""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'misitio', 'headless': True, 'backend_site': 'api.misitio',
            'root': '/test/web/misitio', 'document_root': '/test/web/misitio/front',
        }
        mock_deps['site_mgr'].delete_site.return_value = {'success': True}

        result = runner.invoke(site, ['delete', 'misitio'], input='y\ny\n')

        assert result.exit_code == 0
        assert 'api.misitio' in result.output
        assert '/test/web/misitio' in result.output

    def test_site_delete_failure_path(self, runner, mock_deps):
        """Test site delete when deletion fails"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = {'name': 'testsite'}
        mock_deps['site_mgr'].delete_site.return_value = {'success': False, 'error': 'Database error'}

        result = runner.invoke(site, ['delete', 'testsite'], input='y\ny\n')

        assert 'failed' in result.output.lower() or 'error' in result.output.lower()

    def test_site_delete_cancelled_at_final_confirmation(self, runner, mock_deps):
        """Test that declining the final 'are you sure' prompt cancels without deleting."""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = {'name': 'testsite'}

        # Answer 'y' to remove-files prompt, then 'n' to the final confirmation
        result = runner.invoke(site, ['delete', 'testsite'], input='y\nn\n')

        assert result.exit_code == 0
        assert 'Cancelled' in result.output
        mock_deps['site_mgr'].delete_site.assert_not_called()

    def test_site_delete_keeps_files_when_declined(self, runner, mock_deps):
        """Test that answering 'no' to the remove-files prompt keeps files on disk."""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'testsite', 'document_root': '/test/web/testsite'
        }
        mock_deps['site_mgr'].delete_site.return_value = {'success': True}

        result = runner.invoke(site, ['delete', 'testsite'], input='n\ny\n')

        assert result.exit_code == 0
        assert 'Files kept at: /test/web/testsite' in result.output
        mock_deps['site_mgr'].delete_site.assert_called_once_with('testsite', False, False)

    def test_site_delete_requires_sudo(self, runner, mock_deps):
        """Test site delete checks sudo permissions"""
        from wslaragon.cli.site_commands import site
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(site, ['delete', 'testsite'])

        assert 'sudo' in result.output.lower() or result.exit_code != 0


class TestSiteEnableDisableCommands:
    """Test suite for site enable/disable commands"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock site enable/disable dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr.return_value = mock_site_mgr_instance

            yield {
                'config': mock_config_instance,
                'site_mgr': mock_site_mgr_instance,
            }

    def test_site_enable_success(self, runner, mock_deps):
        """Test site enable command"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].enable_site.return_value = {'success': True}

        result = runner.invoke(site, ['enable', 'testsite'])

        assert result.exit_code == 0

    def test_site_enable_failure(self, runner, mock_deps):
        """Test site enable command failure"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].enable_site.return_value = {'success': False, 'error': 'Site not found'}

        result = runner.invoke(site, ['enable', 'nonexistent'])

        assert result.exit_code == 0
        assert 'error' in result.output.lower() or 'failed' in result.output.lower()

    def test_site_disable_success(self, runner, mock_deps):
        """Test site disable command"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].disable_site.return_value = {'success': True}

        result = runner.invoke(site, ['disable', 'testsite'])

        assert result.exit_code == 0

    def test_site_disable_failure(self, runner, mock_deps):
        """Test site disable command failure"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].disable_site.return_value = {'success': False, 'error': 'Site not found'}

        result = runner.invoke(site, ['disable', 'nonexistent'])

        assert result.exit_code == 0


class TestSitePublicCommand:
    """Test suite for site public command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock site public dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.site_commands.subprocess.run') as mock_run:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr.return_value = mock_site_mgr_instance

            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'site_mgr': mock_site_mgr_instance,
                'run': mock_run,
            }

    def test_site_public_enable(self, runner, mock_deps):
        """Test site public enable"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].update_site_root.return_value = {'success': True}

        result = runner.invoke(site, ['public', 'testsite', '--enable'])

        assert result.exit_code == 0

    def test_site_public_disable(self, runner, mock_deps):
        """Test site public disable"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].update_site_root.return_value = {'success': True}

        result = runner.invoke(site, ['public', 'testsite', '--disable'])

        assert result.exit_code == 0

    def test_site_public_failure(self, runner, mock_deps):
        """Test site public command failure"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].update_site_root.return_value = {'success': False, 'error': 'Site not found'}

        result = runner.invoke(site, ['public', 'testsite'])

        assert 'failed' in result.output.lower() or 'error' in result.output.lower()

    def test_site_public_requires_sudo(self, runner, mock_deps):
        """Test site public requires sudo"""
        from wslaragon.cli.site_commands import site
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(site, ['public', 'testsite'])

        assert 'sudo' in result.output.lower() or result.exit_code != 0


class TestSiteFixPermissionsCommand:
    """Test suite for site fix-permissions command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock site fix-permissions dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.site_commands.subprocess.run') as mock_run:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr.return_value = mock_site_mgr_instance

            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'site_mgr': mock_site_mgr_instance,
                'run': mock_run,
            }

    def test_fix_permissions_success(self, runner, mock_deps):
        """Test fix-permissions command success"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].fix_permissions.return_value = {'success': True}

        result = runner.invoke(site, ['fix-permissions', 'testsite'])

        assert result.exit_code == 0

    def test_fix_permissions_failure(self, runner, mock_deps):
        """Test fix-permissions command failure"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].fix_permissions.return_value = {'success': False, 'error': 'Site not found'}

        result = runner.invoke(site, ['fix-permissions', 'nonexistent'])

        assert 'error' in result.output.lower() or 'failed' in result.output.lower()

    def test_fix_permissions_requires_sudo(self, runner, mock_deps):
        """Test fix-permissions requires sudo"""
        from wslaragon.cli.site_commands import site
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(site, ['fix-permissions', 'testsite'])

        assert 'sudo' in result.output.lower() or result.exit_code != 0


class TestSiteExportCommand:
    """Test suite for site export command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock site export dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.site_commands.BackupManager') as mock_backup, \
             patch('wslaragon.cli.site_commands.subprocess.run') as mock_run:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr.return_value = mock_site_mgr_instance

            mock_backup_instance = MagicMock()
            mock_backup_instance.export_site.return_value = {
                'success': True,
                'file': '/tmp/backup.wslaragon',
                'site': 'testsite'
            }
            mock_backup.return_value = mock_backup_instance

            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'site_mgr': mock_site_mgr_instance,
                'backup': mock_backup_instance,
                'run': mock_run,
            }

    def test_export_success(self, runner, mock_deps):
        """Test site export success"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['export', 'testsite'])

        assert result.exit_code == 0

    def test_export_with_output_path(self, runner, mock_deps):
        """Test site export with custom output path"""
        from wslaragon.cli.site_commands import site

        mock_deps['backup'].export_site.return_value = {
            'success': True,
            'file': '/custom/path/backup.wslaragon',
            'site': 'testsite'
        }

        result = runner.invoke(site, ['export', 'testsite', '--output', '/custom/path'])

        assert result.exit_code == 0

    def test_export_failure(self, runner, mock_deps):
        """Test site export failure"""
        from wslaragon.cli.site_commands import site

        mock_deps['backup'].export_site.return_value = {
            'success': False,
            'error': 'Site not found'
        }

        result = runner.invoke(site, ['export', 'nonexistent'])

        assert 'error' in result.output.lower() or 'failed' in result.output.lower()

    def test_export_requires_sudo(self, runner, mock_deps):
        """Test site export requires sudo"""
        from wslaragon.cli.site_commands import site
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(site, ['export', 'testsite'])

        assert 'sudo' in result.output.lower() or result.exit_code != 0


class TestSiteImportCommand:
    """Test suite for site import command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock site import dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.site_commands.BackupManager') as mock_backup, \
             patch('wslaragon.cli.site_commands.subprocess.run') as mock_run:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr.return_value = mock_site_mgr_instance

            mock_backup_instance = MagicMock()
            mock_backup_instance.import_site.return_value = {
                'success': True,
                'site': 'importedsite',
                'info': {
                    'name': 'importedsite',
                    'domain': 'importedsite.test',
                    'document_root': '/test/web/importedsite',
                }
            }
            mock_backup.return_value = mock_backup_instance

            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'site_mgr': mock_site_mgr_instance,
                'backup': mock_backup_instance,
                'run': mock_run,
            }

    def test_import_success(self, runner, mock_deps):
        """Test site import success"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['import', '/tmp/backup.wslaragon'])

        assert result.exit_code == 0

    def test_import_with_new_name(self, runner, mock_deps):
        """Test site import with custom name"""
        from wslaragon.cli.site_commands import site

        mock_deps['backup'].import_site.return_value = {
            'success': True,
            'site': 'newname',
            'info': {
                'name': 'newname',
                'domain': 'newname.test',
                'document_root': '/test/web/newname',
            }
        }

        result = runner.invoke(site, ['import', '/tmp/backup.wslaragon', '--name', 'newname'])

        assert result.exit_code == 0

    def test_import_failure(self, runner, mock_deps):
        """Test site import failure"""
        from wslaragon.cli.site_commands import site

        mock_deps['backup'].import_site.return_value = {
            'success': False,
            'error': 'Invalid backup file'
        }

        result = runner.invoke(site, ['import', '/tmp/invalid.wslaragon'])

        assert 'error' in result.output.lower() or 'failed' in result.output.lower()

    def test_import_requires_sudo(self, runner, mock_deps):
        """Test site import requires sudo"""
        from wslaragon.cli.site_commands import site
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(site, ['import', '/tmp/backup.wslaragon'])

        assert 'sudo' in result.output.lower() or result.exit_code != 0


class TestSiteSSLCommand:
    """Test suite for site ssl command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock site ssl dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.site_commands.SSLManager') as mock_ssl, \
             patch('wslaragon.cli.site_commands.subprocess.run') as mock_run:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr_instance.get_site.return_value = {
                'name': 'testsite',
                'domain': 'testsite.test',
                'php': True,
                'ssl': False,
                'web_root': '/test/web/testsite',
            }
            mock_site_mgr_instance.tld = '.test'
            mock_site_mgr.return_value = mock_site_mgr_instance

            mock_ssl_instance = MagicMock()
            mock_ssl_instance.setup_ssl_for_site.return_value = {'success': True}
            mock_ssl.return_value = mock_ssl_instance

            mock_nginx_instance = MagicMock()
            mock_nginx_instance.add_site.return_value = (True, None)
            mock_nginx.return_value = mock_nginx_instance

            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'site_mgr': mock_site_mgr_instance,
                'ssl': mock_ssl_instance,
                'nginx': mock_nginx_instance,
                'run': mock_run,
            }

    def test_ssl_enable_success(self, runner, mock_deps):
        """Test site ssl enable success"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['ssl', 'testsite'])

        assert result.exit_code == 0

    def test_ssl_already_enabled(self, runner, mock_deps):
        """Test site ssl when already enabled"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = {
            'name': 'testsite',
            'ssl': True,
        }

        result = runner.invoke(site, ['ssl', 'testsite'])

        assert 'already' in result.output.lower()

    def test_ssl_site_not_found(self, runner, mock_deps):
        """Test site ssl when site not found"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].get_site.return_value = None

        result = runner.invoke(site, ['ssl', 'nonexistent'])

        assert 'not found' in result.output.lower()

    def test_ssl_requires_sudo(self, runner, mock_deps):
        """Test site ssl requires sudo"""
        from wslaragon.cli.site_commands import site
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(site, ['ssl', 'testsite'])

        assert 'sudo' in result.output.lower() or result.exit_code != 0

    def test_ssl_failure(self, runner, mock_deps):
        """Test site ssl when SSL setup fails"""
        from wslaragon.cli.site_commands import site

        mock_deps['ssl'].setup_ssl_for_site.return_value = {'success': False, 'error': 'SSL error'}

        result = runner.invoke(site, ['ssl', 'testsite'])

        assert 'failed' in result.output.lower() or 'error' in result.output.lower()

    def test_ssl_nginx_failure(self, runner, mock_deps):
        """Test site ssl when nginx fails"""
        from wslaragon.cli.site_commands import site

        mock_deps['nginx'].add_site.return_value = (False, "Nginx error")

        result = runner.invoke(site, ['ssl', 'testsite'])

        assert result.exit_code == 0 or 'failed' in result.output.lower()


class TestSiteApiCommands:
    """Test suite for the 'site api add/remove/list' command group"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        """Mock site api dependencies"""
        with patch('wslaragon.cli.site_commands.Config') as mock_config, \
             patch('wslaragon.cli.site_commands.NginxManager') as mock_nginx, \
             patch('wslaragon.cli.site_commands.MySQLManager') as mock_mysql, \
             patch('wslaragon.cli.site_commands.SiteManager') as mock_site_mgr, \
             patch('wslaragon.cli.site_commands.subprocess.run') as mock_run:

            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance

            mock_site_mgr_instance = MagicMock()
            mock_site_mgr.return_value = mock_site_mgr_instance

            mock_run.return_value = MagicMock(returncode=0)

            yield {
                'config': mock_config_instance,
                'site_mgr': mock_site_mgr_instance,
                'run': mock_run,
            }

    def test_api_add_success(self, runner, mock_deps):
        """Test api add reports success and reload message"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].add_api_proxy.return_value = {
            'success': True, 'path': '/api', 'backend': 'https://api.dash.test'
        }

        result = runner.invoke(site, ['api', 'add', 'dash', '/api', 'https://api.dash.test'])

        assert result.exit_code == 0
        assert 'API proxy added: /api -> https://api.dash.test' in result.output
        mock_deps['site_mgr'].add_api_proxy.assert_called_once_with('dash', '/api', 'https://api.dash.test')

    def test_api_add_failure(self, runner, mock_deps):
        """Test api add reports the error message on failure"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].add_api_proxy.return_value = {'success': False, 'error': 'Site not found'}

        result = runner.invoke(site, ['api', 'add', 'dash', '/api', 'https://api.dash.test'])

        assert result.exit_code == 0
        assert 'Failed to add API proxy: Site not found' in result.output

    def test_api_add_requires_sudo(self, runner, mock_deps):
        """Test api add checks sudo permissions before proceeding"""
        from wslaragon.cli.site_commands import site
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(site, ['api', 'add', 'dash', '/api', 'https://api.dash.test'])

        assert 'sudo' in result.output.lower() or result.exit_code != 0
        mock_deps['site_mgr'].add_api_proxy.assert_not_called()

    def test_api_remove_success(self, runner, mock_deps):
        """Test api remove reports success and reload message"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].remove_api_proxy.return_value = {
            'success': True, 'removed_path': '/api', 'removed_backend': 'https://api.dash.test'
        }

        result = runner.invoke(site, ['api', 'remove', 'dash', '/api'])

        assert result.exit_code == 0
        assert 'API proxy removed: /api (was -> https://api.dash.test)' in result.output
        mock_deps['site_mgr'].remove_api_proxy.assert_called_once_with('dash', '/api')

    def test_api_remove_failure(self, runner, mock_deps):
        """Test api remove reports the error message on failure"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].remove_api_proxy.return_value = {'success': False, 'error': 'Path not found'}

        result = runner.invoke(site, ['api', 'remove', 'dash', '/api'])

        assert result.exit_code == 0
        assert 'Failed to remove API proxy: Path not found' in result.output

    def test_api_remove_requires_sudo(self, runner, mock_deps):
        """Test api remove checks sudo permissions before proceeding"""
        from wslaragon.cli.site_commands import site
        import subprocess

        mock_deps['run'].side_effect = subprocess.CalledProcessError(1, 'sudo')

        result = runner.invoke(site, ['api', 'remove', 'dash', '/api'])

        assert 'sudo' in result.output.lower() or result.exit_code != 0
        mock_deps['site_mgr'].remove_api_proxy.assert_not_called()

    def test_api_list_with_proxies(self, runner, mock_deps):
        """Test api list renders a table of configured proxies"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].list_api_proxies.return_value = {
            'success': True,
            'proxies': {'/api': 'https://api.dash.test', '/auth': 'https://auth.dash.test'}
        }

        result = runner.invoke(site, ['api', 'list', 'dash'])

        assert result.exit_code == 0
        assert 'API Proxies: dash' in result.output
        assert '/api' in result.output
        assert 'https://api.dash.test' in result.output

    def test_api_list_no_proxies(self, runner, mock_deps):
        """Test api list reports when no proxies are configured"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].list_api_proxies.return_value = {'success': True, 'proxies': {}}

        result = runner.invoke(site, ['api', 'list', 'dash'])

        assert result.exit_code == 0
        assert 'No API proxies configured' in result.output

    def test_api_list_failure(self, runner, mock_deps):
        """Test api list reports the error message when the site lookup fails"""
        from wslaragon.cli.site_commands import site

        mock_deps['site_mgr'].list_api_proxies.return_value = {'success': False, 'error': 'Site not found'}

        result = runner.invoke(site, ['api', 'list', 'dash'])

        assert result.exit_code == 0
        assert 'Site not found' in result.output


class TestSiteGroupCommand:
    """Test suite for site group command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_site_group_has_commands(self, runner):
        """Test that site group has all expected commands"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['--help'])

        assert result.exit_code == 0
        assert 'create' in result.output
        assert 'list' in result.output
        assert 'delete' in result.output
        assert 'enable' in result.output
        assert 'disable' in result.output
        assert 'public' in result.output
        assert 'fix-permissions' in result.output
        assert 'export' in result.output
        assert 'import' in result.output
        assert 'ssl' in result.output

    def test_site_create_help(self, runner):
        """Test site create command help"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['create', '--help'])

        assert result.exit_code == 0
        assert '--php' in result.output
        assert '--mysql' in result.output
        assert '--ssl' in result.output
        assert '--wordpress' in result.output
        assert '--laravel' in result.output
        assert '--html' in result.output
        assert '--node' in result.output
        assert '--python' in result.output
        assert '--vite' in result.output

    def test_site_delete_help(self, runner):
        """Test site delete command help"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['delete', '--help'])

        assert result.exit_code == 0
        # File removal is an interactive confirm prompt, not a flag
        assert '--remove-database' in result.output

    def test_site_public_help(self, runner):
        """Test site public command help"""
        from wslaragon.cli.site_commands import site

        result = runner.invoke(site, ['public', '--help'])

        assert result.exit_code == 0
        assert '--enable' in result.output
        assert '--disable' in result.output
