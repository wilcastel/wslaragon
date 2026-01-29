import yaml
import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # Load environment variables from .env file in project root
        project_root = Path(__file__).parents[3]
        load_dotenv(dotenv_path=project_root / ".env")
        
        self.config_dir = Path.home() / ".wslaragon"
        self.config_file = self.config_dir / "config.yaml"
        self.sites_dir = self.config_dir / "sites"
        self.ssl_dir = self.config_dir / "ssl"
        self.logs_dir = self.config_dir / "logs"
        
        self._ensure_dirs()
        self._load_config()
    
    def _ensure_dirs(self):
        for dir_path in [self.config_dir, self.sites_dir, self.ssl_dir, self.logs_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def _load_config(self):
        default_document_root = os.getenv('DOCUMENT_ROOT', str(Path.home() / "web"))
        
        default_config = {
            "php": {
                "version": "8.3",
                "ini_file": "/etc/php/8.3/fpm/php.ini",
                "extensions_dir": "/usr/lib/php/20230831"
            },
            "nginx": {
                "config_dir": "/etc/nginx",
                "sites_available": "/etc/nginx/sites-available",
                "sites_enabled": "/etc/nginx/sites-enabled",
                "client_max_body_size": "128M"
            },
            "mysql": {
                "data_dir": "/var/lib/mysql",
                "config_file": "/etc/mysql/mariadb.conf.d/50-server.cnf",
                "user": os.getenv('DB_USER', 'root'),
                "password": os.getenv('DB_PASSWORD', '')
            },
            "ssl": {
                "dir": str(self.ssl_dir),
                "ca_file": str(self.ssl_dir / "rootCA.pem"),
                "ca_key": str(self.ssl_dir / "rootCA-key.pem")
            },
            "sites": {
                "tld": ".test",
                "document_root": default_document_root
            },
            "windows": {
                "hosts_file": "/mnt/c/Windows/System32/drivers/etc/hosts"
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
                
                # Ensure new keys from .env are respected even if config.yaml exists
                if 'mysql' in self.config:
                    if os.getenv('DB_USER'):
                        self.config['mysql']['user'] = os.getenv('DB_USER')
                    if os.getenv('DB_PASSWORD'):
                        self.config['mysql']['password'] = os.getenv('DB_PASSWORD')
        else:
            self.config = default_config
            self.save()
    
    def save(self):
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key, value):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if isinstance(config, dict):
                config = config.setdefault(k, {})
            else:
                break
        if isinstance(config, dict):
            config[keys[-1]] = value
        self.save()