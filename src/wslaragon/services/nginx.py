import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class NginxManager:
    def __init__(self, config):
        self.config = config
        self.config_dir = Path(config.get('nginx.config_dir'))
        self.sites_available = Path(config.get('nginx.sites_available'))
        self.sites_enabled = Path(config.get('nginx.sites_enabled'))
        self.tld = config.get('sites.tld', '.test')
    
    def _normalize_site_name(self, site_name: str) -> str:
        """Strip the TLD suffix if included in the site name."""
        if site_name.endswith(self.tld):
            site_name = site_name[:-len(self.tld)]
        return site_name
    
    def test_config(self) -> bool:
        """Test Nginx configuration"""
        try:
            result = subprocess.run(
                ['sudo', 'nginx', '-t'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"test_config failed: {e}")
            return False
    
    def reload(self) -> bool:
        """Reload Nginx configuration"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'reload', 'nginx'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"reload failed: {e}")
            return False
    
    def restart(self) -> bool:
        """Restart Nginx service"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'nginx'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"restart failed: {e}")
            return False
    
    def create_site_config(self, site_name: str, document_root: str, 
                          ssl: bool = False, php: bool = True, proxy_port: int = None,
                          api_proxies: Dict[str, str] = None) -> str:
        """Generate Nginx site configuration"""
        site_name = self._normalize_site_name(site_name)
        domain = f"{site_name}{self.tld}"
        api_proxies = api_proxies or {}
        
        # Build API proxy location blocks
        # Nginx needs variable-based proxy_pass for dynamic DNS resolution
        # of .test domains (resolved via /etc/hosts at runtime)
        api_proxy_config = ""
        for path, backend in api_proxies.items():
            # Extract host and port from backend URL
            from urllib.parse import urlparse
            parsed = urlparse(backend)
            backend_host = parsed.hostname or backend
            backend_port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            backend_scheme = parsed.scheme or 'https'
            
            # Nginx requires a variable for dynamic DNS resolution
            # We use set directive to store the backend URL
            var_name = path.replace('/', '').replace('-', '_')
            api_proxy_config += f"""
    # API proxy: {path} -> {backend}
    set $backend_{var_name} {backend_scheme}://{backend_host}:{backend_port};
    location {path}/ {{
        proxy_pass $backend_{var_name};
        proxy_http_version 1.1;
        proxy_set_header Host {backend_host};
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Accept "application/json";
        proxy_ssl_server_name on;
        client_max_body_size 128M;
    }}
"""
        
# Proxy configuration (Exclusive: overrides PHP/Static logic)
        if proxy_port:
            common_config = f"""{api_proxy_config}
    # Dev server proxy
    location / {{
        proxy_pass http://127.0.0.1:{proxy_port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        client_max_body_size {self.config.get('nginx.client_max_body_size', '128M')};
    }}"""
        else:
            # PHP-FPM part
            php_config = ""
            if php:
                php_config = f"""
    location ~ \\.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php{self.config.get('php.version')}-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        client_max_body_size 128M;
    }}"""

            # Common configuration elements
            common_config = f"""
    root {document_root};
    index index.php index.html index.htm;
    client_max_body_size {self.config.get('nginx.client_max_body_size', '128M')};

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval'" always;

    # Handle static files — try_files evita 404 en rutas PHP con extensión .js/.css (ej: /livewire/livewire.js)
    location ~* \\.(jpg|jpeg|png|gif|ico|css|js|svg|woff2)$ {{
        try_files $uri /index.php?$query_string;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
{php_config}
    # Error pages
    location = /favicon.ico {{ access_log off; log_not_found off; }}
    location = /robots.txt {{ access_log off; log_not_found off; }}

    location / {{
        try_files $uri $uri/ /index.php?$query_string;
    }}

    # Error handling
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {{
        root /usr/share/nginx/html;
    }}"""

        if ssl:
            config = f"""server {{
    listen 80;
    listen [::]:80;
    server_name {domain};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {domain};
{common_config}

    # SSL configuration
    ssl_certificate {self.config.get('ssl.dir')}/{domain}.pem;
    ssl_certificate_key {self.config.get('ssl.dir')}/{domain}-key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}}"""
        else:
            config = f"""server {{
    listen 80;
    server_name {domain};
{common_config}
}}"""
        
        return config.strip()
    
    def add_site(self, site_name: str, document_root: str, 
                ssl: bool = False, php: bool = True, proxy_port: int = None,
                api_proxies: Dict[str, str] = None) -> Tuple[bool, Optional[str]]:
        """Add a new site configuration"""
        try:
            config_content = self.create_site_config(
                site_name, document_root, ssl, php, proxy_port,
                api_proxies=api_proxies
            )
            
            site_name = self._normalize_site_name(site_name)
            domain = f"{site_name}{self.tld}"
            config_file = self.sites_available / f"{domain}.conf"
            
            # Write configuration using sudo tee
            process = subprocess.Popen(['sudo', 'tee', str(config_file)], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, 
                                     text=True)
            stdout, stderr = process.communicate(input=config_content)
            
            if process.returncode != 0:
                return False, f"Failed to write config: {stderr}"
            
            # Enable site
            success, error = self.enable_site(site_name)
            if not success:
                return False, error
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    def enable_site(self, site_name: str) -> Tuple[bool, Optional[str]]:
        """Enable a site"""
        try:
            site_name = self._normalize_site_name(site_name)
            domain = f"{site_name}{self.tld}"
            source = self.sites_available / f"{domain}.conf"
            target = self.sites_enabled / f"{domain}.conf"
            
            # Create symbolic link
            subprocess.run(['sudo', 'ln', '-sf', str(source), str(target)], check=True, capture_output=True, text=True)
            
            # Test and reload
            if self.test_config():
                if self.reload():
                    return True, None
                else:
                    return False, "Failed to reload Nginx"
            else:
                # Get Nginx test error
                result = subprocess.run(['sudo', 'nginx', '-t'], capture_output=True, text=True)
                # Remove broken link
                subprocess.run(['sudo', 'rm', '-f', str(target)])
                return False, f"Nginx configuration test failed: {result.stderr}"
        except subprocess.CalledProcessError as e:
            return False, f"Process error: {e.stderr}"
        except Exception as e:
            return False, str(e)
    
    def disable_site(self, site_name: str) -> bool:
        """Disable a site"""
        try:
            site_name = self._normalize_site_name(site_name)
            domain = f"{site_name}{self.tld}"
            config_file = self.sites_enabled / f"{domain}.conf"
            subprocess.run(['sudo', 'rm', '-f', str(config_file)], check=True)
            return self.reload()
        except Exception as e:
            logger.debug(f"disable_site failed: {e}")
            return False
    
    def remove_site(self, site_name: str) -> bool:
        """Remove a site completely"""
        try:
            site_name = self._normalize_site_name(site_name)
            domain = f"{site_name}{self.tld}"
            
            # Disable first
            self.disable_site(site_name)
            
            # Remove configuration file
            config_file = self.sites_available / f"{domain}.conf"
            subprocess.run(['sudo', 'rm', '-f', str(config_file)], check=True)
            
            return True
        except Exception as e:
            logger.debug(f"remove_site failed: {e}")
            return False
    
    def list_sites(self) -> Dict[str, Dict]:
        """List all sites and their status"""
        sites = {}
        
        # Get available sites
        for config_file in self.sites_available.glob("*.conf"):
            site_name = config_file.stem
            sites[site_name] = {
                'available': True,
                'enabled': (self.sites_enabled / f"{site_name}.conf").exists(),
                'config_file': str(config_file)
            }
        
        return sites
    
    def get_site_config(self, site_name: str) -> Optional[str]:
        """Get site configuration content"""
        try:
            config_file = self.sites_available / f"{site_name}.conf"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return f.read()
        except Exception as e:
            logger.debug(f"get_site_config failed: {e}")
            pass
        return None