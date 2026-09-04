#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d /usr/share/omarchy ]]; then
  echo "This installer is only intended for Omarchy."
  exit 1
fi

echo "Installing Composer..."
omarchy pkg add composer

required_extensions=(ctype curl dom fileinfo filter hash mbstring openssl pdo_mysql session tokenizer xml)
missing_extensions=()
php_modules="$(php -m)"

for extension in "${required_extensions[@]}"; do
  if ! grep -qx "$extension" <<<"$php_modules"; then
    missing_extensions+=("$extension")
  fi
done

if ((${#missing_extensions[@]})); then
  echo "Missing PHP extensions: ${missing_extensions[*]}" >&2
  echo "Enable them in /etc/php/php.ini and restart php-fpm." >&2
  exit 1
fi

if ! timeout 1 bash -c '</dev/tcp/127.0.0.1/3306' 2>/dev/null; then
  echo "MySQL/MariaDB is not reachable on 127.0.0.1:3306." >&2
  echo "Run ./scripts/setup-omarchy-mariadb.sh first." >&2
  exit 1
fi

echo "Laravel scaffolding prerequisites are ready."
echo "Create a site with: .venv/bin/wslaragon site create myapp --laravel=12"
