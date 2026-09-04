#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d /usr/share/omarchy ]]; then
  echo "This installer is only intended for Omarchy."
  exit 1
fi

echo "Installing the Phase 1 web stack..."
omarchy pkg add nginx php-fpm mkcert nss acl

echo "Preparing Nginx virtual-host directories..."
sudo install -d -m 755 /etc/nginx/sites-available /etc/nginx/sites-enabled

nginx_config=/etc/nginx/nginx.conf
include_line='    include /etc/nginx/sites-enabled/*.conf;'
if ! sudo grep -Fq "$include_line" "$nginx_config"; then
  backup="${nginx_config}.wslaragon.bak.$(date +%Y%m%d%H%M%S)"
  sudo cp "$nginx_config" "$backup"
  sudo sed -i "/^[[:space:]]*http[[:space:]]*{/a\\$include_line" "$nginx_config"
  echo "Nginx configuration backup: $backup"
fi

echo "Installing the local certificate authority..."
mkcert -install

# Omarchy browsers may keep their NSS profile under ~/.config instead of the
# paths mkcert scans. Import the CA into every discovered Firefox/Zen profile.
if command -v certutil >/dev/null 2>&1; then
  while IFS= read -r -d '' cert_db; do
    profile_dir=$(dirname "$cert_db")
    certutil -D -d "sql:$profile_dir" -n "mkcert $(whoami)@$(hostname)" 2>/dev/null || true
    certutil -A -d "sql:$profile_dir" -n "mkcert $(whoami)@$(hostname)" \
      -t "C,," -i "$(mkcert -CAROOT)/rootCA.pem"
  done < <(find "$HOME/.config/mozilla/firefox" "$HOME/.mozilla/firefox" \
    -name cert9.db -print0 2>/dev/null)
fi

# Nginx runs as `http` on Arch. It only needs traversal permission on the home
# directory; this does not grant directory listing or file read access.
setfacl -m u:http:x "$HOME"

echo "Validating and enabling services..."
sudo nginx -t
sudo systemctl enable --now php-fpm nginx

echo "Phase 1 runtime is ready."
echo "Create a test site with: .venv/bin/wslaragon site create demo --html"
