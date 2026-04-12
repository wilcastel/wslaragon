"""Tests for MySQL manager module"""
import subprocess
from unittest.mock import patch, MagicMock, call
import pytest


class TestValidateIdentifier:
    """Test suite for _validate_identifier function"""

    def test_valid_simple_name(self):
        """Test that simple alphanumeric names are valid"""
        from wslaragon.services.mysql import _validate_identifier
        _validate_identifier("mydb")  # Should not raise

    def test_valid_name_with_underscore(self):
        """Test that names with underscores are valid"""
        from wslaragon.services.mysql import _validate_identifier
        _validate_identifier("my_db")  # Should not raise

    def test_valid_name_with_numbers(self):
        """Test that names with numbers are valid"""
        from wslaragon.services.mysql import _validate_identifier
        _validate_identifier("test123")  # Should not raise

    def test_valid_uppercase_name(self):
        """Test that uppercase names are valid"""
        from wslaragon.services.mysql import _validate_identifier
        _validate_identifier("DB_NAME")  # Should not raise

    def test_valid_mixed_case_name(self):
        """Test that mixed case names are valid"""
        from wslaragon.services.mysql import _validate_identifier
        _validate_identifier("MyDatabase")  # Should not raise

    def test_invalid_empty_name(self):
        """Test that empty names are invalid"""
        from wslaragon.services.mysql import _validate_identifier
        with pytest.raises(ValueError, match="Invalid"):
            _validate_identifier("")

    def test_invalid_name_with_semicolon(self):
        """Test that names with semicolons are rejected (SQL injection)"""
        from wslaragon.services.mysql import _validate_identifier
        with pytest.raises(ValueError, match="Invalid"):
            _validate_identifier("my;db")

    def test_invalid_name_with_single_quote(self):
        """Test that names with single quotes are rejected"""
        from wslaragon.services.mysql import _validate_identifier
        with pytest.raises(ValueError, match="Invalid"):
            _validate_identifier("my'db")

    def test_invalid_name_with_space(self):
        """Test that names with spaces are rejected"""
        from wslaragon.services.mysql import _validate_identifier
        with pytest.raises(ValueError, match="Invalid"):
            _validate_identifier("my db")

    def test_invalid_name_with_dash(self):
        """Test that names with dashes are rejected"""
        from wslaragon.services.mysql import _validate_identifier
        with pytest.raises(ValueError, match="Invalid"):
            _validate_identifier("my-db")

    def test_invalid_sql_injection_attempt(self):
        """Test that SQL injection attempts are rejected"""
        from wslaragon.services.mysql import _validate_identifier
        with pytest.raises(ValueError, match="Invalid"):
            _validate_identifier("DROP TABLE users")

    def test_invalid_name_with_null_byte(self):
        """Test that names with null bytes are rejected"""
        from wslaragon.services.mysql import _validate_identifier
        with pytest.raises(ValueError, match="Invalid"):
            _validate_identifier("my\0db")

    def test_invalid_comment_injection(self):
        """Test that names with SQL comments are rejected"""
        from wslaragon.services.mysql import _validate_identifier
        with pytest.raises(ValueError, match="Invalid"):
            _validate_identifier("db; DROP TABLE--")

    def test_custom_field_name_in_error(self):
        """Test that custom field name appears in error message"""
        from wslaragon.services.mysql import _validate_identifier
        with pytest.raises(ValueError, match="database name"):
            _validate_identifier("bad;name", "database name")


class TestMySQLManagerInit:
    """Test suite for MySQLManager.__init__"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    def test_init_sets_config(self, mysql_manager):
        """Test that init sets config attribute"""
        assert mysql_manager.config is not None

    def test_init_sets_config_file(self, mysql_manager):
        """Test that init sets mysql_config_file"""
        assert mysql_manager.mysql_config_file is not None

    def test_init_sets_default_user(self, mysql_manager):
        """Test that init sets default_user from config"""
        assert mysql_manager.default_user == "root"

    def test_init_sets_default_password(self, mysql_manager):
        """Test that init sets default_password from config"""
        assert mysql_manager.default_password == "test_password"


class TestMySQLManagerIsRunning:
    """Test suite for is_running method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_is_running_returns_true_when_active(self, mock_run, mysql_manager):
        """Test is_running returns True when MySQL is active"""
        mock_result = MagicMock()
        mock_result.stdout = "active\n"
        mock_run.return_value = mock_result

        result = mysql_manager.is_running()
        
        assert result is True
        mock_run.assert_called_once_with(
            ['systemctl', 'is-active', 'mysql'],
            capture_output=True, text=True
        )

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_is_running_returns_false_when_inactive(self, mock_run, mysql_manager):
        """Test is_running returns False when MySQL is inactive"""
        mock_result = MagicMock()
        mock_result.stdout = "inactive\n"
        mock_run.return_value = mock_result

        result = mysql_manager.is_running()
        
        assert result is False

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_is_running_returns_false_on_filnotfound(self, mock_run, mysql_manager):
        """Test is_running returns False when systemctl not found"""
        mock_run.side_effect = FileNotFoundError("systemctl not found")

        result = mysql_manager.is_running()
        
        assert result is False

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_is_running_returns_false_on_exception(self, mock_run, mysql_manager):
        """Test is_running returns False on general exception"""
        mock_run.side_effect = Exception("Unexpected error")

        result = mysql_manager.is_running()
        
        assert result is False


