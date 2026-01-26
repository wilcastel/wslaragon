import json
import subprocess
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
                   database_name: str = None) -> Dict:
        """Create a new site"""
        try:
            # Validate site name
            if not site_name or not site_name.replace('-', '').replace('_', '').isalnum():
                return {'success': False, 'error': 'Invalid site name'}
            
            # Check if site already exists
            if site_name in self.sites:
                return {'success': False, 'error': 'Site already exists'}
            
            # Create document root
            site_doc_root = self.document_root / site_name
            site_doc_root.mkdir(exist_ok=True, parents=True)
            
            # Create index file
            index_file = site_doc_root / "index.php"
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
                str(site_doc_root), 
                ssl=ssl, 
                php=php
            )
            
            if not nginx_created:
                return {'success': False, 'error': f'Failed to create Nginx configuration: {nginx_error}'}
            
            # Add to sites registry
            site_info = {
                'name': site_name,
                'domain': f"{site_name}{self.tld}",
                'document_root': str(site_doc_root),
                'php': php,
                'mysql': mysql,
                'ssl': ssl,
                'database': database_name if mysql else None,
                'created_at': datetime.now().isoformat(),
                'enabled': True
            }
            
            self.sites[site_name] = site_info
            self._save_sites()
            
            return {'success': True, 'site': site_info}
            
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
            allowed_fields = ['php', 'mysql', 'ssl', 'database']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    site_info[field] = value
            
            # Recreate Nginx configuration if needed
            if any(field in kwargs for field in ['php', 'ssl']):
                self.nginx.remove_site(site_name)
                self.nginx.add_site(
                    site_name,
                    site_info['document_root'],
                    ssl=site_info.get('ssl', False),
                    php=site_info.get('php', True)
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