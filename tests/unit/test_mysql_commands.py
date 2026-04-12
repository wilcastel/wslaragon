"""Tests for mysql_commands CLI module"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, call


class TestMysqlDatabasesCommand:
    """Test suite for 'mysql databases' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.mysql_commands.Config') as mock_config, \
             patch('wslaragon.cli.mysql_commands.MySQLManager') as mock_mysql:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_mysql_instance = MagicMock()
            mock_mysql.return_value = mock_mysql_instance
            yield {
                'config': mock_config_instance,
                'mysql': mock_mysql_instance,
            }

    def test_mysql_databases_success(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].list_databases.return_value = ['mydb', 'testdb', 'appdb']
        mock_deps['mysql'].get_database_size.side_effect = ['1.5 MB', '0.5 MB', '10 MB']

        result = runner.invoke(mysql, ['databases'])

        assert result.exit_code == 0
        assert 'mydb' in result.output
        assert 'testdb' in result.output
        assert 'appdb' in result.output
        mock_deps['mysql'].list_databases.assert_called_once()

    def test_mysql_databases_shows_sizes(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].list_databases.return_value = ['mydb', 'testdb']
        mock_deps['mysql'].get_database_size.side_effect = ['5 MB', '2 MB']

        result = runner.invoke(mysql, ['databases'])

        assert result.exit_code == 0
        assert '5 MB' in result.output
        assert '2 MB' in result.output

    def test_mysql_databases_unknown_size(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].list_databases.return_value = ['mydb']
        mock_deps['mysql'].get_database_size.return_value = None

        result = runner.invoke(mysql, ['databases'])

        assert result.exit_code == 0
        assert 'Unknown' in result.output

    def test_mysql_databases_empty_list(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].list_databases.return_value = []

        result = runner.invoke(mysql, ['databases'])

        assert result.exit_code == 0
        assert 'MySQL Databases' in result.output

    def test_mysql_databases_table_format(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].list_databases.return_value = ['db1', 'db2']
        mock_deps['mysql'].get_database_size.side_effect = ['1 MB', '2 MB']

        result = runner.invoke(mysql, ['databases'])

        assert result.exit_code == 0
        assert 'Database' in result.output
        assert 'Size' in result.output

    def test_mysql_databases_multiple_dbs_get_size_called(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].list_databases.return_value = ['db1', 'db2', 'db3']
        mock_deps['mysql'].get_database_size.side_effect = ['1 MB', '2 MB', '3 MB']

        runner.invoke(mysql, ['databases'])

        assert mock_deps['mysql'].get_database_size.call_count == 3
        mock_deps['mysql'].get_database_size.assert_has_calls([
            call('db1'),
            call('db2'),
            call('db3'),
        ])