class TestMySQLManagerStart:
    """Test suite for start method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_start_returns_true_on_success(self, mock_run, mysql_manager):
        """Test start returns True on successful start"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = mysql_manager.start()
        
        assert result is True
        mock_run.assert_called()

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_start_returns_false_on_failure(self, mock_run, mysql_manager):
        """Test start returns False on failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Failed to start"
        mock_run.return_value = mock_result

        result = mysql_manager.start()
        
        assert result is False

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_start_returns_false_on_exception(self, mock_run, mysql_manager):
        """Test start returns False on exception"""
        mock_run.side_effect = Exception("Error")

        result = mysql_manager.start()
        
        assert result is False


class TestMySQLManagerStop:
    """Test suite for stop method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_stop_returns_true_on_success(self, mock_run, mysql_manager):
        """Test stop returns True on successful stop"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = mysql_manager.stop()
        
        assert result is True

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_stop_returns_false_on_failure(self, mock_run, mysql_manager):
        """Test stop returns False on failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = mysql_manager.stop()
        
        assert result is False

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_stop_returns_false_on_exception(self, mock_run, mysql_manager):
        """Test stop returns False on exception"""
        mock_run.side_effect = Exception("Error")

        result = mysql_manager.stop()
        
        assert result is False


class TestMySQLManagerRestart:
    """Test suite for restart method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_restart_returns_true_on_success(self, mock_run, mysql_manager):
        """Test restart returns True on successful restart"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = mysql_manager.restart()
        
        assert result is True

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_restart_returns_false_on_failure(self, mock_run, mysql_manager):
        """Test restart returns False on failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = mysql_manager.restart()
        
        assert result is False

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_restart_returns_false_on_exception(self, mock_run, mysql_manager):
        """Test restart returns False on exception"""
        mock_run.side_effect = Exception("Error")

        result = mysql_manager.restart()
        
        assert result is False


class TestMySQLManagerGetConnection:
    """Test suite for get_connection method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_connection_returns_connection(self, mock_connect, mysql_manager):
        """Test get_connection returns a connection"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        result = mysql_manager.get_connection()
        
        assert result is mock_conn
        mock_connect.assert_called_once()

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_connection_uses_default_credentials(self, mock_connect, mysql_manager):
        """Test get_connection uses default credentials"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mysql_manager.get_connection()
        
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['user'] == 'root'
        assert call_kwargs['password'] == 'test_password'

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_connection_accepts_custom_user(self, mock_connect, mysql_manager):
        """Test get_connection accepts custom user"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mysql_manager.get_connection(user='customuser')
        
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['user'] == 'customuser'

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_connection_accepts_custom_password(self, mock_connect, mysql_manager):
        """Test get_connection accepts custom password"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mysql_manager.get_connection(password='custompass')
        
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['password'] == 'custompass'

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_connection_accepts_database(self, mock_connect, mysql_manager):
        """Test get_connection accepts database parameter"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mysql_manager.get_connection(database='mydb')
        
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['database'] == 'mydb'

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_connection_returns_none_on_error(self, mock_connect, mysql_manager):
        """Test get_connection returns None on pymysql.Error"""
        import pymysql
        mock_connect.side_effect = pymysql.Error("Connection failed")

        result = mysql_manager.get_connection()
        
        assert result is None

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_connection_returns_none_on_exception(self, mock_connect, mysql_manager):
        """Test get_connection returns None on general exception"""
        mock_connect.side_effect = Exception("Unexpected error")

        result = mysql_manager.get_connection()
        
        assert result is None


class TestMySQLManagerGetVersion:
    """Test suite for get_version method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_version_returns_version(self, mock_connect, mysql_manager):
        """Test get_version returns version string"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.fetchone.return_value = {'VERSION()': '10.6.12-MariaDB'}

        result = mysql_manager.get_version()
        
        assert result == '10.6.12-MariaDB'

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_version_returns_none_on_null_result(self, mock_connect, mysql_manager):
        """Test get_version returns None when query returns None"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.fetchone.return_value = None

        result = mysql_manager.get_version()
        
        assert result is None

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_version_returns_none_on_error(self, mock_connect, mysql_manager):
        """Test get_version returns None on connection error"""
        mock_connect.return_value = None

        result = mysql_manager.get_version()
        
        assert result is None

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_version_returns_none_on_exception(self, mock_connect, mysql_manager):
        """Test get_version returns None on general exception"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Query error")

        result = mysql_manager.get_version()
        
        assert result is None


class TestMySQLManagerListDatabases:
    """Test suite for list_databases method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_list_databases_returns_user_databases(self, mock_connect, mysql_manager):
        """Test list_databases returns only user databases"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.fetchall.return_value = [
            {'Database': 'mydb'},
            {'Database': 'testdb'},
            {'Database': 'information_schema'},
            {'Database': 'mysql'},
        ]

        result = mysql_manager.list_databases()
        
        assert 'mydb' in result
        assert 'testdb' in result
        assert 'information_schema' not in result
        assert 'mysql' not in result

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_list_databases_returns_empty_on_error(self, mock_connect, mysql_manager):
        """Test list_databases returns empty list on error"""
        mock_connect.return_value = None

        result = mysql_manager.list_databases()
        
        assert result == []

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_list_databases_returns_empty_on_exception(self, mock_connect, mysql_manager):
        """Test list_databases returns empty list on general exception"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Query error")

        result = mysql_manager.list_databases()
        
        assert result == []


