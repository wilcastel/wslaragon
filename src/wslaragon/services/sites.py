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
                   proxy_port: int = None, site_type: str = None, 
                   db_type: str = None, recreate: bool = False) -> Dict:
        """Create a new site"""
        try:
            if not site_name or not site_name.replace('-', '').replace('_', '').isalnum():
                return {'success': False, 'error': 'Invalid site name'}
            
            # Auto-configure for Node/Python
            if site_type in ('node', 'python'):
                # Disable PHP/MySQL by default unless explicitly requested (which we can't easily track with click defaults here without more logic, 
                # but let's assume if user uses --node/--python they want an app server).
                # Note: In main.py we'll handle passing the right flags.
                
                if not proxy_port:
                    # Find next free port
                    start_port = 3000 if site_type == 'node' else 8000
                    proxy_port = self._find_next_free_port(start_port)
            
            if site_name in self.sites and not recreate:
                return {'success': False, 'error': 'Site already exists'}
            
            site_base_dir = self.document_root / site_name
            site_exists = site_base_dir.exists()
            messages = []
            
            # Check for proxy port collisions
            if proxy_port:
                for existing_site in self.sites.values():
                    # Check if port matches and it's not the same site (in case of recreate)
                    if existing_site.get('proxy_port') == proxy_port and existing_site['name'] != site_name:
                         return {'success': False, 'error': f"Port {proxy_port} is already used by site '{existing_site['name']}'"}

            if site_exists:
                if recreate:
                    subprocess.run(['sudo', 'rm', '-rf', str(site_base_dir)], check=True)
                    messages.append(f"[yellow]📁 Deleted existing folder for recreate[/yellow]")
                else:
                    messages.append(f"[yellow]📁 Using existing folder: {site_base_dir}[/yellow]")
            
            site_base_dir.mkdir(exist_ok=True, parents=True)
            
            is_laravel = site_type is not None and (site_type == 'laravel' or site_type.isdigit())
            is_wordpress = site_type == 'wordpress'
            use_public = public_dir or is_laravel or is_wordpress
            
            web_root = site_base_dir / "public" if use_public else site_base_dir
            
            if use_public and not web_root.exists():
                web_root.mkdir(exist_ok=True, parents=True)
                messages.append(f"[green]📁 Created public folder: {web_root}[/green]")
            elif not use_public and not web_root.exists():
                web_root.mkdir(exist_ok=True, parents=True)
            
            if not proxy_port and (not site_exists or recreate):
                if site_type == 'html':
                    self._create_html_site(web_root, site_name)
                elif site_type == 'wordpress':
                    self._create_wordpress_site(web_root, site_name)
                elif is_laravel:
                    laravel_version = 12
                    if site_type and site_type != 'laravel':
                        try:
                            laravel_version = int(site_type)
                        except ValueError:
                            pass
                    index_file = web_root / "index.php"
                    index_content = f"""<?php
echo "<h1>Welcome to {site_name}{self.tld}!</h1>";
echo "<p>Laravel project ready.</p>";
echo "<p>Run 'composer create-project laravel/laravel .' to install.</p>";
phpinfo();
?>"""
                    with open(index_file, 'w') as f:
                        f.write(index_content)
                    messages.append(f"[yellow]📝 Laravel structure ready. Run 'composer create-project laravel/laravel:^{laravel_version}.0 .' to install.[/yellow]")
                else:
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
            
            db_created = False
            db_type_final = db_type or ('mysql' if mysql else None)
            
            if db_type_final in ('mysql', 'postgres', 'supabase'):
                if not database_name:
                    database_name = f"{site_name}_db"
                
                if db_type_final == 'mysql':
                    if self.mysql.database_exists(database_name):
                        messages.append(f"[yellow]🗄️ Using existing database: {database_name}[/yellow]")
                        db_created = False
                    else:
                        db_created, db_error = self.mysql.create_database(database_name)
                        if not db_created:
                            return {'success': False, 'error': f'Failed to create database: {db_error}'}
                        messages.append(f"[green]✅ Created new database: {database_name}[/green]")
                elif db_type_final in ('postgres', 'supabase'):
                    db_created = True
            
            if ssl:
                ssl_mgr = SSLManager(self.config)
                ssl_result = ssl_mgr.setup_ssl_for_site(site_name, self.tld)
                if not ssl_result['success']:
                    return {'success': False, 'error': f"Failed to generate SSL: {ssl_result['error']}"}
            
            nginx_created, nginx_error = self.nginx.add_site(
                site_name, 
                str(web_root), 
                ssl=ssl, 
                php=php,
                proxy_port=proxy_port
            )
            
            if not nginx_created:
                return {'success': False, 'error': f'Failed to create Nginx configuration: {nginx_error}'}
            
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
                'created_at': datetime.now().isoformat(),
                'enabled': True
            }
            
            self.sites[site_name] = site_info
            self._save_sites()
            
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

    def _create_html_site(self, web_root: Path, site_name: str):
        """Create a static HTML site with styles and js folders"""
        import os
        
        index_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_name}</title>
    <link rel="stylesheet" href="styles/estilos.css">
