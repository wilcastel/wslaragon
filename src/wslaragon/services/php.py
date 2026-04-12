import subprocess
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PHPManager:
    def __init__(self, config):
        self.config = config
        self.php_ini_path = Path(config.get('php.ini_file'))

    def _get_php_fpm_services(self) -> List[str]:
        """Find all running PHP-FPM services dynamically.

        Returns a list of service names like ['php8.1-fpm', 'php8.2-fpm'].
        """
        try:
            result = subprocess.run(
                ['systemctl', 'list-units', '--type=service','--no-legend', '--state=running'],
                capture_output=True, text=True
            )
            services = []
            for line in result.stdout.split('\n'):
                if 'php' in line and '-fpm' in line:
                    parts = line.split()
                    if parts:
                        services.append(parts[0])
            return services
        except Exception as e:
            logger.debug(f"_get_php_fpm_services failed: {e}")
            return []

    def _restart_php_fpm(self) -> bool:
        """Restart all running PHP-FPM services.

        Returns True if all restarts succeeded, False otherwise.
        """
        services = self._get_php_fpm_services()
        if not services:
            logger.debug("No PHP-FPM services found to restart")
            return True

        all_success = True
        for service in services:
            try:
                subprocess.run(
                    ['sudo', 'systemctl', 'restart', service],
                    check=True, capture_output=True, text=True
                )
            except subprocess.CalledProcessError as e:
                logger.debug(f"Failed to restart {service}: {e}")
                all_success = False
            except Exception as e:
                logger.debug(f"Error restarting {service}: {e}")
                all_success = False

        return all_success

    def _stop_php_fpm(self) -> bool:
        """Stop all running PHP-FPM services.

        Returns True if all stops succeeded, False otherwise.
        """
        services = self._get_php_fpm_services()
        if not services:
            logger.debug("No PHP-FPM services found to stop")
            return True
        all_success = True
        for service in services:
            try:
                subprocess.run(
                    ['sudo', 'systemctl', 'stop', service],
                    check=False, capture_output=True, text=True
                )
            except Exception as e:
                logger.debug(f"Error stopping {service}: {e}")
                all_success = False

        return all_success

    def get_installed_versions(self) -> List[str]:
        """Get list of installed PHP versions"""
        try:
            result = subprocess.run(
                ['dpkg', '-l'],
                capture_output=True, text=True
            )
            versions = set()
            for line in result.stdout.split('\n'):
                # Filter for installed packages (lines starting with 'ii') that contain 'php'
                if line.startswith('ii') and 'php' in line:
                    match = re.search(r'php(\d+\.\d+)', line)
                    if match:
                        versions.add(match.group(1))
            return sorted(list(versions))
        except Exception as e:
            logger.debug(f"get_installed_versions failed: {e}")
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
        except Exception as e:
            logger.debug(f"get_current_version failed: {e}")
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
                # Stop all running PHP-FPM services dynamically
                self._stop_php_fpm()
                # Start the target PHP-FPM service
                subprocess.run(['sudo', 'systemctl', 'start', fpm_service], check=True)

            return True
        except Exception as e:
            logger.debug(f"switch_version failed: {e}")
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
        except Exception as e:
            logger.debug(f"read_ini failed: {e}")
            pass
        return config
    
    def write_ini(self, config: Dict[str, str]) -> bool:
        """Write PHP configuration to php.ini"""
        try:
            # Read current file
            with open(self.php_ini_path, 'r') as f:
                lines = f.readlines()
            
            # Update configuration in memory
            updated_lines = []
            config_keys = set(config.keys())
            
            for line in lines:
                stripped = line.strip()
                # Match strict key=value pairs, ignoring comments
                if stripped and not stripped.startswith(';') and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    if key in config:
                        updated_lines.append(f"{key} = {config[key]}\n")
                        config_keys.remove(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Add new configurations that weren't found
            if config_keys:
                updated_lines.append("\n; Added by WSLaragon\n")
                for key in config_keys:
                    updated_lines.append(f"{key} = {config[key]}\n")
            
            # Write back using sudo tee
            process = subprocess.Popen(['sudo', 'tee', str(self.php_ini_path)],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     text=True)
            process.communicate(input=''.join(updated_lines))
            
            return process.returncode == 0
        except Exception as e:
            logger.debug(f"write_ini failed: {e}")
            return False

    def update_config(self, key: str, value: str) -> bool:
        """Update a specific PHP configuration directive"""
        try:
            if self.write_ini({key: value}):
                # Restart PHP-FPM to apply changes
                version = self.get_current_version()
                if version:
                    # Parse version to get major.minor
                    v_match = re.search(r'(\d+\.\d+)', version)
                    if v_match:
                        short_version = v_match.group(1)
                        fpm_service = f'php{short_version}-fpm'
                        try:
                            subprocess.run(
                                ['sudo', 'systemctl', 'restart', fpm_service],
                                check=True, capture_output=True, text=True
                            )
                            return True
                        except subprocess.CalledProcessError:
                            # Fallback: try to restart all PHP-FPM services dynamically
                            self._restart_php_fpm()
                            return True

                # Fallback if version detection fails: restart all PHP-FPM services
                self._restart_php_fpm()
                return True
            return False
        except Exception as e:
            logger.debug(f"update_config failed: {e}")
            return False
    
    def get_extensions(self) -> List[str]:
        """Get list of available PHP extensions"""
        try:
            result = subprocess.run(
                ['php', '-m'],
                capture_output=True, text=True
            )
            return [line.strip() for line in result.stdout.split('\n') if line.strip()]
        except Exception as e:
            logger.debug(f"get_extensions failed: {e}")
            return []
    
    def enable_extension(self, extension: str) -> bool:
        """Enable a PHP extension"""
        try:
            # Enable for CLI
            subprocess.run([
                'sudo', 'phpenmod', extension
            ], check=True)

            # Restart PHP-FPM services dynamically
            self._restart_php_fpm()

            return True
        except Exception as e:
            logger.debug(f"enable_extension failed: {e}")
            return False

    def disable_extension(self, extension: str) -> bool:
        """Disable a PHP extension"""
        try:
            # Disable for CLI
            subprocess.run([
                'sudo', 'phpdismod', extension
            ], check=True)

            # Restart PHP-FPM services dynamically
            self._restart_php_fpm()

            return True
        except Exception as e:
            logger.debug(f"disable_extension failed: {e}")
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
        except Exception as e:
            logger.debug(f"get_ini_directives failed: {e}")
            return {}