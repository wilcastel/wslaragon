import json
import logging
import subprocess
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..services.ssl import SSLManager
from .site_creators import get_site_creator

logger = logging.getLogger(__name__)


class SiteManager:
    def __init__(self, config, nginx_manager, mysql_manager):
        self.config = config
        self.nginx = nginx_manager
        self.mysql = mysql_manager
        self.sites_dir = Path(config.get('sites.dir', str(config.home_dir / ".wslaragon" / "sites")))
        
        # Provide default if document_root is missing
        document_root = config.get('sites.document_root')
        if document_root is None:
            document_root = str(config.home_dir / "web")
        self.document_root = Path(document_root)
        
        # Provide default if tld is missing
        self.tld = config.get('sites.tld', '.test')
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

    def _cleanup_failed_site_directory(self, site_base_dir: Optional[Path]):
        """Best-effort cleanup for partially created site directories."""
        if not site_base_dir or not site_base_dir.exists():
            return

        try:
            shutil.rmtree(site_base_dir)
            return
        except Exception as cleanup_error:
            logger.warning(f"Standard cleanup failed for {site_base_dir}: {cleanup_error}")

        try:
            subprocess.run(['sudo', 'rm', '-rf', str(site_base_dir)], check=True, timeout=60)
        except Exception as sudo_cleanup_error:
            logger.warning(f"Sudo cleanup also failed for {site_base_dir}: {sudo_cleanup_error}")
    
    def _normalize_site_name(self, site_name: str) -> str:
        """Strip the TLD suffix if the user included it in the site name.
        
        'dash.aaa.test' -> 'dash.aaa'
        'dash.aaa'      -> 'dash.aaa'
        'blog'           -> 'blog'
        """
        if site_name.endswith(self.tld):
            site_name = site_name[:-len(self.tld)]
        return site_name

    def create_site(self, site_name: str, php: bool = True, 
                   mysql: bool = None, ssl: bool = True,
                   database_name: str = None, public_dir: bool = False,
                   proxy_port: int = None, site_type: str = None, 
                   db_type: str = None, recreate: bool = False,
                   vite_template: str = None, astro_template: str = None) -> Dict:
        """Create a new site"""
        site_base_dir: Optional[Path] = None
        cleanup_on_failure = False
        try:
            # Normalize: strip TLD if user included it
            site_name = self._normalize_site_name(site_name)
            
            if not site_name or not self._is_valid_site_name(site_name):
                return {'success': False, 'error': 'Invalid site name. Use letters, numbers, hyphens, underscores and dots (e.g. dash.misitio)'}
            
            # Auto-enable mysql for WordPress (WP requires a database)
            if site_type == 'wordpress' and mysql is None:
                mysql = True
            
            # Default mysql to False if still None (user didn't specify)
            if mysql is None:
                mysql = False
            
            # Auto-configure for Node/Python/Vite (Astro SSG does NOT need a proxy)
            is_astro_ssg = bool(astro_template)
            if site_type in ('node', 'python') or vite_template:
                if not proxy_port:
                    # Find next free port
                    start_port = 3000 if site_type == 'node' or vite_template else 8000
                    proxy_port = self._find_next_free_port(start_port)
            
            if site_name in self.sites and not recreate:
                return {'success': False, 'error': 'Site already exists'}
            
            site_base_dir = self.document_root / site_name
            site_exists = site_base_dir.exists()
            messages = []

            # Cleanup partial files if creation fails after this point.
            # Applies to fresh creates and forced recreates.
            cleanup_on_failure = (not site_exists) or recreate or (site_exists and site_name not in self.sites)
            
            # Check for proxy port collisions
            if proxy_port:
                for existing_site in self.sites.values():
                    # Check if port matches and it's not the same site (in case of recreate)
                    if existing_site.get('proxy_port') == proxy_port and existing_site['name'] != site_name:
                         return {'success': False, 'error': f"Port {proxy_port} is already used by site '{existing_site['name']}'"}

            if site_exists:
                if recreate or site_name not in self.sites:
                    # recreate=True OR site was deleted but directory left behind.
                    # Clean it so the creator gets a fresh directory.
                    subprocess.run(['sudo', 'rm', '-rf', str(site_base_dir)], check=True)
                    messages.append(f"[yellow]Cleaned existing directory: {site_base_dir}[/yellow]")
            
            # Astro SSG: no PHP
            if is_astro_ssg:
                php = False
            
            site_base_dir.mkdir(exist_ok=True, parents=True)
            
            is_laravel = site_type is not None and (site_type == 'laravel' or site_type.isdigit())
            is_wordpress = site_type == 'wordpress'
            is_phpmyadmin = site_type == 'phpmyadmin'
            # WordPress and phpMyAdmin install in root by default, unlike Laravel which uses public/
            use_public = public_dir or is_laravel
            
            if is_astro_ssg:
                web_root = site_base_dir / "dist"
            else:
                web_root = site_base_dir / "public" if use_public else site_base_dir
            
            if use_public and not is_laravel and not web_root.exists():
                web_root.mkdir(exist_ok=True, parents=True)
                messages.append(f"[green]Created public folder: {web_root}[/green]")
            # IMPORTANT: For Astro SSG we must NOT pre-create dist/ before scaffolding.
            # `npm create astro@latest .` writes to a random subfolder when cwd is not empty.
            elif not use_public and not web_root.exists() and not is_astro_ssg:
                web_root.mkdir(exist_ok=True, parents=True)

