import subprocess
import os
from pathlib import Path
from typing import Dict, List, Optional

class SSLManager:
    def __init__(self, config):
        self.config = config
        self.ssl_dir = Path(config.get('ssl.dir'))
        self.ca_file = Path(config.get('ssl.ca_file'))
        self.ca_key = Path(config.get('ssl.ca_key'))
        self.windows_hosts = Path(config.get('windows.hosts_file'))
        
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Ensure SSL directory exists"""
        self.ssl_dir.mkdir(exist_ok=True, parents=True)
    
    def is_mkcert_installed(self) -> bool:
        """Check if mkcert is installed"""
        try:
            result = subprocess.run(
                ['mkcert', '-version'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def install_mkcert(self) -> bool:
        """Install mkcert"""
        try:
            # Download and install mkcert
            subprocess.run([
                'curl', '-L', 'https://dl.filippo.io/mkcert/latest?for=linux/amd64',
                '-o', '/tmp/mkcert'
            ], check=True)
            
            subprocess.run(['chmod', '+x', '/tmp/mkcert'], check=True)
            subprocess.run(['sudo', 'mv', '/tmp/mkcert', '/usr/local/bin/'], check=True)
            
            # Install local CA
            subprocess.run(['mkcert', '-install'], check=True)
            
            return True
        except Exception:
            return False
    
    def create_ca(self) -> bool:
        """Create Certificate Authority"""
        try:
            if not self.is_mkcert_installed():
                if not self.install_mkcert():
                    return False
            
            # Install local CA (this creates the CA files)
            subprocess.run(['mkcert', '-install'], check=True)
            
            # Copy CA files to our SSL directory
            caroot_path = self._get_caroot_path()
            if caroot_path:
                ca_pem = Path(caroot_path) / "rootCA.pem"
                ca_key = Path(caroot_path) / "rootCA-key.pem"
                
                if ca_pem.exists():
                    subprocess.run(['cp', str(ca_pem), str(self.ca_file)], check=True)
                if ca_key.exists():
                    subprocess.run(['cp', str(ca_key), str(self.ca_key)], check=True)
                
                return True
            
            return False
        except Exception:
            return False
    
    def _get_caroot_path(self) -> Optional[str]:
        """Get mkcert CARoot path"""
        try:
            result = subprocess.run(
                ['mkcert', '-CAROOT'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def generate_certificate(self, domain: str, additional_domains: List[str] = None) -> bool:
        """Generate SSL certificate for domain"""
        try:
            if not self.is_mkcert_installed():
                return False
            
            cert_file = self.ssl_dir / f"{domain}.pem"
            key_file = self.ssl_dir / f"{domain}-key.pem"
            
            # Build domain list
            domains = [domain]
            if additional_domains:
                domains.extend(additional_domains)
            
            # Generate certificate
            subprocess.run(['mkcert'] + domains, check=True)
            
            # Move generated files to our SSL directory
            for file_path in Path('.').glob(f"{domain}*"):
                if file_path.is_file():
                    target = self.ssl_dir / file_path.name
                    subprocess.run(['mv', str(file_path), str(target)], check=True)
            
            return cert_file.exists() and key_file.exists()
        except Exception:
            return False

    def generate_cert(self, domain: str) -> Dict:
        """Wrapper for generate_certificate that returns a DictResult for the CLI"""
        try:
            if self.generate_certificate(domain):
                # Also attempt to add to windows hosts for convenience
                self.add_to_windows_hosts(domain)
                return {'success': True}
            else:
                return {'success': False, 'error': 'Failed to generate certificate (check if mkcert is installed)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_to_windows_hosts(self, domain: str, ip: str = "127.0.0.1") -> bool:
        """Add domain to Windows hosts file using PowerShell (handles elevation)"""
        try:
            # Check if entry already exists (read-only is usually fine)
            if self.windows_hosts.exists():
                with open(self.windows_hosts, 'r') as f:
                    if domain in f.read():
                        return True
            
            # Use PowerShell to add entries with elevated privileges
            # We add both IPv4 and IPv6 entries for better compatibility
            # We use `r`n for Windows-style newlines and clean up previous malformed entries
            ps_script = f"""
