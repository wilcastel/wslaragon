import json
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..services.ssl import SSLManager

class SiteManager:
    def __init__(self, config, nginx_manager, mysql_manager):
        self.config = config
        self.nginx = nginx_manager
        self.mysql = mysql_manager
        self.sites_dir = Path(config.get('sites.dir', str(Path.home() / ".wslaragon" / "sites")))
        self.document_root = Path(config.get('sites.document_root'))
        self.tld = config.get('sites.tld')
        self.sites_file = self.sites_dir / "sites.json"
        
        self._ensure_dirs()
        self._load_sites()
    
    def _ensure_dirs(self):
        """Ensure necessary directories exist"""
        for dir_path in [self.sites_dir, self.document_root]:
            dir_path.mkdir(exist_ok=True, parents=True)
    
    def _load_sites(self):
        """Load sites configuration from JSON file"""
        if self.sites_file.exists():
            with open(self.sites_file, 'r') as f:
                self.sites = json.load(f)
        else:
            self.sites = {}
            self._save_sites()
    
    def _save_sites(self):
        """Save sites configuration to JSON file"""
        with open(self.sites_file, 'w') as f:
            json.dump(self.sites, f, indent=2)
    
    def create_site(self, site_name: str, php: bool = True, 
                   mysql: bool = False, ssl: bool = False,
                   database_name: str = None, public_dir: bool = False,
                   proxy_port: int = None) -> Dict:
        """Create a new site"""
        try:
            # Validate site name
            if not site_name or not site_name.replace('-', '').replace('_', '').isalnum():
                return {'success': False, 'error': 'Invalid site name'}
            
            # Check if site already exists
            if site_name in self.sites:
                return {'success': False, 'error': 'Site already exists'}
            
            # Create document root (always base directory)
            site_base_dir = self.document_root / site_name
            site_base_dir.mkdir(exist_ok=True, parents=True)
            
            # Define actual Nginx web root
            web_root = site_base_dir / "public" if public_dir else site_base_dir
            if public_dir:
                web_root.mkdir(exist_ok=True)
            
            # Create index file (only if not proxying, or even if proxying just as a placeholder)
            if not proxy_port:
                index_file = web_root / "index.php"
                if php:
                    index_content = f"""<?php
echo "<h1>Welcome to {site_name}{self.tld}!</h1>";
echo "<p>PHP Version: " . phpversion() . "</p>";
echo "<p>Server Time: " . date('Y-m-d H:i:s') . "</p>";
phpinfo();
?>"""
                else:
                    index_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Welcome to {site_name}{self.tld}!</title>
</head>
<body>
    <h1>Welcome to {site_name}{self.tld}!</h1>
    <p>Static site is working!</p>
