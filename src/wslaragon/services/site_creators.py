"""Site creator strategies for different site types."""
import json
import logging
import os
import subprocess
import base64
import secrets
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SiteCreator(ABC):
    """Abstract base class for site creation strategies."""
    
    def __init__(self, config, site_name: str, web_root: Path, site_base_dir: Path, tld: str, proxy_port: int = None):
        self.config = config
        self.site_name = site_name
        self.web_root = web_root
        self.site_base_dir = site_base_dir
        self.tld = tld
        self.proxy_port = proxy_port
    
    @abstractmethod
    def create(self) -> List[str]:
        """Create the site scaffolding. Returns list of message strings."""
        pass


class HtmlSiteCreator(SiteCreator):
    """Create a static HTML site with styles and js folders."""
    
    def create(self) -> List[str]:
        """Create a static HTML site with styles and js folders."""
        web_root = self.web_root
        site_name = self.site_name
        
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
            <p>Este es un proyecto HTML estatico listo para desarrollar.</p>
        </section>
        <section class="features">
            <article>
                <h3>Rapido</h3>
                <p>Sitio web estatico de alto rendimiento.</p>
            </article>
            <article>
                <h3>Moderno</h3>
                <p>Con estructura CSS y JavaScript lista.</p>
            </article>
            <article>
                <h3>Facil</h3>
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
        
        return []


class WordPressSiteCreator(SiteCreator):
    """Create a WordPress site."""
    
    def create(self) -> List[str]:
        """Create a WordPress site."""
        web_root = self.web_root
        site_name = self.site_name
        db_password = self.config.get('mysql.password')
        current_user = os.getenv('SUDO_USER') or os.getenv('USER')
        
        if web_root.exists():
            shutil.rmtree(str(web_root))
        
        web_root.mkdir(parents=True)
        
        wp_tar_path = f'/tmp/wordpress-{site_name}.tar.gz'
        subprocess.run(['wget', '-q', '-O', wp_tar_path, 'https://wordpress.org/latest.tar.gz'], check=True)
        subprocess.run(['sudo', 'tar', '-xzf', wp_tar_path, '-C', str(web_root.parent)], check=True)
        
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
define( 'FS_METHOD', 'direct' );

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
        
        return []


