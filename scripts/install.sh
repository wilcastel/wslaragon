#!/bin/bash

# WSLaragon Installation Script
# This script installs WSLaragon and its dependencies on Ubuntu/Debian

# Source shared variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/vars.sh"

set -e

echo "🚀 WSLaragon Installation Script"
echo "================================"

# Check if running as root (should NOT be root)
check_not_root

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
print_status "Installing dependencies..."
sudo apt install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    mariadb-server \
    "php${PHP_VERSION}" \
    "php${PHP_VERSION}-fpm" \
    "php${PHP_VERSION}-mysql" \
    "php${PHP_VERSION}-curl" \
    "php${PHP_VERSION}-gd" \
    "php${PHP_VERSION}-mbstring" \
    "php${PHP_VERSION}-xml" \
    "php${PHP_VERSION}-zip" \
    "php${PHP_VERSION}-bcmath" \
    "php${PHP_VERSION}-intl" \
    "php${PHP_VERSION}-soap" \
    "php${PHP_VERSION}-xsl" \
    "php${PHP_VERSION}-opcache" \
    supervisor

# Install mkcert for SSL
print_status "Installing mkcert for SSL certificates..."
MKCERT_VERSION=$(curl -s https://api.github.com/repos/FiloSottile/mkcert/releases/latest | grep tag_name | cut -d '"' -f 4)
curl -L "https://github.com/FiloSottile/mkcert/releases/download/${MKCERT_VERSION}/mkcert-${MKCERT_VERSION}-linux-amd64" -o mkcert
chmod +x mkcert
sudo mv mkcert /usr/local/bin/

# Install local CA
mkcert -install

# Install Python dependencies
print_status "Installing Python dependencies..."
sudo mkdir -p "$INSTALL_DIR"
sudo chown "$USER:$USER" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Clone or copy WSLaragon files
if [ -d "$PROJECT_DIR" ]; then
    print_status "Copying WSLaragon files from $PROJECT_DIR..."
    cp -r "$PROJECT_DIR"/* .
else
    print_status "Cloning WSLaragon from repository..."
    git clone https://github.com/your-username/wslaragon.git .
fi

# Install Python packages
print_status "Installing Python packages..."
pip install -e .

# Create directories
print_status "Creating WSLaragon directories..."
mkdir -p "$CONFIG_DIR"/{sites,ssl,logs}
mkdir -p "$WEB_ROOT"

# Setup Nginx configuration
print_status "Configuring Nginx..."
sudo mkdir -p /etc/nginx/sites-available
sudo mkdir -p /etc/nginx/sites-enabled

# Create default Nginx config if not exists
if [ ! -f /etc/nginx/sites-available/default ]; then
    sudo cp /usr/share/nginx/html/index.html /etc/nginx/sites-available/
fi

# Setup PHP-FPM
print_status "Configuring PHP-FPM..."
sudo systemctl enable "php${PHP_VERSION}-fpm"
sudo systemctl start "php${PHP_VERSION}-fpm"

# Setup MariaDB
print_status "Configuring MariaDB..."
sudo systemctl enable "$MARIADB_SERVICE"
sudo systemctl start "$MARIADB_SERVICE"

# Secure MySQL installation
print_warning "Please secure your MySQL installation:"
echo "Run: sudo mysql_secure_installation"

# Create systemd service for WSLaragon web interface
print_status "Creating systemd service..."
sudo cp "$INSTALL_DIR/scripts/wslaragon-web.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "$WSLARAGON_WEB_SERVICE"

# Setup permissions
print_status "Setting up permissions..."
sudo chown -R "$USER:$USER" "$INSTALL_DIR"
sudo chown -R "$USER:$USER" "$CONFIG_DIR"
sudo usermod -a -G www-data "$USER"

# Add user to sudoers for passwordless operations (optional)
print_warning "Adding user to sudoers for WSLaragon operations..."
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/nginx, /usr/sbin/service, /bin/systemctl, /usr/bin/phpenmod, /usr/bin/phpdismod" | sudo tee /etc/sudoers.d/wslaragon

# Install shell completion
print_status "Installing shell completion..."
# Add to .bashrc
if ! grep -q 'wslaragon completion' ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# WSLaragon completion" >> ~/.bashrc
    echo 'eval "$(_WSLARAGON_COMPLETE=bash_source wslaragon)"' >> ~/.bashrc
fi

# Start services
print_status "Starting services..."
sudo systemctl start "$NGINX_SERVICE"
sudo systemctl start "$WSLARAGON_WEB_SERVICE"

# Display installation summary
echo ""
echo "✅ WSLaragon installation completed!"
echo "=================================="
echo ""
echo "Web Interface: http://localhost:${WEBSERVICE_PORT}"
echo "CLI Command: wslaragon --help"
echo ""
echo "What's next:"
echo "1. Secure MySQL: sudo mysql_secure_installation"
echo "2. Restart shell to enable completion"
echo "3. Create your first site: wslaragon site create myproject"
echo ""
echo "Configuration files:"
echo "- WSLaragon config: $CONFIG_DIR/config.yaml"
echo "- Nginx sites: /etc/nginx/sites-available/"
echo "- PHP config: $PHP_INI"
echo "- MySQL config: /etc/mysql/my.cnf"
echo ""
echo "For more information, see the documentation."
echo ""

# Verify installation
print_status "Verifying installation..."
source ~/.bashrc
wslaragon --version
nginx -t
php -v
mysql --version
echo ""
print_status "Installation verification completed. Enjoy using WSLaragon! 🎉"