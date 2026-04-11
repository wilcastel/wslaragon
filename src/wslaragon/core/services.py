import subprocess
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.services = {
            'nginx': {'service': 'nginx', 'port': 80},
            'mysql': {'service': 'mariadb', 'port': 3306},
            'php-fpm': {'service': 'php8.3-fpm', 'port': 9000},
            'redis': {'service': 'redis-server', 'port': 6379}
        }
    
    def is_running(self, service_name: str) -> bool:
        """Check if a service is running"""
        try:
            service = self.services.get(service_name)
            if not service:
                return False
            
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