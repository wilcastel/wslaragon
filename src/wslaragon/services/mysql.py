import subprocess
import pymysql
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class MySQLManager:
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
        except Exception:
            return False
    
    def start(self) -> bool:
        """Start MySQL service"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', 'mysql'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def stop(self) -> bool:
        """Stop MySQL service"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'stop', 'mysql'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def restart(self) -> bool:
        """Restart MySQL service"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'mysql'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_connection(self, user: str = None, password: str = None, 
                      database: str = None) -> Optional[pymysql.Connection]:
        """Get MySQL database connection"""
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
        except Exception as e:
            raise e
    
    def get_version(self) -> Optional[str]:
        """Get MySQL version"""
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    result = cursor.fetchone()
                    connection.close()
                    return result['VERSION()'] if result else None
        except Exception:
            pass
        return None
    
    def list_databases(self) -> List[str]:
        """List all databases"""
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("SHOW DATABASES")
                    result = cursor.fetchall()
                    connection.close()
                    return [db['Database'] for db in result if db['Database'] not in ['information_schema', 'performance_schema', 'mysql', 'sys']]
        except Exception:
            pass
        return []
    
    def create_database(self, database_name: str, 
                       charset: str = 'utf8mb4', 
                       collation: str = 'utf8mb4_unicode_ci') -> Tuple[bool, Optional[str]]:
        """Create a new database"""
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET {charset} COLLATE {collation}")
                    connection.commit()
                    connection.close()
                    return True, None
            return False, "Could not establish connection to MySQL"
        except Exception as e:
            return False, str(e)
    
    def drop_database(self, database_name: str) -> bool:
        """Drop a database"""
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"DROP DATABASE IF EXISTS `{database_name}`")
                    connection.commit()
                    connection.close()
                    return True
        except Exception:
            pass
        return False
    
    def list_users(self) -> List[Dict]:
        """List all MySQL users"""
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT User, Host FROM mysql.user")
                    result = cursor.fetchall()
                    connection.close()
                    return result
        except Exception:
            pass
        return []
    
    def create_user(self, username: str, password: str, 
                    host: str = 'localhost') -> bool:
        """Create a new MySQL user"""
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}'")
                    connection.commit()
                    connection.close()
                    return True
        except Exception:
            pass
        return False
    
    def drop_user(self, username: str, host: str = 'localhost') -> bool:
        """Drop a MySQL user"""
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"DROP USER IF EXISTS '{username}'@'{host}'")
                    connection.commit()
                    connection.close()
                    return True
        except Exception:
            pass
        return False
    
    def grant_privileges(self, database: str, username: str, 
                         privileges: str = 'ALL PRIVILEGES',
                         host: str = 'localhost') -> bool:
        """Grant privileges to user on database"""
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"GRANT {privileges} ON `{database}`.* TO '{username}'@'{host}'")
                    cursor.execute("FLUSH PRIVILEGES")
                    connection.commit()
                    connection.close()
                    return True
        except Exception:
            pass
        return False
    
    def get_database_size(self, database_name: str) -> Optional[str]:
        """Get database size"""
        try:
            connection = self.get_connection()
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
                        FROM information_schema.tables
                        WHERE table_schema = '{database_name}'
                    """)
                    result = cursor.fetchone()
                    connection.close()
                    return f"{result['Size (MB)']} MB" if result and result['Size (MB)'] else "0 MB"
        except Exception:
            pass
        return None
    
    def get_database_tables(self, database_name: str) -> List[Dict]:
        """Get tables in a database"""
        try:
            connection = self.get_connection(database=database_name)
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("SHOW TABLE STATUS")
                    result = cursor.fetchall()
                    connection.close()
                    return result
        except Exception:
            pass
        return []
    
    def backup_database(self, database_name: str, backup_path: str) -> bool:
        """Create database backup using mysqldump"""
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
            
            if self.default_password:
                cmd.append(f'-p{self.default_password}')
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def restore_database(self, database_name: str, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            cmd = [
                'mysql',
                f'-u{self.default_user}',
                database_name,
                f'< {backup_path}'
            ]
            
            if self.default_password:
                cmd.insert(1, f'-p{self.default_password}')
            
            result = subprocess.run(' '.join(cmd), shell=True, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False