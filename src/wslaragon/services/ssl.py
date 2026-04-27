import logging
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SSLManager:
    def __init__(self, config):
        self.config = config
        # Provide default values if config keys are missing
        ssl_dir = config.get('ssl.dir')
        if ssl_dir is None:
            ssl_dir = str(Path.home() / ".wslaragon" / "ssl")
        self.ssl_dir = Path(ssl_dir)
        
        ca_file = config.get('ssl.ca_file')
        if ca_file is None:
            ca_file = str(self.ssl_dir / "rootCA.pem")
        self.ca_file = Path(ca_file)
        
        ca_key = config.get('ssl.ca_key')
        if ca_key is None:
            ca_key = str(self.ssl_dir / "rootCA-key.pem")
        self.ca_key = Path(ca_key)
        
        windows_hosts = config.get('windows.hosts_file')
        if windows_hosts is None:
            windows_hosts = "/mnt/c/Windows/System32/drivers/etc/hosts"
        self.windows_hosts = Path(windows_hosts)
        
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
        except Exception as e:
            logger.debug(f"is_mkcert_installed failed: {e}")
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
        except Exception as e:
            logger.debug(f"install_mkcert failed: {e}")
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
        except Exception as e:
            logger.debug(f"create_ca failed: {e}")
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
        except Exception as e:
            logger.debug(f"_get_caroot_path failed: {e}")
            pass
        return None
    
    def generate_certificate(self, domain: str, additional_domains: List[str] = None) -> bool:
        """Generate SSL certificate for domain
        
        Uses openssl to create a certificate with the domain name in both
        the CN (Common Name) and SAN (Subject Alternative Name), signed by
        the local root CA. This ensures compatibility with all browsers and
        clients, including those that still check CN.
        """
        import tempfile
        
        try:
            cert_file = self.ssl_dir / f"{domain}.pem"
            key_file = self.ssl_dir / f"{domain}-key.pem"
            
            # Ensure root CA exists
            if not self.ca_file.exists() or not self.ca_key.exists():
                if not self.create_ca():
                    logger.error("Failed to create root CA for certificate signing")
                    return False
            
            # Build domain list for SANs
            domains = [domain]
            if additional_domains:
                domains.extend(additional_domains)
            
            # Build SAN entries (always include domain as DNS entry)
            san_entries = [f"DNS:{d}" for d in domains]
            # Also add localhost IP for local development convenience
            san_entries.append("IP:127.0.0.1")
            san_string = ",".join(san_entries)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                csr_file = tmp_path / f"{domain}.csr"
                tmp_key = tmp_path / f"{domain}-key.pem"
                tmp_cert = tmp_path / f"{domain}.pem"
                ext_file = tmp_path / f"{domain}.ext"
                
                # Create OpenSSL config for extensions (SANs)
                ext_content = f"""authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = {san_string}
"""
                with open(ext_file, 'w') as f:
                    f.write(ext_content)
                
                # Generate private key
                subprocess.run([
                    'openssl', 'genrsa', '-out', str(tmp_key), '2048'
                ], check=True, capture_output=True)
                
                # Generate CSR with domain as CN (Common Name)
                subprocess.run([
                    'openssl', 'req', '-new',
                    '-key', str(tmp_key),
                    '-out', str(csr_file),
                    '-subj', f'/CN={domain}/O=WSLaragon Development/C=US'
                ], check=True, capture_output=True)
                
                # Sign the certificate with our root CA
                subprocess.run([
                    'openssl', 'x509', '-req',
                    '-in', str(csr_file),
                    '-CA', str(self.ca_file),
                    '-CAkey', str(self.ca_key),
                    '-CAcreateserial',
                    '-out', str(tmp_cert),
                    '-days', '825',
                    '-sha256',
                    '-extfile', str(ext_file)
                ], check=True, capture_output=True)
                
                # Move generated files to SSL directory
                key_file.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(['cp', str(tmp_key), str(key_file)], check=True)
                subprocess.run(['cp', str(tmp_cert), str(cert_file)], check=True)
                
                # Ensure proper permissions
                key_file.chmod(0o600)
                cert_file.chmod(0o644)
            
            return cert_file.exists() and key_file.exists()
        except Exception as e:
            logger.error(f"generate_certificate failed: {e}")
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
$script = "(Get-Content $hostFile) | Where-Object {{ $_ -notmatch '`n127' -and $_ -notmatch '127.0.0.1\\s+$domain' -and $_ -notmatch '::1\\s+$domain' }} | Set-Content $hostFile; Add-Content $hostFile -Value '$entry'"
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
        except Exception as e:
            logger.debug(f"add_to_windows_hosts failed: {e}")
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
        except Exception as e:
            logger.debug(f"remove_from_windows_hosts failed: {e}")
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
        except Exception as e:
            logger.debug(f"get_certificate_info failed: {e}")
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
        except Exception as e:
            logger.debug(f"revoke_certificate failed: {e}")
            return False
    
    def setup_ssl_for_site(self, site_name: str, tld: str) -> Dict:
        """Setup SSL for a site"""
        try:
            # Normalize: strip TLD if user included it
            if site_name.endswith(tld):
                site_name = site_name[:-len(tld)]
            domain = f"{site_name}{tld}"
            
            # Generate certificate
            if not self.generate_certificate(domain):
                return {'success': False, 'error': 'Failed to generate certificate'}
            
            # Add to Windows hosts (non-fatal if it fails — domain may already exist)
            hosts_result = self.add_to_windows_hosts(domain)
            if not hosts_result:
                logger.warning(f"Could not add {domain} to Windows hosts (may already exist or permission denied)")
            
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