</body>
</html>"""
                
                with open(index_file, 'w') as f:
                    f.write(index_content)
            
            # Create database if requested
            db_created = False
            if mysql:
                if not database_name:
                    database_name = f"{site_name}_db"
                
                db_created, db_error = self.mysql.create_database(database_name)
                if not db_created:
                    return {'success': False, 'error': f'Failed to create database: {db_error}'}
            
            # Generate SSL certificates if requested
            if ssl:
                ssl_mgr = SSLManager(self.config)
                ssl_result = ssl_mgr.setup_ssl_for_site(site_name, self.tld)
                if not ssl_result['success']:
                    return {'success': False, 'error': f"Failed to generate SSL: {ssl_result['error']}"}

            # Create Nginx configuration
            nginx_created, nginx_error = self.nginx.add_site(
                site_name, 
                str(web_root), 
                ssl=ssl, 
                php=php,
                proxy_port=proxy_port
            )
            
            if not nginx_created:
                return {'success': False, 'error': f'Failed to create Nginx configuration: {nginx_error}'}
            
            # Add to sites registry
            site_info = {
                'name': site_name,
                'domain': f"{site_name}{self.tld}",
                'document_root': str(site_base_dir), # Base directory for management
                'web_root': str(web_root),           # Actual web root for Nginx
                'php': php,
                'mysql': mysql,
                'ssl': ssl,
                'proxy_port': proxy_port,
                'database': database_name if mysql else None,
                'created_at': datetime.now().isoformat(),
                'enabled': True
            }
            
            self.sites[site_name] = site_info
            self._save_sites()
            
            return {'success': True, 'site': site_info}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_site_root(self, site_name: str, public_dir: bool = True) -> Dict:
        """Update site document root (e.g. to point to public/)"""
        try:
            if site_name not in self.sites:
                return {'success': False, 'error': 'Site not found'}
            
            site_info = self.sites[site_name]
            base_dir = Path(site_info['document_root'])
            old_web_root = site_info.get('web_root', site_info['document_root'])
            
            new_web_root = base_dir / "public" if public_dir else base_dir
            if public_dir:
                new_web_root.mkdir(exist_ok=True)
            
            # Update Nginx config
            # We need to recreate the config completely to update root
            self.nginx.remove_site(site_name)
            
            success, error = self.nginx.add_site(
                site_name,
                str(new_web_root),
                ssl=site_info.get('ssl', False),
                php=site_info.get('php', True),
                proxy_port=site_info.get('proxy_port')
            )
            
            if not success:
                # Try to revert
                self.nginx.add_site(
                    site_name,
                    str(old_web_root),
                    ssl=site_info.get('ssl', False),
                    php=site_info.get('php', True),
                    proxy_port=site_info.get('proxy_port')
                )
                return {'success': False, 'error': f"Failed to update Nginx: {error}"}
            
            # Update registry
            site_info['web_root'] = str(new_web_root)
            self._save_sites()
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            

    
    def delete_site(self, site_name: str, remove_files: bool = False, 
                    remove_database: bool = False) -> Dict:
        """Delete a site"""
        try:
            if site_name not in self.sites:
                return {'success': False, 'error': 'Site not found'}
            
            site_info = self.sites[site_name]
            
            # Remove Nginx configuration
            self.nginx.remove_site(site_name)
            
            # Remove database if requested
            if remove_database and site_info.get('database'):
                self.mysql.drop_database(site_info['database'])
            
            # Remove files if requested
            if remove_files:
                site_doc_root = Path(site_info['document_root'])
                if site_doc_root.exists():
                    subprocess.run(['sudo', 'rm', '-rf', str(site_doc_root)], check=True)
            
            # Remove from sites registry
            del self.sites[site_name]
            self._save_sites()
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def enable_site(self, site_name: str) -> Dict:
        """Enable a site"""
        try:
            if site_name not in self.sites:
                return {'success': False, 'error': 'Site not found'}
            
            # Enable Nginx site
            if not self.nginx.enable_site(site_name):
                return {'success': False, 'error': 'Failed to enable Nginx site'}
            
            # Update site status
            self.sites[site_name]['enabled'] = True
            self._save_sites()
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def disable_site(self, site_name: str) -> Dict:
        """Disable a site"""
        try:
            if site_name not in self.sites:
                return {'success': False, 'error': 'Site not found'}
            
            # Disable Nginx site
            if not self.nginx.disable_site(site_name):
                return {'success': False, 'error': 'Failed to disable Nginx site'}
            
            # Update site status
            self.sites[site_name]['enabled'] = False
            self._save_sites()
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_sites(self) -> List[Dict]:
        """List all sites"""
        return list(self.sites.values())
    
    def get_site(self, site_name: str) -> Optional[Dict]:
        """Get site information"""
        return self.sites.get(site_name)
    
    def update_site(self, site_name: str, **kwargs) -> Dict:
        """Update site configuration"""
        try:
            if site_name not in self.sites:
                return {'success': False, 'error': 'Site not found'}
            
            site_info = self.sites[site_name]
            
            # Update allowed fields
            allowed_fields = ['php', 'mysql', 'ssl', 'database', 'proxy_port']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    site_info[field] = value
            
            # Recreate Nginx configuration if needed
            if any(field in kwargs for field in ['php', 'ssl', 'proxy_port']):
                self.nginx.remove_site(site_name)
                self.nginx.add_site(
                    site_name,
                    site_info['document_root'],
                    ssl=site_info.get('ssl', False),
                    php=site_info.get('php', True),
                    proxy_port=site_info.get('proxy_port')
                )
            
            self._save_sites()
            return {'success': True, 'site': site_info}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_site_logs(self, site_name: str) -> Dict[str, str]:
        """Get site logs"""
        try:
            if site_name not in self.sites:
                return {'error': 'Site not found'}
            
            logs = {}
            
            # Nginx access log
            access_log = f"/var/log/nginx/{site_name}.access.log"
            if Path(access_log).exists():
                with open(access_log, 'r') as f:
                    logs['access'] = f.read()[-1000:]  # Last 1000 characters
            
            # Nginx error log
            error_log = f"/var/log/nginx/{site_name}.error.log"
            if Path(error_log).exists():
                with open(error_log, 'r') as f:
                    logs['error'] = f.read()[-1000:]  # Last 1000 characters
            
            return logs
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_site_url(self, site_name: str) -> Optional[str]:
        """Get site URL"""
        if site_name in self.sites:
            protocol = 'https' if self.sites[site_name].get('ssl') else 'http'
            return f"{protocol}://{site_name}{self.tld}"
        return None

    def fix_permissions(self, site_name: str) -> Dict:
        """Fix file owner and permissions for a site"""
        try:
            if site_name not in self.sites:
                return {'success': False, 'error': 'Site not found'}
            
            site_info = self.sites[site_name]
            doc_root = site_info['document_root']
            
            # Get current user
            current_user = os.getenv('SUDO_USER') or os.getenv('USER')
            
            # Set owner to current_user:www-data
            cmd_chown = ['sudo', 'chown', '-R', f'{current_user}:www-data', doc_root]
            subprocess.run(cmd_chown, check=True, capture_output=True)
            
            # Set permissions to 775 (rwxrwxr-x)
            # User: rwx (Full)
            # Group (Web Server): rwx (Full) - Needed for writing logs, caching, storage
            # Others: r-x (Read/Execute)
            cmd_chmod = ['sudo', 'chmod', '-R', '775', doc_root]
            subprocess.run(cmd_chmod, check=True, capture_output=True)
            
            # Additional fix for storage folders commonly used in frameworks (Laravel, etc)
            # This ensures even new files created inherit the group 'www-data'
            cmd_guid = ['sudo', 'find', doc_root, '-type', 'd', '-exec', 'chmod', 'g+s', '{}', '+']
            subprocess.run(cmd_guid, check=True, capture_output=True)
            
            return {'success': True}
            
        except subprocess.CalledProcessError as e:
            return {'success': False, 'error': f"Command failed: {str(e)}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}