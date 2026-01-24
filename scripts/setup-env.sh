#!/bin/bash

# WSLaragon Development Setup Script
# Adjusts the project for your specific environment

set -e

echo "🔧 WSLaragon Environment Setup"
echo "============================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if we're in WSL
if ! grep -q Microsoft /proc/version 2>/dev/null; then
    print_warning "This script is designed for WSL2 environment"
fi

# Check existing installations
print_status "Checking your current setup..."

echo "Checking PHP..."
if command -v php &> /dev/null; then
    PHP_VERSION=$(php -v | head -n1 | cut -d' ' -f2 | cut -d'-' -f1)
    echo "✓ PHP found: $PHP_VERSION"
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
mkdir -p ~/.wslaragon/{sites,ssl,logs}
mkdir -p "$HOME/web"

# Create initial config if doesn't exist
CONFIG_FILE="$HOME/.wslaragon/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    print_status "Creating initial configuration..."
    cat > "$CONFIG_FILE" << EOF
php:
  version: "8.3"
  ini_file: "/etc/php/8.3/fpm/php.ini"
  extensions_dir: "/usr/lib/php/20230831"

nginx:
  config_dir: "/etc/nginx"
  sites_available: "/etc/nginx/sites-available"
  sites_enabled: "/etc/nginx/sites-enabled"

mysql:
  data_dir: "/var/lib/mysql"
  config_file: "/etc/mysql/mariadb.conf.d/50-server.cnf"

ssl:
  ca_file: "$HOME/.wslaragon/ssl/rootCA.pem"
  ca_key: "$HOME/.wslaragon/ssl/rootCA-key.pem"

sites:
  tld: ".test"
  document_root: "$HOME/web"

windows:
  hosts_file: "/mnt/c/Windows/System32/drivers/etc/hosts"
EOF
    echo "✓ Configuration created at $CONFIG_FILE"
else
    echo "✓ Configuration already exists"
fi

# Setup SSL if mkcert is installed
if command -v mkcert &> /dev/null; then
    print_status "Setting up SSL certificates..."
    if [ ! -f "$HOME/.wslaragon/ssl/rootCA.pem" ]; then
        mkcert -install
        CAROOT=$(mkcert -CAROOT)
        if [ -f "$CAROOT/rootCA.pem" ]; then
            cp "$CAROOT/rootCA.pem" "$HOME/.wslaragon/ssl/"
        fi
        if [ -f "$CAROOT/rootCA-key.pem" ]; then
            cp "$CAROOT/rootCA-key.pem" "$HOME/.wslaragon/ssl/"
        fi
        echo "✓ SSL certificates copied"
    else
        echo "✓ SSL certificates already exist"
    fi
fi

# Install WSLaragon Python package
print_status "Installing WSLaragon..."
cd /opt/wslaragon 2>/dev/null || cd ~/wslaragon
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
if [ -f "/opt/wslaragon/scripts/wslaragon-web.service" ]; then
    sudo cp /opt/wslaragon/scripts/wslaragon-web.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable wslaragon-web
    echo "✓ Web interface service configured"
fi

# Setup permissions
print_status "Setting up permissions..."
sudo chown -R $USER:$USER "$HOME/web"
sudo usermod -a -G www-data $USER

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
echo "3. Access web interface: http://localhost:8080"
echo "4. Browse to your site: http://myproject.test"
echo ""
echo "Your projects will be stored in: $HOME/web/"
echo "Configuration file: $CONFIG_FILE"
echo ""
echo "🚀 Happy coding with WSLaragon!"