class TestMySQLManagerCreateDatabase:
    """Test suite for create_database method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    def test_create_database_rejects_empty_name(self, mysql_manager):
        """Test create_database rejects empty name"""
        result, error = mysql_manager.create_database("")
        
        assert result is False
        assert "Invalid" in error

    def test_create_database_rejects_sql_injection(self, mysql_manager):
        """Test create_database rejects SQL injection attempts"""
        result, error = mysql_manager.create_database("db; DROP TABLE users--")
        
        assert result is False
        assert "Invalid" in error

    def test_create_database_rejects_name_with_space(self, mysql_manager):
        """Test create_database rejects names with spaces"""
        result, error = mysql_manager.create_database("my db")
        
        assert result is False
        assert "Invalid" in error

    def test_create_database_rejects_invalid_charset(self, mysql_manager):
        """Test create_database rejects invalid charset"""
        result, error = mysql_manager.create_database("mydb", charset="utf8mb4; DROP TABLE")
        
        assert result is False
        assert "charset" in error

    def test_create_database_rejects_invalid_collation(self, mysql_manager):
        """Test create_database rejects invalid collation"""
        result, error = mysql_manager.create_database("mydb", collation="hack")
        
        assert result is False
        assert "collation" in error

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_create_database_success(self, mock_connect, mysql_manager):
        """Test create_database succeeds with valid input"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)

        result, error = mysql_manager.create_database("mydb")
        
        assert result is True
        assert error is None
        mock_cursor.execute.assert_called()

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_create_database_with_valid_charset(self, mock_connect, mysql_manager):
        """Test create_database accepts valid charset"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)

        result, error = mysql_manager.create_database("mydb", charset="utf8", collation="utf8_general_ci")
        
        assert result is True

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_create_database_returns_none_on_no_connection(self, mock_connect, mysql_manager):
        """Test create_database returns error when no connection"""
        mock_connect.return_value = None

        result, error = mysql_manager.create_database("mydb")
        
        assert result is False
        assert "connection" in error

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_create_database_handles_pymysql_error(self, mock_connect, mysql_manager):
        """Test create_database handles pymysql errors"""
        import pymysql
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = pymysql.Error("DB error")

        result, error = mysql_manager.create_database("mydb")
        
        assert result is False
        assert error is not None

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_create_database_handles_general_exception(self, mock_connect, mysql_manager):
        """Test create_database handles general exceptions"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Unexpected error")

        result, error = mysql_manager.create_database("mydb")
        
        assert result is False
        assert error is not None