class TestMysqlCreateDbCommand:
    """Test suite for 'mysql create-db <name>' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.mysql_commands.Config') as mock_config, \
             patch('wslaragon.cli.mysql_commands.MySQLManager') as mock_mysql:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_mysql_instance = MagicMock()
            mock_mysql.return_value = mock_mysql_instance
            yield {
                'config': mock_config_instance,
                'mysql': mock_mysql_instance,
            }

    def test_mysql_create_db_success(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].create_database.return_value = (True, None)

        result = runner.invoke(mysql, ['create-db', 'newdb'])

        assert result.exit_code == 0
        assert 'newdb' in result.output
        assert 'created' in result.output.lower()
        mock_deps['mysql'].create_database.assert_called_once_with('newdb')

    def test_mysql_create_db_failure(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].create_database.return_value = (False, 'Connection failed')

        result = runner.invoke(mysql, ['create-db', 'newdb'])

        assert result.exit_code == 0
        assert 'Failed' in result.output
        assert 'newdb' in result.output
        mock_deps['mysql'].create_database.assert_called_once_with('newdb')

    def test_mysql_create_db_displays_db_name(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].create_database.return_value = (True, None)

        result = runner.invoke(mysql, ['create-db', 'myproject_db'])

        assert result.exit_code == 0
        assert 'myproject_db' in result.output

    def test_mysql_create_db_with_checkmark_on_success(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].create_database.return_value = (True, None)

        result = runner.invoke(mysql, ['create-db', 'testdb'])

        assert result.exit_code == 0
        assert 'testdb' in result.output

    def test_mysql_create_db_with_error_message(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].create_database.return_value = (False, 'Database already exists')

        result = runner.invoke(mysql, ['create-db', 'existingdb'])

        assert result.exit_code == 0
        assert 'Failed' in result.output
        assert 'Error:' in result.output

    def test_mysql_create_db_invalid_name(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].create_database.return_value = (False, 'Invalid database name')

        result = runner.invoke(mysql, ['create-db', 'db; DROP'])

        assert result.exit_code == 0
        assert 'Failed' in result.output


class TestMysqlDropDbCommand:
    """Test suite for 'mysql drop-db <name>' command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_deps(self):
        with patch('wslaragon.cli.mysql_commands.Config') as mock_config, \
             patch('wslaragon.cli.mysql_commands.MySQLManager') as mock_mysql:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_mysql_instance = MagicMock()
            mock_mysql.return_value = mock_mysql_instance
            yield {
                'config': mock_config_instance,
                'mysql': mock_mysql_instance,
            }

    def test_mysql_drop_db_confirmed_success(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].drop_database.return_value = True

        result = runner.invoke(mysql, ['drop-db', 'olddb'], input='y\n')

        assert result.exit_code == 0
        assert 'olddb' in result.output
        assert 'dropped' in result.output.lower()
        mock_deps['mysql'].drop_database.assert_called_once_with('olddb')

    def test_mysql_drop_db_confirmed_failure(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].drop_database.return_value = False

        result = runner.invoke(mysql, ['drop-db', 'olddb'], input='y\n')

        assert result.exit_code == 0
        assert 'Failed' in result.output
        assert 'olddb' in result.output
        mock_deps['mysql'].drop_database.assert_called_once_with('olddb')

    def test_mysql_drop_db_cancelled(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        result = runner.invoke(mysql, ['drop-db', 'olddb'], input='n\n')

        assert result.exit_code == 0
        mock_deps['mysql'].drop_database.assert_not_called()

    def test_mysql_drop_db_shows_confirmation_prompt(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].drop_database.return_value = True

        result = runner.invoke(mysql, ['drop-db', 'mydb'], input='y\n')

        assert result.exit_code == 0
        assert 'Are you sure' in result.output
        assert 'mydb' in result.output

    def test_mysql_drop_db_displays_db_name_in_confirm(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].drop_database.return_value = True

        result = runner.invoke(mysql, ['drop-db', 'project_db'], input='y\n')

        assert result.exit_code == 0
        assert 'project_db' in result.output

    def test_mysql_drop_db_invalid_name(self, runner, mock_deps):
        from wslaragon.cli.mysql_commands import mysql

        mock_deps['mysql'].drop_database.return_value = False

        result = runner.invoke(mysql, ['drop-db', 'db; DROP'], input='y\n')

        assert result.exit_code == 0
        assert 'Failed' in result.output


class TestMysqlCommandGroup:
    """Test suite for mysql command group"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_mysql_command_group_help(self, runner):
        from wslaragon.cli.mysql_commands import mysql

        result = runner.invoke(mysql, ['--help'])

        assert result.exit_code == 0
        assert 'databases' in result.output
        assert 'create-db' in result.output
        assert 'drop-db' in result.output

    def test_mysql_command_without_subcommand(self, runner):
        from wslaragon.cli.mysql_commands import mysql

        result = runner.invoke(mysql, [])

        # Click groups return exit_code 2 when no subcommand is provided
        assert result.exit_code == 2
        assert 'Commands:' in result.output

    def test_mysql_databases_help(self, runner):
        from wslaragon.cli.mysql_commands import mysql

        result = runner.invoke(mysql, ['databases', '--help'])

        assert result.exit_code == 0
        assert 'MySQL' in result.output
        assert 'databases' in result.output.lower()

    def test_mysql_create_db_help(self, runner):
        from wslaragon.cli.mysql_commands import mysql

        result = runner.invoke(mysql, ['create-db', '--help'])

        assert result.exit_code == 0
        assert 'Create' in result.output or 'create' in result.output
        assert 'database' in result.output.lower()

    def test_mysql_drop_db_help(self, runner):
        from wslaragon.cli.mysql_commands import mysql

        result = runner.invoke(mysql, ['drop-db', '--help'])

        assert result.exit_code == 0
        assert 'Drop' in result.output or 'drop' in result.output
        assert 'database' in result.output.lower()