import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional

class PHPManager:
    def __init__(self, config):
        self.config = config
        self.php_ini_path = Path(config.get('php.ini_file'))
    
    def get_installed_versions(self) -> List[str]:
        """Get list of installed PHP versions"""
        try:
            result = subprocess.run(
                ['dpkg', '-l', '|', 'grep', '^ii', '|', 'grep', 'php'],
                shell=True, capture_output=True, text=True
            )
            versions = set()
            for line in result.stdout.split('\n'):
                match = re.search(r'php(\d+\.\d+)', line)
                if match:
                    versions.add(match.group(1))
            return sorted(list(versions))
        except Exception:
            return []
    
    def get_current_version(self) -> Optional[str]:
        """Get currently active PHP version"""
        try:
            result = subprocess.run(
                ['php', '-v'],
                capture_output=True, text=True
            )
            match = re.search(r'PHP (\d+\.\d+\.\d+)', result.stdout)
            return match.group(1) if match else None
        except Exception:
            return None
    
    def switch_version(self, version: str) -> bool:
        """Switch PHP version using update-alternatives"""
        try:
            # Switch CLI
            subprocess.run([
                'sudo', 'update-alternatives', '--set', 'php', 
                f'/usr/bin/php{version}'
            ], check=True)
            
            # Switch FPM if exists
            fpm_service = f'php{version}-fpm'
            result = subprocess.run(
                ['systemctl', 'is-active', fpm_service],
                capture_output=True, text=True
            )
            if result.stdout.strip() == 'active':
                subprocess.run(['sudo', 'systemctl', 'stop', 'php*-fpm'], check=True)
                subprocess.run(['sudo', 'systemctl', 'start', fpm_service], check=True)
            
            return True
        except Exception:
            return False
    
    def read_ini(self) -> Dict[str, str]:
        """Read PHP configuration from php.ini"""
        config = {}
        try:
            with open(self.php_ini_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(';') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        except Exception:
            pass
        return config
    
    def write_ini(self, config: Dict[str, str]) -> bool:
        """Write PHP configuration to php.ini"""
        try:
            # Read current file
            lines = []
            with open(self.php_ini_path, 'r') as f:
                lines = f.readlines()
            
            # Update configuration
            updated_lines = []
            config_keys = set(config.keys())
            
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith(';') and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    if key in config:
                        updated_lines.append(f"{key} = {config[key]}\n")
                        config_keys.remove(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Add new configurations
            for key in config_keys:
                updated_lines.append(f"{key} = {config[key]}\n")
            
            # Write back
            with open(self.php_ini_path, 'w') as f:
                f.writelines(updated_lines)
            
            return True
        except Exception:
            return False
    
    def get_extensions(self) -> List[str]:
        """Get list of available PHP extensions"""
        try:
            result = subprocess.run(
                ['php', '-m'],
                capture_output=True, text=True
            )
            return [line.strip() for line in result.stdout.split('\n') if line.strip()]
        except Exception:
            return []
    
    def enable_extension(self, extension: str) -> bool:
        """Enable a PHP extension"""
        try:
            # Enable for CLI
            subprocess.run([
                'sudo', 'phpenmod', extension
            ], check=True)
            
            # Restart PHP-FPM
            subprocess.run([
                'sudo', 'systemctl', 'restart', 'php*-fpm'
            ], check=True)
            
            return True
        except Exception:
            return False
    
    def disable_extension(self, extension: str) -> bool:
        """Disable a PHP extension"""
        try:
            # Disable for CLI
            subprocess.run([
                'sudo', 'phpdismod', extension
            ], check=True)
            
            # Restart PHP-FPM
            subprocess.run([
                'sudo', 'systemctl', 'restart', 'php*-fpm'
            ], check=True)
            
            return True
        except Exception:
            return False
    
    def get_ini_directives(self) -> Dict[str, str]:
        """Get current PHP runtime configuration"""
        try:
            result = subprocess.run(
                ['php', '-i'],
                capture_output=True, text=True
            )
            
            config = {}
            in_config = False
            
            for line in result.stdout.split('\n'):
                if 'Configuration' in line and 'php.ini' in line:
                    in_config = True
                    continue
                
                if in_config and line.strip() and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
                elif in_config and not line.strip():
                    break
            
            return config
        except Exception:
            return {}