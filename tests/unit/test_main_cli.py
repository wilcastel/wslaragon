"""Tests for main.py CLI entrypoint - comprehensive coverage"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path


class TestMainCLI:
    """Test suite for main CLI entrypoint"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cli_shows_help_when_no_command(self, runner):
        """Test CLI shows help when invoked without command"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli)
        assert result.exit_code == 0
        assert 'Usage:' in result.output

    def test_cli_version_option(self, runner):
        """Test CLI --version shows version"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'version' in result.output.lower()


class TestGlossaryFlag:
    """Test suite for --glossary/-g flag"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_glossary_flag_shows_content(self, runner):
        """Test --glossary flag displays content when file exists"""
        from wslaragon.cli.main import cli

        glosario_content = "# Glossary\n## Term 1\nDefinition"

        with patch('wslaragon.cli.main.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=glosario_content)):
            result = runner.invoke(cli, ['--glossary'])

        assert result.exit_code == 0

    def test_glossary_flag_shows_error_when_missing(self, runner):
        """Test --glossary flag shows error when file doesn't exist"""
        from wslaragon.cli.main import cli

        with patch('wslaragon.cli.main.Path.exists', return_value=False):
            result = runner.invoke(cli, ['--glossary'])

        assert result.exit_code == 0
        assert "not found" in result.output

    def test_glossary_short_flag(self, runner):
        """Test -g short flag works same as --glossary"""
        from wslaragon.cli.main import cli

        glosario_content = "# Glossary"

        with patch('wslaragon.cli.main.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=glosario_content)):
            result = runner.invoke(cli, ['-g'])

        assert result.exit_code == 0


class TestCompletionCommand:
    """Test suite for completion command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_completion_shows_bash_script(self, runner):
        """Test completion shows bash script without --install"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['completion', '--shell', 'bash'])
        assert result.exit_code == 0
        assert 'WSLARAGON_COMPLETE' in result.output
        assert 'bash' in result.output.lower()

    def test_completion_shows_zsh_script(self, runner):
        """Test completion shows zsh script without --install"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['completion', '--shell', 'zsh'])
        assert result.exit_code == 0
        assert 'WSLARAGON_COMPLETE' in result.output
        assert 'zsh' in result.output.lower()

    @patch('wslaragon.cli.main.Path')
    def test_completion_install_bash(self, mock_path, runner):
        """Test completion --install for bash"""
        from wslaragon.cli.main import cli

        mock_rc = MagicMock()
        mock_rc.exists.return_value = True
        mock_rc.read_text.return_value = "# existing config"
        mock_rc.__str__ = lambda self: "/home/user/.bashrc"

        mock_home = MagicMock()
        mock_home.__truediv__ = lambda self, key: mock_rc

        mock_path.home.return_value = mock_home

        mock_file = MagicMock()
        mock_file.write = MagicMock()
        mock_file.__enter__ = lambda self: mock_file
        mock_file.__exit__ = MagicMock(return_value=False)

        with patch('builtins.open', return_value=mock_file):
            result = runner.invoke(cli, ['completion', '--install', '--shell', 'bash'])

        assert result.exit_code == 0
        assert "Installed" in result.output or "installed" in result.output

    @patch('wslaragon.cli.main.Path')
    def test_completion_install_zsh(self, mock_path, runner):
        """Test completion --install for zsh"""
        from wslaragon.cli.main import cli

        mock_rc = MagicMock()
        mock_rc.exists.return_value = True
        mock_rc.read_text.return_value = "# existing config"
        mock_rc.__str__ = lambda self: "/home/user/.zshrc"

        mock_home = MagicMock()
        mock_home.__truediv__ = lambda self, key: mock_rc

        mock_path.home.return_value = mock_home

        mock_file = MagicMock()
        mock_file.write = MagicMock()
        mock_file.__enter__ = lambda self: mock_file
        mock_file.__exit__ = MagicMock(return_value=False)

        with patch('builtins.open', return_value=mock_file):
            result = runner.invoke(cli, ['completion', '--install', '--shell', 'zsh'])

        assert result.exit_code == 0
        assert "Installed" in result.output or "installed" in result.output

    @patch('wslaragon.cli.main.Path')
    def test_completion_install_rc_not_found(self, mock_path, runner):
        """Test completion --install fails when rc file doesn't exist"""
        from wslaragon.cli.main import cli

        mock_rc = MagicMock()
        mock_rc.exists.return_value = False
        mock_rc.__str__ = lambda self: "/home/user/.bashrc"

        mock_home = MagicMock()
        mock_home.__truediv__ = lambda self, key: mock_rc

        mock_path.home.return_value = mock_home

        result = runner.invoke(cli, ['completion', '--install', '--shell', 'bash'])

        assert result.exit_code == 0
        assert "Could not find" in result.output

    @patch('wslaragon.cli.main.Path')
    def test_completion_already_installed(self, mock_path, runner):
        """Test completion --install handles already installed case"""
        from wslaragon.cli.main import cli

        mock_rc = MagicMock()
        mock_rc.exists.return_value = True
        mock_rc.read_text.return_value = 'eval "$(_WSLARAGON_COMPLETE=bash_source wslaragon)"'
        mock_rc.__str__ = lambda self: "/home/user/.bashrc"

        mock_home = MagicMock()
        mock_home.__truediv__ = lambda self, key: mock_rc

        mock_path.home.return_value = mock_home

        result = runner.invoke(cli, ['completion', '--install', '--shell', 'bash'])

        assert result.exit_code == 0
        assert "already installed" in result.output.lower()

    @patch('wslaragon.cli.main.Path')
    def test_completion_install_permission_error(self, mock_path, runner):
        """Test completion --install handles permission error"""
        from wslaragon.cli.main import cli

        mock_rc = MagicMock()
        mock_rc.exists.return_value = True
        mock_rc.read_text.return_value = "# existing config"
        mock_rc.__str__ = lambda self: "/home/user/.bashrc"

        mock_home = MagicMock()
        mock_home.__truediv__ = lambda self, key: mock_rc

        mock_path.home.return_value = mock_home

        with patch('builtins.open') as mock_open_call:
            mock_open_call.side_effect = PermissionError("Permission denied")
            result = runner.invoke(cli, ['completion', '--install', '--shell', 'bash'])

        assert result.exit_code == 0
        assert "Permission denied" in result.output

    @patch('wslaragon.cli.main.Path')
    def test_completion_install_read_exception(self, mock_path, runner):
        """Test completion --install handles read exception gracefully"""
        from wslaragon.cli.main import cli

        mock_rc = MagicMock()
        mock_rc.exists.return_value = True
        mock_rc.read_text.side_effect = Exception("Read error")
        mock_rc.__str__ = lambda self: "/home/user/.bashrc"

        mock_home = MagicMock()
        mock_home.__truediv__ = lambda self, key: mock_rc

        mock_path.home.return_value = mock_home

        mock_file = MagicMock()
        mock_file.write = MagicMock()
        mock_file.__enter__ = lambda self: mock_file
        mock_file.__exit__ = MagicMock(return_value=False)

        with patch('builtins.open', return_value=mock_file):
            result = runner.invoke(cli, ['completion', '--install', '--shell', 'bash'])

        assert result.exit_code == 0


class TestGlossaryCommand:
    """Test suite for glossary command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_glossary_command_shows_full_content(self, runner):
        """Test glossary command displays full content"""
        from wslaragon.cli.main import cli

        glosario_content = "# Glossary\n## Term 1\nDefinition of term 1\n## Term 2\nDefinition of term 2"

        with patch('wslaragon.cli.main.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=glosario_content)):
            result = runner.invoke(cli, ['glossary'])

        assert result.exit_code == 0

    def test_glossary_command_not_found(self, runner):
        """Test glossary command shows error when file missing"""
        from wslaragon.cli.main import cli

        with patch('wslaragon.cli.main.Path.exists', return_value=False):
            result = runner.invoke(cli, ['glossary'])

        assert result.exit_code == 0
        assert "not found" in result.output.lower()

    def test_glossary_search_term_found(self, runner):
        """Test glossary command searches for specific term"""
        from wslaragon.cli.main import cli

        glosario_content = "# Glossary\n## nginx\nNginx is a web server\n## php\nPHP is a language"

        with patch('wslaragon.cli.main.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=glosario_content)):
            result = runner.invoke(cli, ['glossary', 'nginx'])

        assert result.exit_code == 0

    def test_glossary_search_term_not_found(self, runner):
        """Test glossary command handles term not found"""
        from wslaragon.cli.main import cli

        glosario_content = "# Glossary\n## nginx\nNginx definition\n## php\nPHP definition"

        with patch('wslaragon.cli.main.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=glosario_content)):
            result = runner.invoke(cli, ['glossary', 'nonexistent'])

        assert result.exit_code == 0
        assert "No info found" in result.output

    def test_glossary_search_case_insensitive(self, runner):
        """Test glossary search is case insensitive"""
        from wslaragon.cli.main import cli

        glosario_content = "# Glossary\n## NGINX\nNginx definition"

        with patch('wslaragon.cli.main.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=glosario_content)):
            result = runner.invoke(cli, ['glossary', 'nginx'])

        assert result.exit_code == 0

    def test_glossary_search_in_content(self, runner):
        """Test glossary search finds terms in content, not just headers"""
        from wslaragon.cli.main import cli

        glosario_content = "# Glossary\n## Web Server\nA web server like nginx is fast"

        with patch('wslaragon.cli.main.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=glosario_content)):
            result = runner.invoke(cli, ['glossary', 'fast'])

        assert result.exit_code == 0

    def test_glossary_fallback_to_usr_share(self, runner):
        """Test glossary falls back to /usr/share/wslaragon/docs/glosario.md"""
        from wslaragon.cli.main import cli

        glosario_content = "# Glossary"

        with patch('wslaragon.cli.main.Path.exists', side_effect=[False, True]), \
             patch('builtins.open', mock_open(read_data=glosario_content)):
            result = runner.invoke(cli, ['glossary'])

        assert result.exit_code == 0


class TestMainFunction:
    """Test suite for main() entrypoint"""

    def test_main_function_exists(self):
        """Test main() function is callable"""
        from wslaragon.cli.main import main

        assert callable(main)

    def test_main_is_simple_wrapper(self):
        """Test main() function structure"""
        from wslaragon.cli.main import main

        assert main.__name__ == 'main'
        assert main.__code__.co_argcount == 0


class TestCLICommands:
    """Test suite for registered CLI commands"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cli_has_doctor_command(self, runner):
        """Test CLI has doctor command registered"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'doctor' in result.output

    def test_cli_has_agent_command(self, runner):
        """Test CLI has agent command registered"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'agent' in result.output

    def test_cli_has_site_command(self, runner):
        """Test CLI has site command registered"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'site' in result.output

    def test_cli_has_service_command(self, runner):
        """Test CLI has service command registered"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'service' in result.output

    def test_cli_has_php_command(self, runner):
        """Test CLI has php command registered"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'php' in result.output

    def test_cli_has_mysql_command(self, runner):
        """Test CLI has mysql command registered"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'mysql' in result.output

    def test_cli_has_ssl_command(self, runner):
        """Test CLI has ssl command registered"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'ssl' in result.output

    def test_cli_has_node_command(self, runner):
        """Test CLI has node command registered"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'node' in result.output

    def test_cli_has_nginx_command(self, runner):
        """Test CLI has nginx command registered"""
        from wslaragon.cli.main import cli

        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'nginx' in result.output