class LaravelSiteCreator(SiteCreator):
    """Create a Laravel site."""
    
    def __init__(self, config, site_name: str, web_root: Path, site_base_dir: Path, tld: str, 
                 proxy_port: int = None, version: int = 12, db_type: str = None, database_name: str = None):
        super().__init__(config, site_name, web_root, site_base_dir, tld, proxy_port)
        self.version = version
        self.db_type = db_type
        self.database_name = database_name
    
    def create(self) -> List[str]:
        """Create a Laravel site with PostgreSQL or Supabase support."""
        messages = []
        site_base_dir = self.site_base_dir
        site_name = self.site_name
        version = self.version
        db_type = self.db_type
        database_name = self.database_name
        
        if not database_name:
            database_name = f"{site_name}_db"
        
        postgres_port = self.config.get('supabase.postgres_port', 5433)
        postgres_password = self.config.get('supabase.postgres_password', 'postgres')
        
        supabase_api_url = f"http://localhost:{self.config.get('supabase.api_port', 8081)}"
        
        current_user = os.getenv('SUDO_USER') or os.getenv('USER')
        exec_cmd_prefix = []
        if os.geteuid() == 0 and current_user:
            exec_cmd_prefix = ['sudo', '-u', current_user]

        composer_project_cmd = exec_cmd_prefix + [
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
                composer_retry_cmd = exec_cmd_prefix + [
                    'composer', 'create-project',
                    f'laravel/laravel:^{version}.0',
                    str(site_base_dir),
                    '--no-interaction',
                    '--no-progress'
                ]
                subprocess.run(composer_retry_cmd, env=env, check=True)
            else:
                raise Exception(f"Laravel installation failed: {result.stderr}")
        
        app_key = f"base64:{base64.b64encode(secrets.token_bytes(32)).decode()}"
        
        if db_type in ('postgres', 'supabase'):
            env_content = f"""APP_NAME="{site_name}"
APP_ENV=local
APP_KEY={app_key}
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
APP_KEY={app_key}
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
        subprocess.run(['sudo', 'chown', '-R', f'{current_user}:www-data', str(site_base_dir)], check=True)
        subprocess.run(['sudo', 'chmod', '-R', '775', str(site_base_dir / 'storage')], check=True)
        subprocess.run(['sudo', 'chmod', '-R', '775', str(site_base_dir / 'bootstrap/cache')], check=True)
        
        messages.append(f"[green]Laravel {version} installed successfully![/green]")
        if db_type in ('postgres', 'supabase'):
            messages.append(f"[yellow]Configured for PostgreSQL/Supabase[/yellow]")
        
        return messages


class NodeSiteCreator(SiteCreator):
    """Create a Node.js app."""
    
    def create(self) -> List[str]:
        """Create a Node.js app."""
        messages = []
        proxy_port = self.proxy_port
        site_name = self.site_name
        site_base_dir = self.site_base_dir
        
        app_content = f"""
const http = require('http');
const port = process.env.PORT || {proxy_port};

const server = http.createServer((req, res) => {{
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/html');
  res.end('<h1>Hello from Node.js!</h1><p>Served via PM2 on port ' + port + '</p>');
}});

server.listen(port, () => {{
  console.log(`Server running at http://localhost:${{port}}/`);
}});
"""
        with open(site_base_dir / "app.js", 'w') as f:
            f.write(app_content.strip())
        
        package_json = {
            "name": site_name,
            "version": "1.0.0",
            "main": "app.js",
            "scripts": {
                "start": f"node app.js"
            }
        }
        with open(site_base_dir / "package.json", 'w') as f:
            json.dump(package_json, f, indent=2)

        messages.append(f"[yellow]Node.js app prepared on port {proxy_port}. Run 'pm2 start app.js --name {site_name}' to start it.[/yellow]")
        
        return messages


class PythonSiteCreator(SiteCreator):
    """Create a Python app."""
    
    def create(self) -> List[str]:
        """Create a Python app."""
        messages = []
        proxy_port = self.proxy_port
        site_base_dir = self.site_base_dir
        
        app_content = f"""
import http.server
import socketserver
import os

PORT = int(os.environ.get('PORT', {proxy_port}))

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
"""
        with open(site_base_dir / "main.py", 'w') as f:
            f.write(app_content.strip())
        messages.append(f"[yellow]Python script prepared on port {proxy_port}. Run 'python3 main.py' to test.[/yellow]")
        
        return messages


class ViteSiteCreator(SiteCreator):
    """Create a Vite project."""
    
    def __init__(self, config, site_name: str, web_root: Path, site_base_dir: Path, tld: str, 
                 proxy_port: int = None, vite_template: str = None):
        super().__init__(config, site_name, web_root, site_base_dir, tld, proxy_port)
        self.vite_template = vite_template
    
    def create(self) -> List[str]:
        """Create a Vite project."""
        messages = []
        proxy_port = self.proxy_port
        site_name = self.site_name
        site_base_dir = self.site_base_dir
        vite_template = self.vite_template
        
        try:
            current_user = os.getenv('SUDO_USER') or os.getenv('USER')
            
            subprocess.run(['sudo', 'chown', '-R', f'{current_user}:{current_user}', str(site_base_dir)], check=True)
            
            npm_path = shutil.which('npm')
            
            if not npm_path:
                if os.geteuid() == 0 and current_user:
                    try:
                        res = subprocess.run(['runuser', '-l', current_user, '-c', 'which npm'], capture_output=True, text=True)
                        if res.returncode == 0:
                            npm_path = res.stdout.strip()
                    except:
                        pass
            
            if not npm_path:
                npm_path = "npm"

            exec_cmd_prefix = []
            if os.geteuid() == 0 and current_user:
                exec_cmd_prefix = ['sudo', '-u', current_user]
            
            full_cmd_create = exec_cmd_prefix + [npm_path, 'create', 'vite@latest', '.', '--', '--template', vite_template]
            subprocess.run(full_cmd_create, cwd=str(site_base_dir), check=True, input="\nn\n", text=True)
            
            full_cmd_install = exec_cmd_prefix + [npm_path, 'install']
            subprocess.run(full_cmd_install, cwd=str(site_base_dir), check=True)
            
            pkg_path = site_base_dir / "package.json"
            with open(pkg_path, 'r') as f:
                pkg = json.load(f)
            
            if 'scripts' in pkg:
                pkg['scripts']['dev'] = f"vite --port {proxy_port} --host"
                pkg['scripts']['start'] = f"vite --port {proxy_port} --host"
            
            with open(pkg_path, 'w') as f:
                json.dump(pkg, f, indent=2)
                
            for cfg_file in ['vite.config.js', 'vite.config.ts']:
                cfg_path = site_base_dir / cfg_file
                if cfg_path.exists():
                    with open(cfg_path, 'r') as f:
                        content = f.read()
                    
                    if 'defineConfig({' in content and 'allowedHosts' not in content:
                        new_content = content.replace('defineConfig({', 'defineConfig({\n  server: {\n    allowedHosts: true\n  },')
                        with open(cfg_path, 'w') as f:
                            f.write(new_content)
                    break

            messages.append(f"[green]Vite ({vite_template}) project created successfully![/green]")
            messages.append(f"[yellow]Node process prepared. Run 'wslaragon node start {site_name}' to serve 'npm run dev'.[/yellow]")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Vite scaffolding failed: {str(e)}")
        
        return messages


class DefaultSiteCreator(SiteCreator):
    """Create a default PHP or static site."""
    
    def __init__(self, config, site_name: str, web_root: Path, site_base_dir: Path, tld: str, 
                 proxy_port: int = None, php: bool = True):
        super().__init__(config, site_name, web_root, site_base_dir, tld, proxy_port)
        self.php = php
    
    def create(self) -> List[str]:
        """Create a default PHP or static site."""
        messages = []
        web_root = self.web_root
        site_name = self.site_name
        tld = self.tld
        php = self.php
        
        index_file = web_root / "index.php" if php else web_root / "index.html"
        
        if php:
            index_content = f"""<?php
echo "<h1>Welcome to {site_name}{tld}!</h1>";
echo "<p>PHP Version: " . phpversion() . "</p>";
echo "<p>Server Time: " . date('Y-m-d H:i:s') . "</p>";
phpinfo();
?>"""
        else:
            index_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Welcome to {site_name}{tld}!</title>
</head>
<body>
    <h1>Welcome to {site_name}{tld}!</h1>
    <p>Static site is working!</p>
</body>
</html>"""
        
        with open(index_file, 'w') as f:
            f.write(index_content)
        
        return messages


def get_site_creator(site_type: Optional[str], vite_template: Optional[str], php: bool, 
                      config, site_name: str, web_root: Path, site_base_dir: Path, 
                      tld: str, proxy_port: int = None, 
                      version: int = None, db_type: str = None, 
                      database_name: str = None) -> Optional[SiteCreator]:
    """Factory function to get the appropriate site creator."""
    if vite_template:
        return ViteSiteCreator(config, site_name, web_root, site_base_dir, tld, proxy_port, vite_template=vite_template)
    elif site_type == 'html':
        return HtmlSiteCreator(config, site_name, web_root, site_base_dir, tld)
    elif site_type == 'wordpress':
        return WordPressSiteCreator(config, site_name, web_root, site_base_dir, tld)
    elif site_type is not None and (site_type == 'laravel' or site_type.isdigit()):
        laravel_version = int(site_type) if site_type.isdigit() else version or 12
        return LaravelSiteCreator(config, site_name, web_root, site_base_dir, tld,
                                  proxy_port=proxy_port, version=laravel_version, 
                                  db_type=db_type, database_name=database_name)
    elif site_type == 'node':
        return NodeSiteCreator(config, site_name, web_root, site_base_dir, tld, proxy_port)
    elif site_type == 'python':
        return PythonSiteCreator(config, site_name, web_root, site_base_dir, tld, proxy_port)
    else:
        return DefaultSiteCreator(config, site_name, web_root, site_base_dir, tld, php=php)