# Use Strategy pattern for site creation
            # Run creator for all sites that have a site_type or template.
            # Generic proxy-only sites (node/python without template) skip scaffolding.
            needs_scaffolding = site_type in ('html', 'wordpress', 'phpmyadmin', 'laravel') or \
                                site_type and site_type.isdigit() or \
                                vite_template or astro_template
            
            if needs_scaffolding or (not proxy_port):
                # Directory is fresh or user explicitly asked to recreate — run creator
                laravel_version = None
                if is_laravel:
                    if site_type and site_type != 'laravel':
                        try:
                            laravel_version = int(site_type)
                        except ValueError:
                            laravel_version = 12
                    else:
                        laravel_version = 12
                
                creator = get_site_creator(
                    site_type, vite_template, php, self.config,
                    site_name, web_root, site_base_dir, self.tld, proxy_port,
                    version=laravel_version, db_type=db_type, database_name=database_name,
                    astro_template=astro_template
                )
                if creator:
                    creator_messages = creator.create()
                    messages.extend(creator_messages)
            
            db_created = False
            db_type_final = db_type or ('mysql' if mysql else None)
            
            if db_type_final in ('mysql', 'postgres', 'supabase'):
                if not database_name:
                    # Sanitize: replace dots with underscores for DB names
                    database_name = f"{site_name.replace('.', '_')}_db"
                
                if db_type_final == 'mysql':
                    if self.mysql.database_exists(database_name):
                        messages.append(f"[yellow]Using existing database: {database_name}[/yellow]")
                        db_created = False
                    else:
                        db_created, db_error = self.mysql.create_database(database_name)
                        if not db_created:
                            raise Exception(f'Failed to create database: {db_error}')
                        messages.append(f"[green]Created new database: {database_name}[/green]")
                elif db_type_final in ('postgres', 'supabase'):
                    db_created = True
            
            # Create scaffolding for Vite/Node/Python (these have proxy_port)
            if vite_template:
                # Vite scaffolding is handled by ViteSiteCreator above
                pass
            
            # Create default app file for Node/Python
            elif site_type == 'node':
                # Handled by NodeSiteCreator above
                pass
            elif site_type == 'python':
                # Handled by PythonSiteCreator above
                pass
            
            # Astro headless starts with no proxies — user adds them via:
            # wslaragon site api add <name> /api https://backend.test
            api_proxies = {}
            
            if ssl:
                ssl_mgr = SSLManager(self.config)
                ssl_result = ssl_mgr.setup_ssl_for_site(site_name, self.tld)
                if not ssl_result['success']:
                    raise Exception(f"Failed to generate SSL: {ssl_result['error']}")
            
            nginx_created, nginx_error = self.nginx.add_site(
                site_name, 
                str(web_root), 
                ssl=ssl, 
                php=php,
                proxy_port=proxy_port,
                api_proxies=api_proxies,
                astro_ssg=is_astro_ssg
            )
            
            if not nginx_created:
                raise Exception(f'Failed to create Nginx configuration: {nginx_error}')
            
            site_info = {
                'name': site_name,
                'domain': f"{site_name}{self.tld}",
                'document_root': str(site_base_dir),
                'web_root': str(web_root),
                'php': php,
                'mysql': mysql,
                'db_type': db_type_final,
                'ssl': ssl,
                'proxy_port': proxy_port,
                'database': database_name if db_type_final else None,
                'api_proxies': api_proxies,
                'astro_template': astro_template,
                'created_at': datetime.now().isoformat(),
                'enabled': True
            }
            
            self.sites[site_name] = site_info
            self._save_sites()
            
            self.fix_permissions(site_name)
            
            panel_content = f"[bold green]Site created successfully![/bold green]\n\n"
            panel_content += f"Domain: {site_info['domain']}\n"
            panel_content += f"Document Root: {site_info['document_root']}\n"
            panel_content += f"PHP: {'Yes' if site_info['php'] else 'No'}\n"
            panel_content += f"Proxy: {site_info.get('proxy_port') if site_info.get('proxy_port') else 'No'}\n"
            panel_content += f"MySQL: {'Yes' if site_info['mysql'] else 'No'}\n"
            panel_content += f"SSL: {'Yes' if site_info['ssl'] else 'No'}"
            
            if messages:
                panel_content += "\n\n" + "\n".join(msg for msg in messages)
            
            return {'success': True, 'site': site_info, 'messages': messages}
            
        except Exception as e:
            if cleanup_on_failure and site_name not in self.sites:
                self._cleanup_failed_site_directory(site_base_dir)
            logger.error(f"Failed to create site {site_name}: {e}")
            return {'success': False, 'error': str(e)}

    def create_headless_site(self, site_name: str, backend: str, frontend: str,
                             ssl: bool = True, database_name: str = None,
                             recreate: bool = False) -> Dict:
        """Create a headless site pair: frontend at name.test and backend at api.name.test."""
        root_dir: Optional[Path] = None
        backend_site_name: Optional[str] = None
        db_name: Optional[str] = None
        db_created_by_us = False
        try:
            site_name = self._normalize_site_name(site_name)
            if not site_name or not self._is_valid_site_name(site_name):
                return {'success': False, 'error': 'Invalid site name. Use letters, numbers, hyphens, underscores and dots (e.g. dash.misitio)'}
            if backend not in ('wordpress', 'laravel'):
                return {'success': False, 'error': 'Invalid backend. Use wordpress or laravel'}
            if frontend == 'sveltkit':
                frontend = 'sveltekit'
            if frontend not in ('sveltekit', 'astro'):
                return {'success': False, 'error': 'Invalid frontend. Use sveltekit or astro'}

            backend_site_name = f"api.{site_name}"
            colliding_sites = [name for name in (site_name, backend_site_name) if name in self.sites]
            if colliding_sites and not recreate:
                return {'success': False, 'error': f"Site already exists: {', '.join(colliding_sites)}"}

            root_dir = self.document_root / site_name
            if root_dir.exists():
                if not recreate:
                    return {'success': False, 'error': f"Site directory already exists: {root_dir}"}
                subprocess.run(['sudo', 'rm', '-rf', str(root_dir)], check=True)

            backend_dir = root_dir / "back"
            frontend_dir = root_dir / "front"
            backend_web_root = backend_dir / "public" if backend == 'laravel' else backend_dir
            frontend_web_root = frontend_dir / "dist" if frontend == 'astro' else frontend_dir
            root_dir.mkdir(parents=True, exist_ok=True)
            backend_dir.mkdir(parents=True, exist_ok=True)
            frontend_dir.mkdir(parents=True, exist_ok=True)

            frontend_proxy_port = None
            if frontend == 'sveltekit':
                frontend_proxy_port = self._find_next_free_port(3000)

            db_name = database_name or f"{backend_site_name.replace('.', '_')}_db"
            messages = []

            backend_creator = get_site_creator(
                backend, None, True, self.config, backend_site_name,
                backend_web_root, backend_dir, self.tld, None,
                version=12, db_type='mysql', database_name=db_name
            )
            if backend_creator:
                messages.extend(backend_creator.create())

            if self.mysql.database_exists(db_name):
                messages.append(f"[yellow]Using existing database: {db_name}[/yellow]")
            else:
                db_created, db_error = self.mysql.create_database(db_name)
                if not db_created:
                    raise Exception(f'Failed to create database: {db_error}')
                db_created_by_us = True
                messages.append(f"[green]Created new database: {db_name}[/green]")

            if frontend == 'astro':
                frontend_creator = get_site_creator(
                    None, None, False, self.config, site_name,
                    frontend_web_root, frontend_dir, self.tld, None,
                    astro_template='basics'
                )
            else:
                frontend_creator = get_site_creator(
                    'sveltekit', None, False, self.config, site_name,
                    frontend_web_root, frontend_dir, self.tld, frontend_proxy_port
                )
            if frontend_creator:
                messages.extend(frontend_creator.create())

            if ssl:
                ssl_mgr = SSLManager(self.config)
                for configured_site in (site_name, backend_site_name):
                    ssl_result = ssl_mgr.setup_ssl_for_site(configured_site, self.tld)
                    if not ssl_result['success']:
                        raise Exception(f"Failed to generate SSL for {configured_site}: {ssl_result['error']}")

            backend_nginx_created, backend_nginx_error = self.nginx.add_site(
                backend_site_name, str(backend_web_root), ssl=ssl, php=True
            )
            if not backend_nginx_created:
                raise Exception(f'Failed to create backend Nginx configuration: {backend_nginx_error}')

            frontend_nginx_created, frontend_nginx_error = self.nginx.add_site(
                site_name, str(frontend_web_root), ssl=ssl, php=False,
                proxy_port=frontend_proxy_port, astro_ssg=(frontend == 'astro')
            )
            if not frontend_nginx_created:
                raise Exception(f'Failed to create frontend Nginx configuration: {frontend_nginx_error}')

            now = datetime.now().isoformat()
            frontend_site_info = {
                'name': site_name,
                'domain': f"{site_name}{self.tld}",
                'document_root': str(frontend_dir),
                'web_root': str(frontend_web_root),
                'php': False,
                'mysql': False,
                'db_type': None,
                'ssl': ssl,
                'proxy_port': frontend_proxy_port,
                'database': None,
                'api_proxies': {},
                'astro_template': 'basics' if frontend == 'astro' else None,
                'headless': True,
                'role': 'frontend',
                'root': str(root_dir),
                'backend': backend,
                'frontend': frontend,
                'backend_site': backend_site_name,
                'created_at': now,
                'enabled': True
            }
            backend_site_info = {
                'name': backend_site_name,
                'domain': f"{backend_site_name}{self.tld}",
                'document_root': str(backend_dir),
                'web_root': str(backend_web_root),
                'php': True,
                'mysql': True,
                'db_type': 'mysql',
                'ssl': ssl,
                'proxy_port': None,
                'database': db_name,
                'api_proxies': {},
                'headless': True,
                'role': 'backend',
                'root': str(root_dir),
                'backend': backend,
                'frontend': frontend,
                'frontend_site': site_name,
                'created_at': now,
                'enabled': True
            }

            self.sites[site_name] = frontend_site_info
            self.sites[backend_site_name] = backend_site_info
            self._save_sites()

            self.fix_permissions(site_name)
            self.fix_permissions(backend_site_name)

            return {
                'success': True,
                'site': frontend_site_info,
                'backend_site': backend_site_info,
                'messages': messages
            }

        except Exception as e:
            for rollback_site in (site_name, backend_site_name):
                if rollback_site:
                    try:
                        self.nginx.remove_site(rollback_site)
                    except Exception:
                        pass
                    self.sites.pop(rollback_site, None)
            self._save_sites()
            self._cleanup_failed_site_directory(root_dir)
            if db_created_by_us and db_name:
                try:
                    self.mysql.drop_database(db_name)
                except Exception:
                    pass
            logger.error(f"Failed to create headless site {site_name}: {e}")
            return {'success': False, 'error': str(e)}

    def update_site_root(self, site_name: str, public_dir: bool = True) -> Dict:
        """Update site document root (e.g. to point to public/)"""
        try:
            site_name = self._normalize_site_name(site_name)
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
                proxy_port=site_info.get('proxy_port'),
                astro_ssg=bool(site_info.get('astro_template'))
            )
            
            if not success:
                # Try to revert
                self.nginx.add_site(
                    site_name,
                    str(old_web_root),
                    ssl=site_info.get('ssl', False),
                    php=site_info.get('php', True),
                    proxy_port=site_info.get('proxy_port'),
                    astro_ssg=bool(site_info.get('astro_template'))
                )
                return {'success': False, 'error': f"Failed to update Nginx: {error}"}
            
            # Update registry
            site_info['web_root'] = str(new_web_root)
            self._save_sites()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Failed to update site root for {site_name}: {e}")
            return {'success': False, 'error': str(e)}
        

    
    def delete_site(self, site_name: str, remove_files: bool = False,
                    remove_database: bool = False) -> Dict:
        """Delete a site. If it's one half of a headless pair, deletes both halves."""
        try:
            site_name = self._normalize_site_name(site_name)
            if site_name not in self.sites:
                return {'success': False, 'error': 'Site not found'}

            site_info = self.sites[site_name]

            # Headless sites are created and stored as a linked frontend/backend
            # pair sharing one root directory — deleting only one half would
            # orphan the other's registry entry, nginx config and directory.
            paired_site_name = site_info.get('backend_site') or site_info.get('frontend_site')
            names_to_delete = [site_name]
            if site_info.get('headless') and paired_site_name and paired_site_name in self.sites:
                names_to_delete.append(paired_site_name)
            shared_root = site_info.get('root')

            for name in names_to_delete:
                info = self.sites[name]

                # Remove Nginx configuration
                self.nginx.remove_site(name)

                # Remove database if requested
                if remove_database and info.get('database'):
                    # Only attempt to delete MySQL databases
                    # Postgres/Supabase are external (Docker) and we don't manage their lifecycle yet
                    if info.get('db_type') == 'mysql' or not info.get('db_type'):
                        self.mysql.drop_database(info['database'])

                # Remove files now unless they live under a shared root
                # (handled once, below, so we don't delete it twice)
                if remove_files and not shared_root:
                    site_doc_root = Path(info['document_root'])
                    if site_doc_root.exists():
                        subprocess.run(['sudo', 'rm', '-rf', str(site_doc_root)], check=True, timeout=60)

                del self.sites[name]

            if remove_files and shared_root:
                root_path = Path(shared_root)
                if root_path.exists():
                    subprocess.run(['sudo', 'rm', '-rf', str(root_path)], check=True, timeout=60)

            self._save_sites()

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to delete site {site_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def enable_site(self, site_name: str) -> Dict:
        """Enable a site"""
        try:
            site_name = self._normalize_site_name(site_name)
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
            logger.error(f"Failed to enable site {site_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def disable_site(self, site_name: str) -> Dict:
        """Disable a site"""
        try:
            site_name = self._normalize_site_name(site_name)
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
            logger.error(f"Failed to disable site {site_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_sites(self) -> List[Dict]:
        """List all sites"""
        return list(self.sites.values())
    
    def get_site(self, site_name: str) -> Optional[Dict]:
        """Get site information"""
        site_name = self._normalize_site_name(site_name)
        return self.sites.get(site_name)
    
    def update_site(self, site_name: str, **kwargs) -> Dict:
        """Update site configuration"""
        try:
            site_name = self._normalize_site_name(site_name)
            if site_name not in self.sites:
                return {'success': False, 'error': 'Site not found'}
            
            site_info = self.sites[site_name]
            
            # Update allowed fields
            allowed_fields = ['php', 'mysql', 'ssl', 'database', 'proxy_port', 'api_proxies']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    site_info[field] = value
            
            # Recreate Nginx configuration if needed
            if any(field in kwargs for field in ['php', 'ssl', 'proxy_port', 'api_proxies']):
                self.nginx.remove_site(site_name)
                self.nginx.add_site(
                    site_name,
                    site_info['document_root'],
                    ssl=site_info.get('ssl', False),
                    php=site_info.get('php', True),
                    proxy_port=site_info.get('proxy_port'),
                    api_proxies=site_info.get('api_proxies', {}),
                    astro_ssg=bool(site_info.get('astro_template'))
                )
            
            self._save_sites()
            return {'success': True, 'site': site_info}
            
        except Exception as e:
            logger.error(f"Failed to update site {site_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_site_logs(self, site_name: str) -> Dict[str, str]:
        """Get site logs"""
        try:
            site_name = self._normalize_site_name(site_name)
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
            logger.error(f"Failed to get logs for {site_name}: {e}")
            return {'error': str(e)}
    
    def get_site_url(self, site_name: str) -> Optional[str]:
        """Get site URL"""
        site_name = self._normalize_site_name(site_name)
        if site_name in self.sites:
            protocol = 'https' if self.sites[site_name].get('ssl') else 'http'
            return f"{protocol}://{site_name}{self.tld}"
        return None

    def fix_permissions(self, site_name: str) -> Dict:
        """Fix file owner and permissions for a site"""
        try:
            site_name = self._normalize_site_name(site_name)
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
            
            # WordPress specific fix: FS_METHOD direct
            # This prevents WP from asking for FTP credentials
            wp_config = Path(doc_root) / 'wp-config.php'
            if wp_config.exists():
                try:
                    with open(wp_config, 'r') as f:
                        content = f.read()
                    
                    if "FS_METHOD" not in content:
                        # Insert before ABSPATH definition or append to file
                        if "if ( ! defined( 'ABSPATH' ) )" in content:
                            new_content = content.replace(
                                "if ( ! defined( 'ABSPATH' ) )",
                                "define( 'FS_METHOD', 'direct' );\n\nif ( ! defined( 'ABSPATH' ) )"
                            )
                        else:
                            new_content = content + "\ndefine( 'FS_METHOD', 'direct' );\n"
                        
                        with open(wp_config, 'w') as f:
                            f.write(new_content)
                            
                        # Re-apply ownership to wp-config.php just in case
                        subprocess.run(['sudo', 'chown', f'{current_user}:www-data', str(wp_config)], check=True)
                except Exception:
                    pass # Non-critical failure, continue
            
            return {'success': True}
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed while fixing permissions for {site_name}: {e}")
            return {'success': False, 'error': f"Command failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Failed to fix permissions for {site_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def add_api_proxy(self, site_name: str, path: str, backend: str) -> Dict:
        """Add an API proxy to a site (e.g. /api -> https://api.example.test)"""
        try:
            site_name = self._normalize_site_name(site_name)
            if site_name not in self.sites:
                return {'success': False, 'error': 'Site not found'}
            
            site_info = self.sites[site_name]
            
            # Normalize path: ensure it starts with /
            if not path.startswith('/'):
                path = '/' + path
            
            # Remove trailing slash from path (location blocks match /path/ pattern)
            path = path.rstrip('/')
            
            # Validate backend URL
            if not backend.startswith(('http://', 'https://')):
                backend = 'https://' + backend
            
            # Initialize api_proxies if missing
            if 'api_proxies' not in site_info:
                site_info['api_proxies'] = {}
            
            # Check for duplicate path
            if path in site_info['api_proxies']:
                return {'success': False, 'error': f"API proxy path '{path}' already exists (-> {site_info['api_proxies'][path]})"}
            
            site_info['api_proxies'][path] = backend
            self._save_sites()
            
            # Regenerate Nginx config with new proxy
            self.nginx.remove_site(site_name)
            success, error = self.nginx.add_site(
                site_name,
                site_info['document_root'],
                ssl=site_info.get('ssl', False),
                php=site_info.get('php', True),
                proxy_port=site_info.get('proxy_port'),
                api_proxies=site_info.get('api_proxies', {}),
                astro_ssg=bool(site_info.get('astro_template'))
            )
            
            if not success:
                # Revert the change
                del site_info['api_proxies'][path]
                self._save_sites()
                return {'success': False, 'error': f"Failed to update Nginx config: {error}"}
            
            return {'success': True, 'site': site_info, 'path': path, 'backend': backend}
            
        except Exception as e:
            logger.error(f"Failed to add API proxy for {site_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def remove_api_proxy(self, site_name: str, path: str) -> Dict:
        """Remove an API proxy from a site"""
        try:
            site_name = self._normalize_site_name(site_name)
            if site_name not in self.sites:
                return {'success': False, 'error': 'Site not found'}
            
            site_info = self.sites[site_name]
            
            # Normalize path
            if not path.startswith('/'):
                path = '/' + path
            path = path.rstrip('/')
            
            if 'api_proxies' not in site_info or path not in site_info['api_proxies']:
                return {'success': False, 'error': f"No API proxy found at path '{path}'"}
            
            old_backend = site_info['api_proxies'].pop(path)
            
            # Clean up empty api_proxies
            if not site_info['api_proxies']:
                del site_info['api_proxies']
            
            self._save_sites()
            
            # Regenerate Nginx config without the proxy
            self.nginx.remove_site(site_name)
            success, error = self.nginx.add_site(
                site_name,
                site_info['document_root'],
                ssl=site_info.get('ssl', False),
                php=site_info.get('php', True),
                proxy_port=site_info.get('proxy_port'),
                api_proxies=site_info.get('api_proxies', {}),
                astro_ssg=bool(site_info.get('astro_template'))
            )
            
            if not success:
                # Revert the change
                if 'api_proxies' not in site_info:
                    site_info['api_proxies'] = {}
                site_info['api_proxies'][path] = old_backend
                self._save_sites()
                return {'success': False, 'error': f"Failed to update Nginx config: {error}"}
            
            return {'success': True, 'site': site_info, 'removed_path': path, 'removed_backend': old_backend}
            
        except Exception as e:
            logger.error(f"Failed to remove API proxy for {site_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_api_proxies(self, site_name: str) -> Dict:
        """List all API proxies for a site"""
        site_name = self._normalize_site_name(site_name)
        if site_name not in self.sites:
            return {'success': False, 'error': 'Site not found'}
        
        site_info = self.sites[site_name]
        proxies = site_info.get('api_proxies', {})
        
        return {'success': True, 'proxies': proxies}
    
    @staticmethod
    def _is_valid_site_name(name: str) -> bool:
        """Validate site name: allows letters, numbers, hyphens, underscores and dots.
        Supports subdomains like 'dash.misitio', 'api.v2.myapp'.
        Rejects names starting/ending with dot or hyphen, consecutive dots, etc.
        """
        if not name:
            return False
        # Must only contain allowed characters
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')
        if not all(c in allowed_chars for c in name):
            return False
        # Cannot start or end with dot or hyphen
        if name[0] in '.-' or name[-1] in '.-':
            return False
        # No consecutive dots
        if '..' in name:
            return False
        # Each label between dots must be valid
        for label in name.split('.'):
            if not label or label.startswith('-') or label.endswith('-'):
                return False
        return True

    def _find_next_free_port(self, start_port: int) -> int:
        """Find the next available port starting from start_port"""
        import socket
        
        port = start_port
        while True:
            # Check internal registry
            collision = False
            for site in self.sites.values():
                if site.get('proxy_port') == port:
                    collision = True
                    break
            
            if collision:
                port += 1
                continue
                
            # Check system socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) == 0:
                    # Port is open (in use)
                    port += 1
                else:
                    return port
