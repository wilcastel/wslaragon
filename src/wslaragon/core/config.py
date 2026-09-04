import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .platform import detect_platform, platform_defaults


def _deep_merge(defaults, overrides):
    """Merge user configuration onto defaults without losing new keys."""
    result = defaults.copy()
    for key, value in (overrides or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

class Config:
    def __init__(self):
        # Load environment variables from .env file in project root
        project_root = Path(__file__).parents[3]
        load_dotenv(dotenv_path=project_root / ".env")
        
        # Use SUDO_USER's home directory when running with sudo,
        # otherwise use the current user's home
        sudo_user = os.getenv('SUDO_USER')
        if sudo_user:
            import pwd
            try:
                self.home_dir = Path(pwd.getpwnam(sudo_user).pw_dir)
            except (KeyError, ImportError):
                self.home_dir = Path.home()
        else:
            self.home_dir = Path.home()
        
        self.config_dir = self.home_dir / ".wslaragon"
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
        default_document_root = os.getenv('DOCUMENT_ROOT', str(self.home_dir / "web"))
        
        default_config = platform_defaults(detect_platform(), self.home_dir)
        default_config["sites"]["document_root"] = default_document_root
        default_config["mysql"]["user"] = os.getenv('DB_USER', 'root')
        default_config["mysql"]["password"] = os.getenv('DB_PASSWORD', '')
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = _deep_merge(default_config, yaml.safe_load(f) or {})
                
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