$hostFile = 'C:\\Windows\\System32\\drivers\\etc\\hosts'
$domain = '{domain}'
$entry = "`r`n127.0.0.1`t$domain`r`n::1`t$domain"
# Cleanup any previous malformed entries or old entries for this domain
$script = "(Get-Content $hostFile) | Where-Object {{ \$_ -notmatch '`n127' -and \$_ -notmatch '127.0.0.1\\s+$domain' -and \$_ -notmatch '::1\\s+$domain' }} | Set-Content $hostFile; Add-Content $hostFile -Value '$entry'"
Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command $script"
"""
            # Base64 encode the script
            import base64
            encoded_script = base64.b64encode(ps_script.encode('utf-16-le')).decode('ascii')
            
            subprocess.run([
                'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', 
                '-EncodedCommand', encoded_script
            ], check=True)
            
            return True
        except Exception:
            return False
    
    def remove_from_windows_hosts(self, domain: str) -> bool:
        """Remove domain from Windows hosts file using PowerShell (handles elevation)"""
        try:
            # Use PowerShell to remove entries with elevated privileges mechanism
            # We wrap the removal logic in a script block that we execute as Admin
            ps_script = f"""
$hostFile = 'C:\\Windows\\System32\\drivers\\etc\\hosts'
$domain = '{domain}'
# The inner command that actually modifies the file
$innerCmd = "(Get-Content $hostFile) | Where-Object {{ $_ -notmatch '127.0.0.1\\s+$domain' -and $_ -notmatch '::1\\s+$domain' }} | Set-Content $hostFile"

# Execute with elevation
Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $innerCmd
"""
            # Base64 encode the script
            import base64
            encoded_script = base64.b64encode(ps_script.encode('utf-16-le')).decode('ascii')
            
            subprocess.run([
                'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', 
                '-EncodedCommand', encoded_script
            ], check=True)
            
            return True
        except Exception:
            return False
    
    def get_certificate_info(self, domain: str) -> Optional[Dict]:
        """Get certificate information"""
        try:
            cert_file = self.ssl_dir / f"{domain}.pem"
            if not cert_file.exists():
                return None
            
            # Use openssl to get certificate info
            result = subprocess.run([
                'openssl', 'x509', '-in', str(cert_file), '-text', '-noout'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                info = {'file': str(cert_file)}
                for line in result.stdout.split('\n'):
                    if 'Subject:' in line:
                        info['subject'] = line.strip()
                    elif 'Issuer:' in line:
                        info['issuer'] = line.strip()
                    elif 'Not Before:' in line:
                        info['valid_from'] = line.strip()
                    elif 'Not After :' in line:
                        info['valid_until'] = line.strip()
                
                return info
        except Exception:
            pass
        return None
    
    def list_certificates(self) -> List[Dict]:
        """List all certificates"""
        certificates = []
        
        for cert_file in self.ssl_dir.glob("*.pem"):
            if cert_file.name.endswith("-key.pem"):
                continue
            
            domain = cert_file.stem
            info = self.get_certificate_info(domain)
            if info:
                certificates.append(info)
        
        return certificates
    
    def revoke_certificate(self, domain: str) -> bool:
        """Revoke/remove certificate"""
        try:
            cert_file = self.ssl_dir / f"{domain}.pem"
            key_file = self.ssl_dir / f"{domain}-key.pem"
            
            removed = False
            if cert_file.exists():
                cert_file.unlink()
                removed = True
            
            if key_file.exists():
                key_file.unlink()
                removed = True
            
            # Also try to remove from hosts file
            self.remove_from_windows_hosts(domain)
            
            return removed
        except Exception:
            return False
    
    def setup_ssl_for_site(self, site_name: str, tld: str) -> Dict:
        """Setup SSL for a site"""
        try:
            domain = f"{site_name}{tld}"
            
            # Generate certificate
            if not self.generate_certificate(domain):
                return {'success': False, 'error': 'Failed to generate certificate'}
            
            # Add to Windows hosts
            if not self.add_to_windows_hosts(domain):
                return {'success': False, 'error': 'Failed to add to Windows hosts'}
            
            # Get certificate info
            cert_info = self.get_certificate_info(domain)
            
            return {
                'success': True,
                'domain': domain,
                'certificate': cert_info,
                'cert_file': str(self.ssl_dir / f"{domain}.pem"),
                'key_file': str(self.ssl_dir / f"{domain}-key.pem")
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}