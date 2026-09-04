import subprocess
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self, config=None):
        php_service = config.get('php.fpm_service', 'php8.3-fpm') if config else 'php8.3-fpm'
        platform = config.get('platform.name') if config else None
        redis_service = 'redis' if platform in {'arch', 'omarchy'} else 'redis-server'
        self.services = {
            'nginx': {'service': 'nginx', 'port': 80},
            'mysql': {'service': 'mariadb', 'port': 3306},
            'php-fpm': {'service': php_service, 'port': 9000},
            'redis': {'service': redis_service, 'port': 6379}
        }
        self.mysql = None
        if config:
            try:
                from ..services.mysql import MySQLManager
                self.mysql = MySQLManager(config)
                if self.mysql.backend == 'docker':
                    self.services['mysql']['service'] = f'docker:{self.mysql.container}'
            except (TypeError, ValueError):
                # Invalid/mocked configuration falls back to systemd conventions.
                self.mysql = None
    
    def is_running(self, service_name: str) -> bool:
        """Check if a service is running"""
        try:
            service = self.services.get(service_name)
            if not service:
                return False
            if service_name == 'mysql' and self.mysql:
                return self.mysql.is_running()
            
            # Check systemd service
            result = subprocess.run(
                ['systemctl', 'is-active', service['service']],
                capture_output=True, text=True
            )
            return result.stdout.strip() == 'active'
        except Exception as e:
            logger.debug(f"is_running failed: {e}")
            return False
    
    def start(self, service_name: str) -> bool:
        """Start a service"""
        try:
            service = self.services.get(service_name)
            if not service:
                return False
            if service_name == 'mysql' and self.mysql:
                return self.mysql.start()
            
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', service['service']],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"start failed: {e}")
            return False
    
    def stop(self, service_name: str) -> bool:
        """Stop a service"""
        try:
            service = self.services.get(service_name)
            if not service:
                return False
            if service_name == 'mysql' and self.mysql:
                return self.mysql.stop()
            
            result = subprocess.run(
                ['sudo', 'systemctl', 'stop', service['service']],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"stop failed: {e}")
            return False
    
    def restart(self, service_name: str) -> bool:
        """Restart a service"""
        try:
            service = self.services.get(service_name)
            if not service:
                return False
            if service_name == 'mysql' and self.mysql:
                return self.mysql.restart()
            
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', service['service']],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"restart failed: {e}")
            return False
    
    def enable(self, service_name: str) -> bool:
        """Enable service at boot"""
        try:
            service = self.services.get(service_name)
            if not service:
                return False
            if service_name == 'mysql' and self.mysql and self.mysql.backend == 'docker':
                # Docker containers are intentionally on-demand in Omarchy.
                return True
            
            result = subprocess.run(
                ['sudo', 'systemctl', 'enable', service['service']],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"enable failed: {e}")
            return False
    
    def status(self) -> Dict[str, Dict]:
        """Get status of all services"""
        status = {}
        for name, service in self.services.items():
            status[name] = {
                'running': self.is_running(name),
                'port': service['port'],
                'service': service['service']
            }
        return status
