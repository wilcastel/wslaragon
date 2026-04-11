#!/bin/bash

# WSLaragon Development Setup Script
# Adjusts the project for your specific environment

# Source shared variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/vars.sh"

set -e

echo "🔧 WSLaragon Environment Setup"
echo "============================="

# Check if we're in WSL
if ! grep -q Microsoft /proc/version 2>/dev/null; then
    print_warning "This script is designed for WSL2 environment"
fi

# Check existing installations
print_status "Checking your current setup..."

echo "Checking PHP..."
if command -v php &> /dev/null; then
    PHP_INSTALLED_VERSION=$(php -v | head -n1 | cut -d' ' -f2 | cut -d'-' -f1)    echo "✓ PHP found: $PHP_INSTALLED_VERSION"
else
    echo "✗ PHP not found"
fi

echo "Checking Nginx..."
if command -v nginx &> /dev/null; then
    echo "✓ Nginx found"
else
    echo "✗ Nginx not found"
fi

echo "Checking MariaDB/MySQL..."
if command -v mysql &> /dev/null; then
    MYSQL_VERSION=$(mysql --version | head -n1)
    echo "✓ MariaDB/MySQL found: $MYSQL_VERSION"
else
    echo "✗ MariaDB/MySQL not found"
fi

echo "Checking mkcert..."
if command -v mkcert &> /dev/null; then
    echo "✓ mkcert found"
    MKCERT_CAROOT=$(mkcert -CAROOT)
    echo "  CA Root: $MKCERT_CAROOT"
else
    echo "✗ mkcert not found"
fi

# Create required directories
print_status "Creating project directories..."
mkdir -p "$CONFIG_DIR"/{sites,ssl,logs}
mkdir -p "$WEB_ROOT"

# Create initial config if doesn't exist
CONFIG_FILE="$CONFIG_DIR/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    print_status "Creating initial configuration..."
    cat > "$CONFIG_FILE" << EOF
php:
  version: "$PHP_VERSION"  ini_file: "$PHP_INI"
  extensions_dir: "$PHP_EXTENSIONS_DIR"

nginx:
  config_dir: "/etc/nginx"
  sites_available: "/etc/nginx/sites-available"
  sites_enabled: "/etc/nginx/sites-enabled"

mysql:
  data_dir: "/var/lib/mysql"
  config_file: "/etc/mysql/mariadb.conf.d/50-server.cnf"

ssl:
  ca_file: "$SSL_DIR/rootCA.pem"
  ca_key: "$SSL_DIR/rootCA-key.pem"

sites:
  tld: ".test"
  document_root: "$WEB_ROOT"

windows:
  hosts_file: "$WINDOWS_HOSTS_FILE"
EOF
    echo "✓ Configuration created at $CONFIG_FILE"
else
    echo "✓ Configuration already exists"
fi

# Setup SSL if mkcert is installed
if command -v mkcert &> /dev/null; then
    print_status "Setting up SSL certificates..."
    if [ ! -f "$SSL_DIR/rootCA.pem" ]; then
        mkcert -install
        CAROOT=$(mkcert -CAROOT)
        if [ -f "$CAROOT/rootCA.pem" ]; then
            cp "$CAROOT/rootCA.pem" "$SSL_DIR/"
        fi
        if [ -f "$CAROOT/rootCA-key.pem" ]; then
            cp "$CAROOT/rootCA-key.pem" "$SSL_DIR/"
        fi
        echo "✓ SSL certificates copied"
    else
        echo "✓ SSL certificates already exist"
    fi
fi

# Install WSLaragon Python package
print_status "Installing WSLaragon..."
cd "$INSTALL_DIR" 2>/dev/null || cd "$PROJECT_DIR"
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -e .
    echo "✓ WSLaragon installed in Python environment"
else
    print_warning "Python virtual environment not found"
    echo "Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
fi

# Create systemd service for web interface
print_status "Setting up web interface service..."
if [ -f "$INSTALL_DIR/scripts/wslaragon-web.service" ]; then
    sudo cp "$INSTALL_DIR/scripts/wslaragon-web.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable "$WSLARAGON_WEB_SERVICE"
    echo "✓ Web interface service configured"
fi

# Setup permissions
print_status "Setting up permissions..."
sudo chown -R "$USER:$USER" "$WEB_ROOT"
sudo usermod -a -G www-data "$USER"

# Setup sudoers for passwordless operations
print_status "Configuring sudoers..."
SUDOERS_FILE="/etc/sudoers.d/wslaragon"
if [ ! -f "$SUDOERS_FILE" ]; then
    echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/nginx, /usr/sbin/service, /bin/systemctl, /usr/bin/phpenmod, /usr/bin/phpdismod, /bin/cp, /bin/ln, /bin/rm" | sudo tee "$SUDOERS_FILE"
    echo "✓ Sudoers configured"
else
    echo "✓ Sudoers already configured"
fi

# Test installations
print_status "Testing configuration..."
php --version
nginx -t 2>/dev/null && echo "✓ Nginx configuration OK" || echo "✗ Nginx configuration error"

echo ""
echo "✅ Environment setup completed!"
echo "============================="
echo ""
echo "Next steps:"
echo "1. Start services: wslaragon service start nginx"
echo "2. Create first site: wslaragon site create myproject --php --mysql"
echo "3. Access web interface: http://localhost:${WEBSERVICE_PORT}"
echo "4. Browse to your site: http://myproject.test"
echo ""
echo "Your projects will be stored in: $WEB_ROOT/"
echo "Configuration file: $CONFIG_FILE"
echo ""
echo "🚀 Happy coding with WSLaragon!"