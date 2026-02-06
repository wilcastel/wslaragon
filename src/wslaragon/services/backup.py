import shutil
import subprocess
import json
import tarfile
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class BackupManager:
    """Manages site backups (export/import)"""
    
    def __init__(self, config, site_manager, mysql_manager, nginx_manager):
        self.config = config
        self.site_manager = site_manager
        self.mysql_manager = mysql_manager
        self.nginx_manager = nginx_manager
        self.backup_dir = Path(config.get('backup.dir', str(Path.home() / ".wslaragon" / "backups")))
        self.backup_dir.mkdir(exist_ok=True, parents=True)

    def export_site(self, site_name: str, output_path: str = None) -> Dict:
        """Export a site to a backup file"""
        try:
            site = self.site_manager.get_site(site_name)
            if not site:
                return {'success': False, 'error': 'Site not found'}

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{site_name}_{timestamp}.wslaragon"
            
            if output_path:
                target_file = Path(output_path)
                if target_file.is_dir():
                    target_file = target_file / filename
            else:
                target_file = self.backup_dir / filename

            # key elements to backup
            manifest = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'site_info': site,
                'files': {},
                'database': {}
            }
            
            # Temporary directory for building the archive
            temp_dir = Path(f"/tmp/wslaragon_backup_{site_name}_{timestamp}")
            temp_dir.mkdir(exist_ok=True)
            
            # 1. Backup Files
            doc_root = Path(site['document_root'])
            if doc_root.exists():
                shutil.make_archive(str(temp_dir / "files"), 'gztar', doc_root)
                manifest['files']['archive'] = "files.tar.gz"
            
            # 2. Backup Database
            if site.get('mysql') and site.get('database'):
                db_name = site.get('database')
                dump_file = temp_dir / "database.sql"
                # Use mysqldump
                # Note: Assuming sudo or passwordless access for root configured in my.cnf or via sudo
                subprocess.run(['sudo', 'mysqldump', db_name], 
                             stdout=open(dump_file, 'w'), 
                             check=True)
                manifest['database']['dump'] = "database.sql"
                manifest['database']['name'] = db_name

            # 3. Save Manifest
            with open(temp_dir / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)

            # 4. Create Final Archive (tar.gz named .wslaragon)
            with tarfile.open(target_file, "w:gz") as tar:
                tar.add(temp_dir / "manifest.json", arcname="manifest.json")
                if (temp_dir / "files.tar.gz").exists():
                    tar.add(temp_dir / "files.tar.gz", arcname="files.tar.gz")
                if (temp_dir / "database.sql").exists():
                    tar.add(temp_dir / "database.sql", arcname="database.sql")

            # Cleanup
            shutil.rmtree(temp_dir)
            
            return {
                'success': True, 
                'file': str(target_file),
                'site': site_name
            }

        except Exception as e:
            # Cleanup on failure
            if 'temp_dir' in locals() and temp_dir.exists():
                shutil.rmtree(temp_dir)
            return {'success': False, 'error': str(e)}

    def import_site(self, backup_file: str, new_name: str = None) -> Dict:
        """Import a site from a backup file"""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                 return {'success': False, 'error': 'Backup file not found'}

            # Temporary extraction
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_dir = Path(f"/tmp/wslaragon_import_{timestamp}")
            temp_dir.mkdir(exist_ok=True)
            
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=temp_dir)
            
            if not (temp_dir / "manifest.json").exists():
                 return {'success': False, 'error': 'Invalid backup: manifest.json missing'}

            with open(temp_dir / "manifest.json", 'r') as f:
                manifest = json.load(f)
            
            original_site = manifest['site_info']
            site_name = new_name or original_site['name']
            
            # Check if site exists
            if self.site_manager.get_site(site_name):
                 return {'success': False, 'error': f"Site '{site_name}' already exists. Delete it first or choose a different name."}

            # 1. Prepare Environment (Create site structure)
            # We use site_manager to create the base structure and Nginx config
            # We preserve the original settings (php, ssl, etc)
            
            create_result = self.site_manager.create_site(
                site_name,
                php=original_site.get('php', True),
                mysql=original_site.get('mysql', False),
                ssl=original_site.get('ssl', False),
                proxy_port=original_site.get('proxy_port'),
                site_type='html', # Dummy type, we will overwrite files
                db_type=original_site.get('db_type'),
                database_name=original_site.get('database') if not new_name else f"{site_name}_db"
            )
            
            if not create_result['success']:
                 return {'success': False, 'error': f"Failed to create site structure: {create_result['error']}"}
            
            new_site_info = create_result['site']
            
            # 2. Restore Files
            if "archive" in manifest.get('files', {}):
                archive_path = temp_dir / manifest['files']['archive']
                doc_root = Path(new_site_info['document_root'])
                
                # Clear dummy files created by create_site
                subprocess.run(['sudo', 'rm', '-rf', f"{str(doc_root)}/*"], check=True)
                
                # unpack
                shutil.unpack_archive(str(archive_path), str(doc_root), 'gztar')
                
                # Fix permissions
                self.site_manager.fix_permissions(site_name)

            # 3. Restore Database
            if "dump" in manifest.get('database', {}) and new_site_info.get('database'):
                dump_path = temp_dir / manifest['database']['dump']
                db_name = new_site_info['database']
                
                with open(dump_path, 'r') as f:
                     subprocess.run(['sudo', 'mysql', db_name], stdin=f, check=True)
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            return {
                'success': True,
                'site': site_name,
                'info': new_site_info
            }

        except Exception as e:
            if 'temp_dir' in locals() and temp_dir.exists():
                shutil.rmtree(temp_dir)
            return {'success': False, 'error': str(e)}
