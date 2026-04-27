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
            is_root = os.geteuid() == 0 and current_user
            
            subprocess.run(['sudo', 'chown', '-R', f'{current_user}:{current_user}', str(site_base_dir)], check=True)
            
            if is_root:
                def run_as_user(cmd, **kwargs):
                    return subprocess.run(
                        ['runuser', '-l', current_user, '-c', cmd],
                        **kwargs
                    )
            else:
                def run_as_user(cmd, **kwargs):
                    return subprocess.run(cmd, shell=True, **kwargs)
            
            run_as_user(f"npm create vite@latest . -- --template {vite_template}", 
                       cwd=str(site_base_dir), check=True, input="\nn\n", text=True)
            
            run_as_user("npm install", cwd=str(site_base_dir), check=True)
            
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


class AstroSiteCreator(SiteCreator):
    """Create an Astro project."""
    
    def __init__(self, config, site_name: str, web_root: Path, site_base_dir: Path, tld: str, 
                 proxy_port: int = None, astro_template: str = None):
        super().__init__(config, site_name, web_root, site_base_dir, tld, proxy_port)
        self.astro_template = astro_template
    
    def create(self) -> List[str]:
        """Create an Astro project."""
        messages = []
        site_name = self.site_name
        site_base_dir = self.site_base_dir
        astro_template = self.astro_template or 'basics'

        # If template is 'headless', use AstroHeadlessSiteCreator instead
        if astro_template == 'headless':
            creator = AstroHeadlessSiteCreator(
                self.config, site_name, self.web_root, site_base_dir, self.tld, self.proxy_port
            )
            return creator.create()

        try:
            current_user = os.getenv('SUDO_USER') or os.getenv('USER')
            is_root = os.geteuid() == 0 and current_user
            
            subprocess.run(['sudo', 'chown', '-R', f'{current_user}:{current_user}', str(site_base_dir)], check=True)
            
            if is_root:
                def run_as_user(cmd, **kwargs):
                    return subprocess.run(
                        ['runuser', '-l', current_user, '-c', cmd],
                        **kwargs
                    )
            else:
                def run_as_user(cmd, **kwargs):
                    return subprocess.run(cmd, shell=True, **kwargs)
            
            scaffold_cmd = f"npm create astro@latest . -- --template {astro_template} --no-install --no-git --yes"
            result = run_as_user(scaffold_cmd, cwd=str(site_base_dir), capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                scaffold_cmd = f"npm create astro@latest . --yes"
                result = run_as_user(scaffold_cmd, cwd=str(site_base_dir), input=f"{astro_template}\n\n", capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    raise Exception(f"Astro scaffolding failed: {result.stderr}")
            
            result = run_as_user("npm install", cwd=str(site_base_dir), capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise Exception(f"Astro npm install failed: {result.stderr}")
            
            pkg_path = site_base_dir / "package.json"
            if pkg_path.exists():
                with open(pkg_path, 'r') as f:
                    pkg = json.load(f)
                
                if 'scripts' not in pkg:
                    pkg['scripts'] = {}
                pkg['scripts']['dev'] = "astro dev --host"
                pkg['scripts']['build'] = "astro build"
                pkg['scripts']['preview'] = "astro preview --host"
                
                with open(pkg_path, 'w') as f:
                    json.dump(pkg, f, indent=2)
            
            result = run_as_user("npm run build", cwd=str(site_base_dir), capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise Exception(f"Astro build failed: {result.stderr}")
            
            dist_dir = site_base_dir / "dist"
            if not dist_dir.exists():
                raise Exception("Astro build did not produce dist/ directory")
            
            messages.append(f"[green]Astro ({astro_template}) project created successfully![/green]")
            messages.append(f"[green]Static site built -> dist/ ({dist_dir})[/green]")
            messages.append(f"[dim]Dev mode: npm run dev (from {site_base_dir})[/dim]")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Astro project creation failed: {str(e)}")
        
        return messages


class AstroHeadlessSiteCreator(SiteCreator):
    """Create an Astro headless project preconfigured for API-driven hydration.
    
    Generates a minimal, clean project with the island architecture pattern.
    No APIs are hardcoded — the user configures which ones they need via:
    
    1. Edit .env to set API endpoints
    2. wslaragon site api add <name> <path> <backend> to create Nginx proxies
    
    Includes:
    - .env.example with all possible API configurations (commented out)
    - .env with minimal defaults (site name + URL)
    - src/utils/api.ts — generic API client with per-endpoint configuration
    - src/components/Island.tsx — minimal example Preact island
    - src/layouts/BaseLayout.astro — responsive base layout
    - src/pages/index.astro — home page showing the pattern
    - astro.config.mjs — hybrid rendering + dev server proxy config
    """
    
    def create(self) -> List[str]:
        messages = []
        proxy_port = self.proxy_port
        site_name = self.site_name
        site_base_dir = self.site_base_dir
        tld = self.tld
        domain = f"{site_name}{tld}"
        current_user = os.getenv('SUDO_USER') or os.getenv('USER')
        
        try:
            if site_base_dir.exists():
                subprocess.run(['sudo', 'rm', '-rf', str(site_base_dir)], check=True)
            site_base_dir.mkdir(parents=True, exist_ok=True)
            
            src_dir = site_base_dir / "src"
            components_dir = src_dir / "components"
            layouts_dir = src_dir / "layouts"
            pages_dir = src_dir / "pages"
            utils_dir = src_dir / "utils"
            public_dir = site_base_dir / "public"
            
            for d in [components_dir, layouts_dir, pages_dir, utils_dir, public_dir]:
                d.mkdir(parents=True, exist_ok=True)
            
            # --- .env (minimal — user adds APIs as needed) ---
            env_content = f"""# WSLaragon Astro Headless — API Configuration
# =============================================
# PRIVATE_ vars: server-side only (build time / SSR). Never sent to browser.
# PUBLIC_ vars: embedded in client JS. Safe for islands that hydrate.
#
# Add APIs with: wslaragon site api add {site_name} <path> <backend_url>
# Example: wslaragon site api add {site_name} /api https://api.{domain}/api

SITE_NAME={site_name}
SITE_URL=https://{domain}
"""
            with open(site_base_dir / ".env", 'w') as f:
                f.write(env_content)
            
            # --- .env.example (reference with all patterns) ---
            env_example = f"""# WSLaragon Astro Headless — API Configuration Examples
# =============================================
# Copy the endpoints you need to .env and customize.
# Then add Nginx proxies: wslaragon site api add {site_name} <path> <backend_url>

# Content API (Laravel, Strapi, WordPress, etc.)
# PRIVATE_CONTENT_API_URL=https://api.{domain}/api
# PUBLIC_CONTENT_API_URL=https://{domain}/api

# Ads / Monetization API
# PRIVATE_ADS_API_URL=https://ads.{domain}/api
# PUBLIC_ADS_API_URL=https://{domain}/ads-api

# Search API (Meilisearch, Elasticsearch, FastAPI, etc.)
# PRIVATE_SEARCH_API_URL=https://search.{domain}/api
# PUBLIC_SEARCH_API_URL=https://{domain}/search-api
# PUBLIC_SEARCH_API_KEY=your-public-key

# Auth API (if needed)
# PRIVATE_AUTH_API_URL=https://auth.{domain}/api

# Analytics API (if needed)
# PRIVATE_ANALYTICS_API_URL=https://analytics.{domain}/api

SITE_NAME={site_name}
SITE_URL=https://{domain}
"""
            with open(site_base_dir / ".env.example", 'w') as f:
                f.write(env_example)
            
            # --- package.json ---
            pkg = {
                "name": site_name,
                "type": "module",
                "version": "0.0.1",
                "scripts": {
                    "dev": f"astro dev --port {proxy_port} --host",
                    "start": f"astro dev --port {proxy_port} --host",
                    "build": "astro build",
                    "preview": f"astro preview --port {proxy_port} --host",
                    "astro": "astro"
                },
                "dependencies": {
                    "astro": "^5.0.0",
                    "@astrojs/preact": "^4.0.0",
                    "preact": "^10.0.0"
                }
            }
            with open(site_base_dir / "package.json", 'w') as f:
                json.dump(pkg, f, indent=2)
            
            # --- astro.config.mjs ---
            astro_config = f"""import {{ defineConfig }} from 'astro/config';
import preact from '@astrojs/preact';

export default defineConfig({{
  output: 'hybrid',
  server: {{
    host: true,
    port: {proxy_port},
  }},
  vite: {{
    server: {{
      proxy: {{
        // Add API proxies here as you configure them.
        // Example: '/api' -> 'https://api.{domain}/api'
        // These are DEV-ONLY proxies. In production, Nginx handles routing.
        //
        // After running: wslaragon site api add {site_name} /api https://api.{domain}/api
        // Uncomment below:
        // '/api': {{
        //   target: process.env.PRIVATE_CONTENT_API_URL || 'https://api.{domain}',
        //   changeOrigin: true,
        // }},
      }},
    }},
  }},
  integrations: [preact()],
}});
"""
            with open(site_base_dir / "astro.config.mjs", 'w') as f:
                f.write(astro_config)
            
            # --- tsconfig.json ---
            tsconfig = {
                "extends": "astro/tsconfigs/base",
                "compilerOptions": {
                    "jsx": "react-jsx",
                    "jsxImportSource": "preact"
                }
            }
            with open(site_base_dir / "tsconfig.json", 'w') as f:
                json.dump(tsconfig, f, indent=2)
            
            # --- src/utils/api.ts ---
            api_utils = """/**
 * API client utilities for WSLaragon Astro Headless
 * 
 * Usage patterns:
 * 
 *   Server-side (.astro files):  const data = await fetchApi('content', '/posts');
 *   Client-side (.tsx islands):   const data = await fetchApi('content', '/posts');
 *
 * Each API endpoint is defined by a path prefix that maps to an environment variable.
 * Add new APIs by:
 *   1. Adding PUBLIC_*_API_URL to .env
 *   2. Adding the endpoint name and path here
 *   3. Running: wslaragon site api add <site> <path> <backend_url>
 */

interface ApiConfig {
  /** Path prefix used in the browser (e.g., '/api') */
  path: string;
  /** Full URL from PUBLIC_ env var, falls back to relative path */
  url: string;
}

// Registry of API endpoints.
// Add entries here when you add new APIs to .env
const API_REGISTRY: Record<string, { envKey: string; defaultPath: string }> = {
  content:  { envKey: 'PUBLIC_CONTENT_API_URL',  defaultPath: '/api' },
  ads:      { envKey: 'PUBLIC_ADS_API_URL',      defaultPath: '/ads-api' },
  search:   { envKey: 'PUBLIC_SEARCH_API_URL',   defaultPath: '/search-api' },
  auth:     { envKey: 'PUBLIC_AUTH_API_URL',      defaultPath: '/auth-api' },
  analytics:{ envKey: 'PUBLIC_ANALYTICS_API_URL',  defaultPath: '/analytics-api' },
};

// Build endpoint map from env vars (only includes configured APIs)
const endpoints: Record<string, ApiConfig> = {};
for (const [name, config] of Object.entries(API_REGISTRY)) {
  const url = import.meta.env[config.envKey] as string | undefined;
  if (url) {
    endpoints[name] = { path: config.defaultPath, url };
  }
}

export type ApiEndpoint = keyof typeof endpoints;

/**
 * Fetch from a registered API endpoint.
 * Uses relative paths in production (Nginx proxies) or full URLs from env vars.
 */
export async function fetchApi<T = unknown>(
  endpoint: ApiEndpoint,
  path: string,
  options?: RequestInit
): Promise<T> {
  const config = endpoints[endpoint];
  if (!config) {
    throw new Error(`Unknown API endpoint: ${endpoint}. Available: ${Object.keys(endpoints).join(', ')}`);
  }

  const url = config.path + path;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error (${response.status}): ${response.statusText}`);
  }

  return response.json();
}

/**
 * Server-side only fetch — uses PRIVATE_ env vars.
 * Use in .astro files for build-time data fetching.
 * This data NEVER reaches the browser.
 */
export async function fetchApiSSR<T = unknown>(
  endpoint: ApiEndpoint,
  path: string,
  options?: RequestInit
): Promise<T> {
  const privateEnvKey = API_REGISTRY[endpoint].envKey.replace('PUBLIC_', 'PRIVATE_');
  const url = import.meta.env[privateEnvKey] || process.env[privateEnvKey];
  
  if (!url) {
    throw new Error(`Private API URL not configured for ${endpoint}. Set ${privateEnvKey} in .env`);
  }

  const response = await fetch(url + path, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error (${response.status}): ${response.statusText}`);
  }

  return response.json();
}

/** Get list of configured endpoint names */
export function getConfiguredEndpoints(): string[] {
  return Object.keys(endpoints);
}
"""
            with open(utils_dir / "api.ts", 'w') as f:
                f.write(api_utils)
            
            # --- src/components/Island.tsx (minimal example island) ---
            island_content = """import { useState, useEffect } from 'preact/hooks';
import { fetchApi, type ApiEndpoint } from '../utils/api';

interface Props {
  /** API endpoint name (must be configured in .env) */
  endpoint: ApiEndpoint;
  /** API path to fetch, e.g., '/posts' or '/items/5' */
  path: string;
  /** Loading message */
  loading?: string;
  /** Fallback when no data or API not configured */
  fallback?: string;
}

/**
 * Generic island component that fetches data from any configured API.
 * Use as an example to build your own specialized islands.
 * 
 * Hydration strategies:
 *   client:load    — hydrate immediately (critical content)
 *   client:visible  — hydrate when visible in viewport (below fold)
 *   client:idle    — hydrate when browser is idle (low priority)
 *   client:only    — skip SSR, only hydrate on client
 */
export default function Island({ endpoint, path, loading = 'Cargando...', fallback = 'Sin datos' }: Props) {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchApi(endpoint, path)
      .then(setData)
      .catch(err => setError(err.message));
  }, [endpoint, path]);

  if (error) return <p class="island-error">{error}</p>;
  if (!data) return <p class="island-loading">{loading}</p>;

  return (
    <div class="island" data-endpoint={endpoint}>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
"""
            with open(components_dir / "Island.tsx", 'w') as f:
                f.write(island_content)
            
            # --- src/layouts/BaseLayout.astro ---
            layout_content = f"""---
export interface Props {{
  title: string;
  description?: string;
}}

const {{ title, description = site_name }} = Astro.props;
const siteName = import.meta.env.SITE_NAME || '{site_name}';
---
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content={{description}} />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <title>{{title}} | {{siteName}}</title>
  </head>
  <body>
    <header>
      <nav>
        <a href="/" class="logo">{{siteName}}</a>
      </nav>
    </header>
    <main>
      <slot />
    </main>
    <footer>
      <p>&copy; {{new Date().getFullYear()}} {{siteName}}</p>
    </footer>
  </body>
</html>

<style>
  :root {{
    --color-bg: #f8fafc;
    --color-text: #0f172a;
    --color-primary: #6366f1;
    --color-border: #e2e8f0;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: var(--color-bg);
    color: var(--color-text);
    line-height: 1.6;
  }}
  header {{
    border-bottom: 1px solid var(--color-border);
    padding: 1rem 2rem;
  }}
  .logo {{
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--color-primary);
    text-decoration: none;
  }}
  main {{
    max-width: 72rem;
    margin: 0 auto;
    padding: 2rem;
  }}
  footer {{
    border-top: 1px solid var(--color-border);
    padding: 2rem;
    text-align: center;
    color: #64748b;
  }}
  .island, .island-loading, .island-error {{
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
  }}
  .island {{ background: white; border: 1px solid var(--color-border); }}
  .island-loading {{ color: #94a3b8; }}
  .island-error {{ background: #fef2f2; color: #dc2626; }}
</style>
"""
            with open(layouts_dir / "BaseLayout.astro", 'w') as f:
                f.write(layout_content)
            
            # --- src/pages/index.astro ---
            index_page = f"""---
import BaseLayout from '../layouts/BaseLayout.astro';
import {{ getConfiguredEndpoints }} from '../utils/api';

const endpoints = getConfiguredEndpoints();

// Server-side data fetching example:
// Uncomment when you have a content API configured in .env
// import {{ fetchApiSSR }} from '../utils/api';
// const posts = await fetchApiSSR('content', '/posts').catch(() => []);
---

<BaseLayout title="Inicio">
  <section class="hero">
    <h1>{site_name}</h1>
    <p>Astro Headless con islas interactivas.</p>
  </section>

  <section class="setup">
    <h2>Configuración</h2>
    <p>Editá <code>.env</code> para agregar tus APIs:</p>
    <pre class="env-example">PUBLIC_CONTENT_API_URL=https://{domain}/api
# PUBLIC_ADS_API_URL=https://{domain}/ads-api
# PUBLIC_SEARCH_API_URL=https://{domain}/search-api</pre>

    <p>Luego agregá los proxies de Nginx:</p>
    <pre class="cmd-example">wslaragon site api add {site_name} /api https://api.{domain}/api
# wslaragon site api add {site_name} /search-api https://search.{domain}/api</pre>

    {{endpoints.length > 0 ? (
      <p class="endpoints-active">✓ APIs configuradas: {{endpoints.join(', ')}}</p>
    ) : (
      <p class="endpoints-empty">Ninguna API configurada aún. Agregá endpoints en .env y ejecutá <code>wslaragon site api add</code></p>
    )}}
  </section>

  <section class="pattern">
    <h2>Patrón de Islas</h2>
    <div class="pattern-grid">
      <div class="pattern-card">
        <h3>Build Time (0 JS)</h3>
        <p>Datos obtenidos en el servidor. El HTML se genera estático.</p>
        <pre>const data = await fetchApiSSR('content', '/posts');</pre>
      </div>
      <div class="pattern-card">
        <h3>Hidratación (client:*)</h3>
        <p>Componentes Preact que se hidratan en el navegador.</p>
        <pre>&lt;Island client:visible endpoint="content" path="/posts" /&gt;</pre>
      </div>
    </div>
  </section>
</BaseLayout>

<style>
  .hero {{
    text-align: center;
    padding: 3rem 0;
  }}
  .hero h1 {{
    font-size: 2.5rem;
    color: var(--color-primary);
  }}
  .setup {{
    background: white;
    padding: 2rem;
    border-radius: 0.5rem;
    border: 1px solid var(--color-border);
    margin-bottom: 2rem;
  }}
  .env-example, .cmd-example {{
    background: #0f172a;
    color: #e2e8f0;
    padding: 1rem;
    border-radius: 0.5rem;
    overflow-x: auto;
    font-size: 0.875rem;
  }}
  .endpoints-active {{
    color: #16a34a;
    font-weight: 600;
  }}
  .endpoints-empty {{
    color: #94a3b8;
  }}
  .pattern-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }}
  .pattern-card {{
    padding: 1.5rem;
    border: 1px solid var(--color-border);
    border-radius: 0.5rem;
  }}
  .pattern-card h3 {{
    color: var(--color-primary);
    margin-bottom: 0.5rem;
  }}
  .pattern-card pre {{
    background: #0f172a;
    color: #e2e8f0;
    padding: 0.75rem;
    border-radius: 0.375rem;
    font-size: 0.8rem;
    overflow-x: auto;
  }}
  @media (max-width: 768px) {{
    .pattern-grid {{
      grid-template-columns: 1fr;
    }}
  }}
</style>
"""
            with open(pages_dir / "index.astro", 'w') as f:
                f.write(index_page)
            
            # --- public/favicon.svg ---
            favicon = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36"><text y="32" font-size="32">⚡</text></svg>"""
            with open(public_dir / "favicon.svg", 'w') as f:
                f.write(favicon)
            
            # Install dependencies
            if os.geteuid() == 0 and current_user:
                result = subprocess.run(
                    ['runuser', '-l', current_user, '-c', 'npm install'],
                    cwd=str(site_base_dir), capture_output=True, text=True, timeout=180
                )
            else:
                result = subprocess.run(['npm', 'install'], cwd=str(site_base_dir), capture_output=True, text=True, timeout=180)
            if result.returncode != 0:
                messages.append(f"[yellow]npm install had warnings[/yellow]")
            
            # Build static site
            if os.geteuid() == 0 and current_user:
                build_result = subprocess.run(
                    ['runuser', '-l', current_user, '-c', 'npm run build'],
                    cwd=str(site_base_dir), capture_output=True, text=True, timeout=120
                )
            else:
                build_result = subprocess.run(['npm', 'run', 'build'], cwd=str(site_base_dir), capture_output=True, text=True, timeout=120)
            
            dist_dir = site_base_dir / "dist"
            if build_result.returncode != 0 or not dist_dir.exists():
                messages.append(f"[yellow]Build failed — run 'npm run build' manually from {site_base_dir}[/yellow]")
            else:
                messages.append(f"[green]Static site built -> dist/ ({dist_dir})[/green]")
            
            # Set permissions
            subprocess.run(['sudo', 'chown', '-R', f'{current_user}:www-data', str(site_base_dir)], check=True)
            
            messages.append(f"[green]Astro Headless project created successfully![/green]")
            messages.append(f"[yellow]Edit .env to configure your API endpoints[/yellow]")
            messages.append(f"[yellow]Add API proxies: wslaragon site api add {site_name} /api https://api.{domain}/api[/yellow]")
            messages.append(f"[dim]Dev mode: npm run dev (from {site_base_dir})[/dim]")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Astro Headless project creation failed: {str(e)}")
        
        return messages


class PhpMyAdminSiteCreator(SiteCreator):
    """Create a phpMyAdmin site for database management."""
    
    def create(self) -> List[str]:
        """Download and install phpMyAdmin."""
        web_root = self.web_root
        site_name = self.site_name
        current_user = os.getenv('SUDO_USER') or os.getenv('USER')
        
        # Download phpMyAdmin
        pma_version = '5.2.2'
        pma_tar_path = f'/tmp/phpMyAdmin-{site_name}.tar.xz'
        pma_url = f'https://files.phpmyadmin.net/phpMyAdmin/{pma_version}/phpMyAdmin-{pma_version}-all-languages.tar.xz'
        
        # Download
        result = subprocess.run(
            ['wget', '-q', '-O', pma_tar_path, pma_url],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            # Fallback to .tar.gz
            pma_url_gz = f'https://files.phpmyadmin.net/phpMyAdmin/{pma_version}/phpMyAdmin-{pma_version}-all-languages.tar.gz'
            result = subprocess.run(
                ['wget', '-q', '-O', pma_tar_path, pma_url_gz],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(f"Failed to download phpMyAdmin: {result.stderr}")
        
        # Extract
        result = subprocess.run(
            ['tar', '-xf', pma_tar_path, '-C', '/tmp'],
            capture_output=True, text=True,
            cwd='/tmp'
        )
        if result.returncode != 0:
            raise Exception(f"Failed to extract phpMyAdmin: {result.stderr}")
        
        # Find extracted directory
        pma_extracted = Path(f'/tmp/phpMyAdmin-{pma_version}-all-languages')
        if not pma_extracted.exists():
            # Try to find it
            pma_dirs = list(Path('/tmp').glob('phpMyAdmin-*-all-languages'))
            if pma_dirs:
                pma_extracted = pma_dirs[0]
            else:
                raise Exception("Could not find extracted phpMyAdmin directory")
        
        # Clear web_root and copy files
        if web_root.exists():
            shutil.rmtree(str(web_root))
        
        subprocess.run(['cp', '-r', f'{pma_extracted}/.', str(web_root)], check=True)
        subprocess.run(['rm', '-rf', str(pma_extracted)], check=False)
        subprocess.run(['rm', '-f', pma_tar_path], check=False)
        
        # Set permissions
        subprocess.run(['sudo', 'chown', '-R', f'{current_user}:www-data', str(web_root)], check=True)
        subprocess.run(['sudo', 'chmod', '-R', '755', str(web_root)], check=True)
        
        # Create blowfish_secret for cookie auth
        blowfish_secret = secrets.token_urlsafe(32)
        
        # Get MySQL credentials from config
        db_password = self.config.get('mysql.password', '')
        db_user = self.config.get('mysql.user', 'root')
        
        # Create config.inc.php
        config_content = f"""<?php
/**
 * phpMyAdmin configuration - auto-generated by WSLaragon
 */

// Authentication type
$cfg['Servers'][1]['auth_type'] = 'cookie';

// Server settings
$cfg['Servers'][1]['host'] = 'localhost';
$cfg['Servers'][1]['port'] = '3306';
$cfg['Servers'][1]['connect_type'] = 'tcp';
$cfg['Servers'][1]['compress'] = false;
$cfg['Servers'][1]['AllowNoPassword'] = false;

// Blowfish secret for cookie encryption
$cfg['blowfish_secret'] = '{blowfish_secret}';

// Upload directory
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';

// Temp directory
$cfg['TempDir'] = '/tmp/';

// Default language
$cfg['DefaultLang'] = 'es';

// Max rows to display
$cfg['MaxRows'] = 30;

// Allow login without password on localhost (development)
$cfg['Servers'][1]['AllowNoPassword'] = true;

// Navigation settings
$cfg['NavigationDBSeparator'] = '_';

// Hide databases pattern (system databases)
// $cfg['Servers'][1]['hide_db'] = '^(information_schema|performance_schema|mysql|sys)$';
?>"""
        
        with open(web_root / "config.inc.php", 'w') as f:
            f.write(config_content)
        
        # Create tmp directory for phpMyAdmin
        tmp_dir = web_root / 'tmp'
        tmp_dir.mkdir(exist_ok=True)
        subprocess.run(['sudo', 'chown', '-R', f'www-data:www-data', str(tmp_dir)], check=False)
        
        return [f"[green]phpMyAdmin {pma_version} installed successfully![/green]",
                f"[yellow]Access at: https://{site_name}{self.tld}[/yellow]"]


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
                      database_name: str = None, astro_template: str = None) -> Optional[SiteCreator]:
    """Factory function to get the appropriate site creator."""
    if vite_template:
        return ViteSiteCreator(config, site_name, web_root, site_base_dir, tld, proxy_port, vite_template=vite_template)
    elif astro_template:
        return AstroSiteCreator(config, site_name, web_root, site_base_dir, tld, proxy_port, astro_template=astro_template)
    elif site_type == 'html':
        return HtmlSiteCreator(config, site_name, web_root, site_base_dir, tld)
    elif site_type == 'wordpress':
        return WordPressSiteCreator(config, site_name, web_root, site_base_dir, tld)
    elif site_type == 'phpmyadmin':
        return PhpMyAdminSiteCreator(config, site_name, web_root, site_base_dir, tld)
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