</head>
<body>
    <header>
        <h1>{site_name}</h1>
        <nav>
            <ul>
                <li><a href="#">Inicio</a></li>
                <li><a href="#">Acerca</a></li>
                <li><a href="#">Contacto</a></li>
            </ul>
        </nav>
    </header>
    <main>
        <section class="hero">
            <h2>Bienvenido a tu nuevo sitio web</h2>
            <p>Este es un proyecto HTML estático listo para desarrollar.</p>
        </section>
        <section class="features">
            <article>
                <h3>Rápido</h3>
                <p>Sitio web estático de alto rendimiento.</p>
            </article>
            <article>
                <h3>Moderno</h3>
                <p>Con estructura CSS y JavaScript lista.</p>
            </article>
            <article>
                <h3>Fácil</h3>
                <p>Simple de personalizar y expandir.</p>
            </article>
        </section>
    </main>
    <footer>
        <p>&copy; 2024 {site_name}. Todos los derechos reservados.</p>
    </footer>
    <script src="js/app.js"></script>
</body>
</html>"""
        
        styles_dir = web_root / "styles"
        styles_dir.mkdir(exist_ok=True)
        
        estilos_content = f"""/* Reset y estilos base */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f4f4f4;
}}

header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    text-align: center;
}}

header h1 {{
    margin-bottom: 1rem;
}}

nav ul {{
    list-style: none;
    display: flex;
    justify-content: center;
    gap: 2rem;
}}

nav a {{
    color: white;
    text-decoration: none;
    font-weight: 500;
    transition: opacity 0.3s;
}}

nav a:hover {{
    opacity: 0.8;
}}

main {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}}

.hero {{
    background: white;
    padding: 3rem;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}}

.hero h2 {{
    color: #667eea;
    margin-bottom: 1rem;
}}

.features {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
}}

.features article {{
    background: white;
    padding: 2rem;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s;
}}

.features article:hover {{
    transform: translateY(-5px);
}}

.features h3 {{
    color: #667eea;
    margin-bottom: 0.5rem;
}}

footer {{
    background: #333;
    color: white;
    text-align: center;
    padding: 1.5rem;
    margin-top: 2rem;
}}
"""
        
        js_dir = web_root / "js"
        js_dir.mkdir(exist_ok=True)
        
        app_js_content = f"""// App JavaScript - {site_name}
// Scripts del sitio