class TestMySQLManagerDropDatabase:
    """Test suite for drop_database method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    def test_drop_database_rejects_invalid_name(self, mysql_manager):
        """Test drop_database rejects invalid names"""
        result = mysql_manager.drop_database("db; DROP")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_drop_database_success(self, mock_connect, mysql_manager):
        """Test drop_database succeeds with valid input"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)

        result = mysql_manager.drop_database("mydb")
        
        assert result is True
        mock_cursor.execute.assert_called()

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_drop_database_returns_false_on_error(self, mock_connect, mysql_manager):
        """Test drop_database returns False on error"""
        mock_connect.return_value = None

        result = mysql_manager.drop_database("mydb")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_drop_database_returns_false_on_exception(self, mock_connect, mysql_manager):
        """Test drop_database returns False on general exception"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Query error")

        result = mysql_manager.drop_database("mydb")
        
        assert result is False


class TestMySQLManagerDatabaseExists:
    """Test suite for database_exists method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    def test_database_exists_rejects_invalid_name(self, mysql_manager):
        """Test database_exists rejects invalid names"""
        result = mysql_manager.database_exists("db; DROP")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_database_exists_returns_true(self, mock_connect, mysql_manager):
        """Test database_exists returns True when database exists"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.fetchone.return_value = {'SCHEMA_NAME': 'mydb'}

        result = mysql_manager.database_exists("mydb")
        
        assert result is True

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_database_exists_returns_false(self, mock_connect, mysql_manager):
        """Test database_exists returns False when database doesn't exist"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.fetchone.return_value = None

        result = mysql_manager.database_exists("nonexistent")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_database_exists_returns_false_on_exception(self, mock_connect, mysql_manager):
        """Test database_exists returns False on exception"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Query error")

        result = mysql_manager.database_exists("mydb")
        
        assert result is False


class TestMySQLManagerListUsers:
    """Test suite for list_users method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_list_users_returns_users(self, mock_connect, mysql_manager):
        """Test list_users returns user list"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.fetchall.return_value = [
            {'User': 'root', 'Host': 'localhost'},
            {'User': 'testuser', 'Host': '%'},
        ]

        result = mysql_manager.list_users()
        
        assert len(result) == 2
        assert result[0]['User'] == 'root'

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_list_users_returns_empty_on_error(self, mock_connect, mysql_manager):
        """Test list_users returns empty list on error"""
        mock_connect.return_value = None

        result = mysql_manager.list_users()
        
        assert result == []

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_list_users_returns_empty_on_exception(self, mock_connect, mysql_manager):
        """Test list_users returns empty list on general exception"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Query error")

        result = mysql_manager.list_users()
        
        assert result == []


class TestMySQLManagerCreateUser:
    """Test suite for create_user method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    def test_create_user_rejects_invalid_username(self, mysql_manager):
        """Test create_user rejects invalid username"""
        result = mysql_manager.create_user("user; DROP", "password")
        
        assert result is False

    def test_create_user_rejects_invalid_host(self, mysql_manager):
        """Test create_user rejects invalid host pattern"""
        result = mysql_manager.create_user("testuser", "password", host="host; DROP")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_create_user_success(self, mock_connect, mysql_manager):
        """Test create_user succeeds with valid input"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)

        result = mysql_manager.create_user("testuser", "password123")
        
        assert result is True
        mock_cursor.execute.assert_called()

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_create_user_with_custom_host(self, mock_connect, mysql_manager):
        """Test create_user accepts custom host"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)

        result = mysql_manager.create_user("testuser", "password123", host="%")
        
        assert result is True

    def test_create_user_rejects_empty_host(self, mysql_manager):
        """Test create_user rejects empty host"""
        result = mysql_manager.create_user("testuser", "password123", host="")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_create_user_returns_false_on_pymysql_error(self, mock_connect, mysql_manager):
        """Test create_user returns False on pymysql error"""
        import pymysql
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = pymysql.Error("DB error")

        result = mysql_manager.create_user("testuser", "password123")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_create_user_returns_false_on_exception(self, mock_connect, mysql_manager):
        """Test create_user returns False on general exception"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Unexpected error")

        result = mysql_manager.create_user("testuser", "password123")
        
        assert result is False


