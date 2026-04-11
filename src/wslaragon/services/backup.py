"""Site backup and restore manager for WSLaragon.

Handles export/import of complete site backups including files, database,
and Nginx configuration.
"""
import logging
import shutil
import subprocess
import json
import os
import tarfile
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Valid site name pattern (for security)
VALID_SITE_NAME = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$')


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
        """Export a site to a backup file
        
        Args:
            site_name: Name of the site to export
            output_path: Optional directory or file path for the backup
            
        Returns:
            Dict with 'success', 'file', and 'site' keys
        """
        # Validate site name
        if not site_name or not VALID_SITE_NAME.match(site_name):
            return {'success': False, 'error': f'Invalid site name: {site_name}'}
        
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

            # Key elements to backup
            manifest = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'site_info': site,
                'files': {},
                'database': {}
            }
            
            # Temporary directory for building the archive
            # Use tempfile instead of predictable /tmp path
            import tempfile
            temp_dir = Path(tempfile.mkdtemp(prefix=f'wslaragon_backup_{site_name}_'))
            
            # 1. Backup Files
            doc_root = Path(site['document_root'])
            if doc_root.exists():
                shutil.make_archive(str(temp_dir / "files"), 'gztar', doc_root)
                manifest['files']['archive'] = "files.tar.gz"
            
            # 2. Backup Database
            if site.get('mysql') and site.get('database'):
                db_name = site.get('database')
                dump_file = temp_dir / "database.sql"
                success = self.mysql_manager.backup_database(db_name, str(dump_file))
                if success:
                    manifest['database']['dump'] = "database.sql"
                    manifest['database']['name'] = db_name
                else:
                    logger.warning(f"Failed to backup database {db_name}, continuing without it")

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

            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return {
                'success': True, 
                'file': str(target_file),
                'site': site_name
            }

        except Exception as e:
            # Cleanup on failure
            if 'temp_dir' in locals() and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f"Error exporting site {site_name}: {e}")
            return {'success': False, 'error': str(e)}

    def import_site(self, backup_file: str, new_name: str = None) -> Dict:
        """Import a site from a backup file
        
        Args:
            backup_file: Path to the .wslaragon backup file
            new_name: Optional new name for the imported site
            
        Returns:
            Dict with 'success', 'site', and 'info' keys
        """
        # Validate new_name if provided
        if new_name and not VALID_SITE_NAME.match(new_name):
            return {'success': False, 'error': f'Invalid site name: {new_name}'}
        
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                return {'success': False, 'error': 'Backup file not found'}

            # Validate path traversal
            backup_path = backup_path.resolve()
            
            # Use temporary directory (secure)
            import tempfile
            temp_dir = Path(tempfile.mkdtemp(prefix='wslaragon_import_'))
            
            # Safe tar extraction (CVE-2007-4559 mitigation)
            with tarfile.open(backup_path, "r:gz") as tar:
                # Filter out paths with traversal
                safe_members = []
                for member in tar.getmembers():
                    if member.name.startswith('/') or '..' in member.name:
                        logger.warning(f"Skipping dangerous path in archive: {member.name}")
                        continue
                    safe_members.append(member)
                tar.extractall(path=temp_dir, members=safe_members)
            
            if not (temp_dir / "manifest.json").exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                return {'success': False, 'error': 'Invalid backup: manifest.json missing'}

            with open(temp_dir / "manifest.json", 'r') as f:
                manifest = json.load(f)
            
            original_site = manifest['site_info']
            site_name = new_name or original_site['name']
            
            # Check if site exists
            if self.site_manager.get_site(site_name):
                shutil.rmtree(temp_dir, ignore_errors=True)
                return {'success': False, 'error': f"Site '{site_name}' already exists. Delete it first or choose a different name."}

            # 1. Create site structure
            create_result = self.site_manager.create_site(
                site_name,
                php=original_site.get('php', True),
                mysql=original_site.get('mysql', False),
                ssl=original_site.get('ssl', False),
                proxy_port=original_site.get('proxy_port'),
                site_type='html',  # Dummy type, we will overwrite files
                db_type=original_site.get('db_type'),
                database_name=original_site.get('database') if not new_name else f"{site_name}_db"
            )
            
            if not create_result['success']:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return {'success': False, 'error': f"Failed to create site structure: {create_result['error']}"}
            
            new_site_info = create_result['site']
            
            # 2. Restore Files
            if "archive" in manifest.get('files', {}):
                archive_path = temp_dir / manifest['files']['archive']
                doc_root = Path(new_site_info['document_root'])
                
                # Clear dummy files created by create_site
                # Use shutil.rmtree on contents instead of shell rm -rf
                for item in doc_root.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                
                # Unpack archive
                shutil.unpack_archive(str(archive_path), str(doc_root), 'gztar')
                
                # Fix permissions
                self.site_manager.fix_permissions(site_name)

            # 3. Restore Database
            if "dump" in manifest.get('database', {}) and new_site_info.get('database'):
                dump_path = temp_dir / manifest['database']['dump']
                db_name = new_site_info['database']
                
                success = self.mysql_manager.restore_database(db_name, str(dump_path))
                if not success:
                    logger.warning(f"Failed to restore database {db_name}")
            
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return {
                'success': True,
                'site': site_name,
                'info': new_site_info
            }

        except Exception as e:
            if 'temp_dir' in locals() and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f"Error importing site: {e}")
            return {'success': False, 'error': str(e)}