document.addEventListener('DOMContentLoaded', function() {{
    console.log('DOM cargado - {site_name}');
    
    // Smooth scroll para enlaces
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
        anchor.addEventListener('click', function(e) {{
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {{
                target.scrollIntoView({{ behavior: 'smooth' }});
            }}
        }});
    }});
    
    console.log('Scripts inicializados correctamente');
}});
"""
        
        with open(web_root / "index.html", 'w', encoding='utf-8') as f:
            f.write(index_content)
        with open(styles_dir / "estilos.css", 'w', encoding='utf-8') as f:
            f.write(estilos_content)
        with open(js_dir / "app.js", 'w', encoding='utf-8') as f:
            f.write(app_js_content)
    
    def _create_wordpress_site(self, web_root: Path, site_name: str):
        """Create a WordPress site"""
        import shutil
        
        db_password = self.config.get('mysql.password')
        current_user = os.getenv('SUDO_USER') or os.getenv('USER')
        
        if web_root.exists():
            subprocess.run(['sudo', 'rm', '-rf', str(web_root)], check=True)
        
        web_root.mkdir(parents=True)
        
        wp_tar_path = f'/tmp/wordpress-{site_name}.tar.gz'
        subprocess.run(['wget', '-q', '-O', wp_tar_path, 
            'https://wordpress.org/latest.tar.gz'], check=True)
        subprocess.run(['sudo', 'tar', '-xzf', wp_tar_path, '-C', 
            str(web_root.parent)], check=True)
        
        wordpress_dir = web_root.parent / 'wordpress'
        if wordpress_dir.exists():
            subprocess.run(['sudo', 'cp', '-r', f'{wordpress_dir}/.', str(web_root)], check=True)
            subprocess.run(['sudo', 'rm', '-rf', str(wordpress_dir)], check=True)
        subprocess.run(['sudo', 'rm', '-f', wp_tar_path], check=True)
        
        subprocess.run(['sudo', 'chown', '-R', f'{current_user}:www-data', str(web_root)], check=True)
        subprocess.run(['sudo', 'chmod', '-R', '755', str(web_root)], check=True)
        
        wp_content = f"""<?php
 /**
  * The base configuration for WordPress
  */
 define( 'DB_NAME', '{site_name}_db' );
 define( 'DB_USER', 'root' );
 define( 'DB_PASSWORD', '{db_password}' );
 define( 'DB_HOST', 'localhost' );
 define( 'DB_CHARSET', 'utf8mb4' );
 define( 'DB_COLLATE', 'utf8mb4_unicode_ci' );

 $table_prefix = 'wp_';

 define( 'WP_DEBUG', true );
 define( 'WP_DEBUG_LOG', true );
 define( 'WP_DEBUG_DISPLAY', false );
 define( 'WP_MEMORY_LIMIT', '256M' );

 if ( ! defined( 'ABSPATH' ) ) {{
     define( 'ABSPATH', __DIR__ . '/' );
 }}

 require_once ABSPATH . 'wp-settings.php';
 """
        
        index_php_content = """<?php
 /**
  * Front to the WordPress application.
  */
 define( 'WP_USE_THEMES', true );
 require __DIR__ . '/wp-blog-header.php';
 """
        
        with open(web_root / "wp-config.php", 'w') as f:
            f.write(wp_content)
        with open(web_root / "index.php", 'w') as f:
            f.write(index_php_content)
    
    def _create_laravel_site(self, site_base_dir: Path, site_name: str, version: int = 12,
                              db_type: str = None, database_name: str = None):
        """Create a Laravel site with PostgreSQL or Supabase support"""
        import shutil
        
        if not database_name:
            database_name = f"{site_name}_db"
        
        postgres_port = self.config.get('supabase.postgres_port', 5433)
        postgres_password = self.config.get('supabase.postgres_password', 'postgres')
        
        supabase_api_url = f"http://localhost:{self.config.get('supabase.api_port', 8081)}"
        
        composer_project_cmd = [
            'composer', 'create-project',
            f'laravel/laravel:^{version}.0',
            str(site_base_dir),
            '--no-interaction',
            '--no-progress'
        ]
        
        result = subprocess.run(composer_project_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            if 'out of memory' in result.stderr.lower():
                env = os.environ.copy()
                env['COMPOSER_MEMORY_LIMIT'] = '-1'
                subprocess.run(['composer', 'create-project',
                    f'laravel/laravel:^{version}.0',
                    str(site_base_dir),
                    '--no-interaction',
                    '--no-progress'
                ], env=env, check=True)
            else:
                raise Exception(f"Laravel installation failed: {result.stderr}")
        
        if db_type in ('postgres', 'supabase'):
            env_content = f"""APP_NAME="{site_name}"
APP_ENV=local
APP_KEY=base64:$(php -r "echo base64_encode(random_bytes(32));")
APP_DEBUG=true
APP_URL=http://{site_name}.test

LOG_CHANNEL=stack
LOG_LEVEL=debug