class TestMySQLManagerDropUser:
    """Test suite for drop_user method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    def test_drop_user_rejects_invalid_username(self, mysql_manager):
        """Test drop_user rejects invalid username"""
        result = mysql_manager.drop_user("user; DROP")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_drop_user_success(self, mock_connect, mysql_manager):
        """Test drop_user succeeds with valid input"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)

        result = mysql_manager.drop_user("testuser")
        
        assert result is True

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_drop_user_returns_false_on_no_connection(self, mock_connect, mysql_manager):
        """Test drop_user returns False when no connection"""
        mock_connect.return_value = None

        result = mysql_manager.drop_user("testuser")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_drop_user_returns_false_on_exception(self, mock_connect, mysql_manager):
        """Test drop_user returns False on general exception"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Query error")

        result = mysql_manager.drop_user("testuser")
        
        assert result is False


class TestMySQLManagerGrantPrivileges:
    """Test suite for grant_privileges method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    def test_grant_privileges_rejects_invalid_database(self, mysql_manager):
        """Test grant_privileges rejects invalid database name"""
        result = mysql_manager.grant_privileges("db; DROP", "user")
        
        assert result is False

    def test_grant_privileges_rejects_invalid_username(self, mysql_manager):
        """Test grant_privileges rejects invalid username"""
        result = mysql_manager.grant_privileges("mydb", "user; DROP")
        
        assert result is False

    def test_grant_privileges_rejects_invalid_privilege(self, mysql_manager):
        """Test grant_privileges rejects invalid privilege string"""
        result = mysql_manager.grant_privileges("mydb", "user", privileges="DROP ALL TABLES")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_grant_privileges_success(self, mock_connect, mysql_manager):
        """Test grant_privileges succeeds with valid input"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)

        result = mysql_manager.grant_privileges("mydb", "user")
        
        assert result is True
        mock_cursor.execute.assert_called()

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_grant_privileges_accepts_valid_privileges(self, mock_connect, mysql_manager):
        """Test grant_privileges accepts valid privilege strings"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)

        result = mysql_manager.grant_privileges("mydb", "user", privileges="SELECT, INSERT")
        
        assert result is True

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_grant_privileges_returns_false_on_no_connection(self, mock_connect, mysql_manager):
        """Test grant_privileges returns False when no connection"""
        mock_connect.return_value = None

        result = mysql_manager.grant_privileges("mydb", "user")
        
        assert result is False

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_grant_privileges_returns_false_on_exception(self, mock_connect, mysql_manager):
        """Test grant_privileges returns False on general exception"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Query error")

        result = mysql_manager.grant_privileges("mydb", "user")
        
        assert result is False


class TestMySQLManagerGetDatabaseSize:
    """Test suite for get_database_size method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    def test_get_database_size_rejects_invalid_name(self, mysql_manager):
        """Test get_database_size rejects invalid name"""
        result = mysql_manager.get_database_size("db; DROP")
        
        assert result is None

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_database_size_returns_size(self, mock_connect, mysql_manager):
        """Test get_database_size returns formatted size"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.fetchone.return_value = {'size_mb': 1.5}

        result = mysql_manager.get_database_size("mydb")
        
        assert result == "1.5 MB"

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_database_size_returns_zero(self, mock_connect, mysql_manager):
        """Test get_database_size returns 0 MB for empty database"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.fetchone.return_value = {'size_mb': None}

        result = mysql_manager.get_database_size("mydb")
        
        assert result == "0 MB"

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_database_size_returns_none_on_error(self, mock_connect, mysql_manager):
        """Test get_database_size returns None on error"""
        mock_connect.return_value = None

        result = mysql_manager.get_database_size("mydb")
        
        assert result is None

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_database_size_returns_none_on_exception(self, mock_connect, mysql_manager):
        """Test get_database_size returns None on general exception"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Query error")

        result = mysql_manager.get_database_size("mydb")
        
        assert result is None


class TestMySQLManagerGetDatabaseTables:
    """Test suite for get_database_tables method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    def test_get_database_tables_rejects_invalid_name(self, mysql_manager):
        """Test get_database_tables rejects invalid name"""
        result = mysql_manager.get_database_tables("db; DROP")
        
        assert result == []

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_database_tables_returns_tables(self, mock_connect, mysql_manager):
        """Test get_database_tables returns table list"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.fetchall.return_value = [
            {'Name': 'users', 'Engine': 'InnoDB'},
            {'Name': 'posts', 'Engine': 'InnoDB'},
        ]

        result = mysql_manager.get_database_tables("mydb")
        
        assert len(result) == 2

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_database_tables_returns_empty_on_error(self, mock_connect, mysql_manager):
        """Test get_database_tables returns empty list on error"""
        mock_connect.return_value = None

        result = mysql_manager.get_database_tables("mydb")
        
        assert result == []

    @patch('wslaragon.services.mysql.pymysql.connect')
    def test_get_database_tables_returns_empty_on_exception(self, mock_connect, mysql_manager):
        """Test get_database_tables returns empty list on general exception"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.execute.side_effect = Exception("Query error")

        result = mysql_manager.get_database_tables("mydb")
        
        assert result == []


