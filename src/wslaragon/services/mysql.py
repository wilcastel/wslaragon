"""MySQL database manager for WSLaragon.

Handles MySQL/MariaDB operations: database creation, user management,
backups, and connection management.
"""
import logging
import os
import re
import subprocess
import tempfile
import pymysql
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Valid identifier pattern for MySQL database and user names
VALID_IDENTIFIER = re.compile(r'^[a-zA-Z0-9_]+$')


def _validate_identifier(name: str, field: str = "identifier") -> None:
    """Validate that a database/user name contains only safe characters.
    
    Raises:
        ValueError: If the name contains potentially dangerous characters.
    """
    if not name or not VALID_IDENTIFIER.match(name):
        raise ValueError(
            f"Invalid {field}: '{name}'. "
            f"Only alphanumeric characters and underscores are allowed."
        )


class MySQLManager:
    """Manages MySQL/MariaDB databases, users, and operations."""
    
    def __init__(self, config):
        self.config = config
        self.mysql_config_file = Path(config.get('mysql.config_file'))
        self.default_user = config.get('mysql.user', 'root')
        self.default_password = config.get('mysql.password', '')
    
    def is_running(self) -> bool:
        """Check if MySQL service is running"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'mysql'],
                capture_output=True, text=True
            )
            return result.stdout.strip() == 'active'
        except FileNotFoundError:
            logger.warning("systemctl not found, cannot check MySQL status")
            return False
        except Exception as e:
            logger.error(f"Error checking MySQL status: {e}")
            return False
    
    def start(self) -> bool:
        """Start MySQL service"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', 'mysql'],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error(f"Failed to start MySQL: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error starting MySQL: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop MySQL service"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'stop', 'mysql'],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error(f"Failed to stop MySQL: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error stopping MySQL: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart MySQL service"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'mysql'],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error(f"Failed to restart MySQL: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error restarting MySQL: {e}")
            return False
    
    def get_connection(self, user: str = None, password: str = None, 
                       database: str = None) -> Optional[pymysql.Connection]:
        """Get MySQL database connection
        
        Args:
            user: MySQL user name (defaults to configured user)
            password: MySQL password (defaults to configured password)
            database: Database name to connect to (optional)
            
        Returns:
            pymysql connection object or None on failure
        """
        try:
            user = user or self.default_user
            password = password or self.default_password
            
            connection = pymysql.connect(
                host='localhost',
                user=user,
                password=password,
                database=database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        except pymysql.Error as e:
            logger.error(f"MySQL connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error connecting to MySQL: {e}")
            return None
    
    def get_version(self) -> Optional[str]:
        """Get MySQL version"""
        connection = None
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    result = cursor.fetchone()
                    return result['VERSION()'] if result else None
        except Exception as e:
            logger.error(f"Error getting MySQL version: {e}")
        finally:
            if connection:
                connection.close()
        return None
    
    def list_databases(self) -> List[str]:
        """List all user databases (excludes system databases)"""
        connection = None
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("SHOW DATABASES")
                    result = cursor.fetchall()
                    system_dbs = {'information_schema', 'performance_schema', 'mysql', 'sys'}
                    return [db['Database'] for db in result if db['Database'] not in system_dbs]
        except Exception as e:
            logger.error(f"Error listing databases: {e}")
        finally:
            if connection:
                connection.close()
        return []
    
    def create_database(self, database_name: str, 
                        charset: str = 'utf8mb4', 
                        collation: str = 'utf8mb4_unicode_ci') -> Tuple[bool, Optional[str]]:
        """Create a new database
        
        Args:
            database_name: Name for the new database (alphanumeric + underscore only)
            charset: Character set (default: utf8mb4)
            collation: Collation (default: utf8mb4_unicode_ci)
            
        Returns:
            Tuple of (success, error_message)
        """
        # Validate input to prevent SQL injection
        try:
            _validate_identifier(database_name, "database name")
        except ValueError as e:
            return False, str(e)
        
        # Validate charset and collation against whitelist
        allowed_charsets = {
            'utf8mb4', 'utf8', 'latin1', 'ascii', 'binary', 'ucs2', 
            'utf16', 'utf32', 'utf8mb3'
        }
        allowed_collations = [
            c for c in [
                'utf8mb4_unicode_ci', 'utf8mb4_general_ci', 'utf8mb4_bin',
                'utf8_general_ci', 'utf8_unicode_ci', 'latin1_general_ci',
                'latin1_swedish_ci', 'ascii_general_ci', 'binary'
            ]
        ]
        
        if charset not in allowed_charsets:
            return False, f"Unsupported charset: {charset}"
        if collation not in allowed_collations:
            return False, f"Unsupported collation: {collation}"
        
        connection = None
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    # Use parameterized approach: backtick-escaped identifier
                    safe_name = database_name.replace('`', '``')
                    cursor.execute(
                        f"CREATE DATABASE IF NOT EXISTS `{safe_name}` CHARACTER SET %s COLLATE %s",
                        (charset, collation)
                    )
                    connection.commit()
                    return True, None
            return False, "Could not establish connection to MySQL"
        except pymysql.Error as e:
            logger.error(f"MySQL error creating database: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            return False, str(e)
        finally:
            if connection:
                connection.close()
    
    def drop_database(self, database_name: str) -> bool:
        """Drop a database
        
        Args:
            database_name: Name of the database to drop
            
        Returns:
            True if successful, False otherwise
        """
        try:
            _validate_identifier(database_name, "database name")
        except ValueError as e:
            logger.error(f"Invalid database name for drop: {e}")
            return False
        
        connection = None
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    safe_name = database_name.replace('`', '``')
                    cursor.execute(f"DROP DATABASE IF EXISTS `{safe_name}`")
                    connection.commit()
                    return True
        except Exception as e:
            logger.error(f"Error dropping database: {e}")
        finally:
            if connection:
                connection.close()
        return False
    
    def database_exists(self, database_name: str) -> bool:
        """Check if a database exists
        
        Args:
            database_name: Name of the database to check
            
        Returns:
            True if database exists, False otherwise
        """
        try:
            _validate_identifier(database_name, "database name")
        except ValueError:
            return False
        
        connection = None
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    # Use parameterized query - much safer than string interpolation
                    cursor.execute(
                        "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
                        (database_name,)
                    )
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            logger.error(f"Error checking database existence: {e}")
        finally:
            if connection:
                connection.close()
        return False
    
    def list_users(self) -> List[Dict]:
        """List all MySQL users"""
        connection = None
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT User, Host FROM mysql.user")
                    result = cursor.fetchall()
                    return result
        except Exception as e:
            logger.error(f"Error listing users: {e}")
        finally:
            if connection:
                connection.close()
        return []
    
    def create_user(self, username: str, password: str, 
                    host: str = 'localhost') -> bool:
        """Create a new MySQL user
        
        Args:
            username: MySQL username (alphanumeric + underscore only)
            password: User password
            host: Host pattern (default: localhost)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            _validate_identifier(username, "username")
        except ValueError as e:
            logger.error(f"Invalid username: {e}")
            return False
        
        # Validate host pattern
        if not host or not re.match(r'^[a-zA-Z0-9._%-]+$', host):
            logger.error(f"Invalid host pattern: {host}")
            return False
        
        connection = None
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    # Use parameterized query to prevent SQL injection
                    cursor.execute(
                        "CREATE USER %s@%s IDENTIFIED BY %s",
                        (username, host, password)
                    )
                    connection.commit()
                    return True
        except pymysql.Error as e:
            logger.error(f"MySQL error creating user: {e}")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
        finally:
            if connection:
                connection.close()
        return False
    
    def drop_user(self, username: str, host: str = 'localhost') -> bool:
        """Drop a MySQL user"""
        try:
            _validate_identifier(username, "username")
        except ValueError as e:
            logger.error(f"Invalid username for drop: {e}")
            return False
        
        connection = None
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DROP USER IF EXISTS %s@%s",
                        (username, host)
                    )
                    connection.commit()
                    return True
        except Exception as e:
            logger.error(f"Error dropping user: {e}")
        finally:
            if connection:
                connection.close()
        return False
    
    def grant_privileges(self, database: str, username: str, 
                          privileges: str = 'ALL PRIVILEGES',
                          host: str = 'localhost') -> bool:
        """Grant privileges to user on database
        
        Args:
            database: Database name (validated)
            username: MySQL username (validated)
            privileges: Privilege string (validated against whitelist)
            host: Host pattern
        """
        try:
            _validate_identifier(database, "database name")
            _validate_identifier(username, "username")
        except ValueError as e:
            logger.error(f"Invalid identifier for grant: {e}")
            return False
        
        # Whitelist allowed privilege strings
        allowed_privileges = {
            'ALL PRIVILEGES', 'SELECT', 'INSERT', 'UPDATE', 'DELETE',
            'CREATE', 'DROP', 'ALTER', 'INDEX', 'REFERENCES',
            'SELECT, INSERT, UPDATE, DELETE',
            'SELECT, INSERT', 'SELECT, INSERT, UPDATE',
        }
        if privileges not in allowed_privileges:
            logger.error(f"Invalid privilege string: {privileges}")
            return False
        
        connection = None
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    # Use backtick escaping for database name and parameterized for user/host
                    safe_db = database.replace('`', '``')
                    cursor.execute(
                        f"GRANT {privileges} ON `{safe_db}`.* TO %s@%s",
                        (username, host)
                    )
                    cursor.execute("FLUSH PRIVILEGES")
                    connection.commit()
                    return True
        except Exception as e:
            logger.error(f"Error granting privileges: {e}")
        finally:
            if connection:
                connection.close()
        return False
    
    def get_database_size(self, database_name: str) -> Optional[str]:
        """Get database size in MB
        
        Args:
            database_name: Name of the database (validated)
            
        Returns:
            Size string like "1.50 MB" or None
        """
        try:
            _validate_identifier(database_name, "database name")
        except ValueError:
            return None
        
        connection = None
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    # Use parameterized query instead of string interpolation
                    cursor.execute(
                        """SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS `size_mb`
                        FROM information_schema.tables
                        WHERE table_schema = %s""",
                        (database_name,)
                    )
                    result = cursor.fetchone()
                    if result and result.get('size_mb') is not None:
                        return f"{result['size_mb']} MB"
                    return "0 MB"
        except Exception as e:
            logger.error(f"Error getting database size: {e}")
        finally:
            if connection:
                connection.close()
        return None
    
    def get_database_tables(self, database_name: str) -> List[Dict]:
        """Get tables in a database"""
        try:
            _validate_identifier(database_name, "database name")
        except ValueError:
            return []
        
        connection = None
        try:
            connection = self.get_connection(database=database_name)
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("SHOW TABLE STATUS")
                    result = cursor.fetchall()
                    return result
        except Exception as e:
            logger.error(f"Error getting database tables: {e}")
        finally:
            if connection:
                connection.close()
        return []
    
    def backup_database(self, database_name: str, backup_path: str) -> bool:
        """Create database backup using mysqldump
        
        Uses MYSQL_PWD environment variable instead of command-line flag
        to avoid exposing the password in the process list.
        
        Args:
            database_name: Name of the database to backup
            backup_path: Path where the backup file will be written
            
        Returns:
            True if successful, False otherwise
        """
        try:
            _validate_identifier(database_name, "database name")
        except ValueError as e:
            logger.error(f"Invalid database name for backup: {e}")
            return False
        
        try:
            cmd = [
                'mysqldump',
                f'-u{self.default_user}',
                database_name,
                '--single-transaction',
                '--routines',
                '--triggers',
                f'--result-file={backup_path}'
            ]
            
            # Use MYSQL_PWD env var instead of -p flag to avoid
            # exposing password in process list (visible via `ps aux`)
            env = os.environ.copy()
            if self.default_password:
                env['MYSQL_PWD'] = self.default_password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"mysqldump failed: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return False
    
    def restore_database(self, database_name: str, backup_path: str) -> bool:
        """Restore database from a backup file
        
        Uses MYSQL_PWD environment variable instead of command-line flag
        and avoids shell=True by piping the file content directly.
        
        Args:
            database_name: Name of the target database
            backup_path: Path to the backup SQL file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            _validate_identifier(database_name, "database name")
        except ValueError as e:
            logger.error(f"Invalid database name for restore: {e}")
            return False
        
        # Validate backup file exists
        backup_file = Path(backup_path)
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            cmd = [
                'mysql',
                f'-u{self.default_user}',
                database_name
            ]
            
            # Use MYSQL_PWD env var instead of -p flag
            env = os.environ.copy()
            if self.default_password:
                env['MYSQL_PWD'] = self.default_password
            
            # Read file and pipe to stdin - avoids shell=True injection risk
            with open(backup_path, 'r') as f:
                result = subprocess.run(
                    cmd, 
                    stdin=f, 
                    env=env,
                    capture_output=True, 
                    text=True
                )
            
            if result.returncode != 0:
                logger.error(f"mysql restore failed: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False