DB_CONNECTION=pgsql
DB_HOST=127.0.0.1
DB_PORT={postgres_port}
DB_DATABASE={database_name}
DB_USERNAME=postgres
DB_PASSWORD={postgres_password}

BROADCAST_DRIVER=log
CACHE_DRIVER=file
FILESYSTEM_DISK=local
QUEUE_CONNECTION=sync
SESSION_DRIVER=file
SESSION_LIFETIME=120

REDIS_HOST=127.0.0.1
REDIS_PASSWORD=null
REDIS_PORT=6379

MAIL_MAILER=log
MAIL_HOST=mailpit
MAIL_PORT=1025
MAIL_USERNAME=null
MAIL_PASSWORD=null
MAIL_ENCRYPTION=null
MAIL_FROM_ADDRESS="hello@example.com"
MAIL_FROM_NAME="{site_name}"

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=
AWS_USE_PATH_STYLE_ENDPOINT=false

PUSHER_APP_ID=
PUSHER_APP_KEY=
PUSHER_APP_SECRET=
PUSHER_HOST=
PUSHER_PORT=443
PUSHER_SCHEME=https
PUSHER_APP_CLUSTER=mt1

VITE_APP_NAME="{site_name}"
VITE_PUSHER_APP_KEY="${{PUSHER_APP_KEY}}"
VITE_PUSHER_HOST="${{PUSHER_HOST}}"
VITE_PUSHER_PORT="${{PUSHER_PORT}}"
VITE_PUSHER_SCHEME="${{PUSHER_SCHEME}}"
VITE_PUSHER_CLUSTER="${{PUSHER_APP_CLUSTER}}"
"""
            
            if db_type == 'supabase':
                env_content += f"""

SUPABASE_URL={supabase_api_url}
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
"""
        else:
            db_password = self.config.get('mysql.password')
            env_content = f"""APP_NAME="{site_name}"
APP_ENV=local
APP_KEY=base64:$(php -r "echo base64_encode(random_bytes(32));")
APP_DEBUG=true
APP_URL=http://{site_name}.test

LOG_CHANNEL=stack
LOG_LEVEL=debug

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE={database_name}
DB_USERNAME=root
DB_PASSWORD={db_password}

BROADCAST_DRIVER=log
CACHE_DRIVER=file
FILESYSTEM_DISK=local
QUEUE_CONNECTION=sync
SESSION_DRIVER=file
SESSION_LIFETIME=120

REDIS_HOST=127.0.0.1
REDIS_PASSWORD=null
REDIS_PORT=6379

MAIL_MAILER=log
MAIL_HOST=mailpit
MAIL_PORT=1025
MAIL_USERNAME=null
MAIL_PASSWORD=null
MAIL_ENCRYPTION=null
MAIL_FROM_ADDRESS="hello@example.com"
MAIL_FROM_NAME="{site_name}"

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=
AWS_USE_PATH_STYLE_ENDPOINT=false

PUSHER_APP_ID=
PUSHER_APP_KEY=
PUSHER_APP_SECRET=
PUSHER_HOST=
PUSHER_PORT=443
PUSHER_SCHEME=https
PUSHER_APP_CLUSTER=mt1

VITE_APP_NAME="{site_name}"
VITE_PUSHER_APP_KEY="${{PUSHER_APP_KEY}}"
VITE_PUSHER_HOST="${{PUSHER_HOST}}"
VITE_PUSHER_PORT="${{PUSHER_PORT}}"
VITE_PUSHER_SCHEME="${{PUSHER_SCHEME}}"
VITE_PUSHER_CLUSTER="${{PUSHER_APP_CLUSTER}}"
"""
        
        with open(site_base_dir / '.env', 'w') as f:
            f.write(env_content)
        
        current_user = os.getenv('SUDO_USER') or os.getenv('USER')
        subprocess.run(['chown', '-R', f'{current_user}:www-data', str(site_base_dir)], check=True)
        subprocess.run(['chmod', '-R', '775', str(site_base_dir / 'storage')], check=True)
        subprocess.run(['chmod', '-R', '775', str(site_base_dir / 'bootstrap/cache')], check=True)
        
        return {'web_root': str(site_base_dir / 'public')}