class TestMySQLManagerBackupDatabase:
    """Test suite for backup_database method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    def test_backup_database_rejects_invalid_name(self, mysql_manager):
        """Test backup_database rejects invalid name"""
        result = mysql_manager.backup_database("db; DROP", "/tmp/backup.sql")
        
        assert result is False

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_backup_database_success(self, mock_run, mysql_manager):
        """Test backup_database success"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = mysql_manager.backup_database("mydb", "/tmp/backup.sql")
        
        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert 'mysqldump' in call_args[0][0]
        assert 'MYSQL_PWD' in call_args[1]['env']

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_backup_database_sets_mysql_pwd_env(self, mock_run, mysql_manager):
        """Test backup_database sets MYSQL_PWD environment variable"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        mysql_manager.backup_database("mydb", "/tmp/backup.sql")
        
        call_kwargs = mock_run.call_args[1]
        assert 'MYSQL_PWD' in call_kwargs['env']
        assert call_kwargs['env']['MYSQL_PWD'] == 'test_password'

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_backup_database_returns_false_on_failure(self, mock_run, mysql_manager):
        """Test backup_database returns False on mysqldump failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error"
        mock_run.return_value = mock_result

        result = mysql_manager.backup_database("mydb", "/tmp/backup.sql")
        
        assert result is False

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_backup_database_returns_false_on_exception(self, mock_run, mysql_manager):
        """Test backup_database returns False on general exception"""
        mock_run.side_effect = Exception("Unexpected error")

        result = mysql_manager.backup_database("mydb", "/tmp/backup.sql")
        
        assert result is False


class TestMySQLManagerRestoreDatabase:
    """Test suite for restore_database method"""

    @pytest.fixture
    def mysql_manager(self, mock_config):
        from wslaragon.services.mysql import MySQLManager
        return MySQLManager(mock_config)

    @patch('builtins.open', create=True)
    def test_restore_database_rejects_invalid_name(self, mock_open, mysql_manager, tmp_path):
        """Test restore_database rejects invalid name"""
        backup_file = tmp_path / "backup.sql"
        backup_file.write_text("-- backup")
        
        result = mysql_manager.restore_database("db; DROP", str(backup_file))
        
        assert result is False

    def test_restore_database_rejects_missing_file(self, mysql_manager):
        """Test restore_database rejects missing backup file"""
        result = mysql_manager.restore_database("mydb", "/nonexistent/backup.sql")
        
        assert result is False

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_restore_database_success(self, mock_run, mysql_manager, tmp_path):
        """Test restore_database success"""
        backup_file = tmp_path / "backup.sql"
        backup_file.write_text("-- backup content")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = mysql_manager.restore_database("mydb", str(backup_file))
        
        assert result is True
        mock_run.assert_called_once()

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_restore_database_sets_mysql_pwd_env(self, mock_run, mysql_manager, tmp_path):
        """Test restore_database sets MYSQL_PWD environment variable"""
        backup_file = tmp_path / "backup.sql"
        backup_file.write_text("-- backup content")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        mysql_manager.restore_database("mydb", str(backup_file))
        
        call_kwargs = mock_run.call_args[1]
        assert 'MYSQL_PWD' in call_kwargs['env']
        assert call_kwargs['env']['MYSQL_PWD'] == 'test_password'

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_restore_database_returns_false_on_failure(self, mock_run, mysql_manager, tmp_path):
        """Test restore_database returns False on mysql failure"""
        backup_file = tmp_path / "backup.sql"
        backup_file.write_text("-- backup content")
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error"
        mock_run.return_value = mock_result

        result = mysql_manager.restore_database("mydb", str(backup_file))
        
        assert result is False

    @patch('wslaragon.services.mysql.subprocess.run')
    def test_restore_database_returns_false_on_exception(self, mock_run, mysql_manager, tmp_path):
        """Test restore_database returns False on general exception"""
        backup_file = tmp_path / "backup.sql"
        backup_file.write_text("-- backup content")
        
        mock_run.side_effect = Exception("Unexpected error")

        result = mysql_manager.restore_database("mydb", str(backup_file))
        
        assert result is False