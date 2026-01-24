#!/bin/bash

# WSLaragon Installation Script
# This script installs WSLaragon and its dependencies on Ubuntu/Debian

set -e

echo "🚀 WSLaragon Installation Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Run as a regular user."
   exit 1
fi

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
    php8.3 \
    php8.3-fpm \
    php8.3-mysql \
    php8.3-curl \
    php8.3-gd \
    php8.3-mbstring \
    php8.3-xml \
    php8.3-zip \
    php8.3-bcmath \
    php8.3-intl \
    php8.3-soap \
    php8.3-xsl \
    php8.3-opcache \
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
cd /opt
sudo mkdir -p wslaragon
sudo chown $USER:$USER wslaragon
cd wslaragon

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Clone or copy WSLaragon files
if [ -d "$HOME/wslaragon" ]; then
    print_status "Copying WSLaragon files from $HOME/wslaragon..."
    cp -r $HOME/wslaragon/* .
else
    print_status "Cloning WSLaragon from repository..."
    git clone https://github.com/your-username/wslaragon.git .
fi

# Install Python packages
print_status "Installing Python packages..."
pip install -e .

# Create directories
print_status "Creating WSLaragon directories..."
mkdir -p ~/.wslaragon/{sites,ssl,logs}
mkdir -p "$HOME/web"

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
sudo systemctl enable php8.3-fpm
sudo systemctl start php8.3-fpm

# Setup MariaDB
print_status "Configuring MariaDB..."
sudo systemctl enable mariadb
sudo systemctl start mariadb

# Secure MySQL installation
print_warning "Please secure your MySQL installation:"
echo "Run: sudo mysql_secure_installation"

# Create systemd service for WSLaragon web interface
print_status "Creating systemd service..."
sudo cp /opt/wslaragon/scripts/wslaragon-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wslaragon-web

# Setup permissions
print_status "Setting up permissions..."
sudo chown -R $USER:$USER /opt/wslaragon
sudo chown -R $USER:$USER ~/.wslaragon
sudo usermod -a -G www-data $USER

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
sudo systemctl start nginx
sudo systemctl start wslaragon-web

# Display installation summary
echo ""
echo "✅ WSLaragon installation completed!"
echo "=================================="
echo ""
echo "Web Interface: http://localhost:8080"
echo "CLI Command: wslaragon --help"
echo ""
echo "What's next:"
echo "1. Secure MySQL: sudo mysql_secure_installation"
echo "2. Restart shell to enable completion"
echo "3. Create your first site: wslaragon site create myproject"
echo ""
echo "Configuration files:"
echo "- WSLaragon config: ~/.wslaragon/config.yaml"
echo "- Nginx sites: /etc/nginx/sites-available/"
echo "- PHP config: /etc/php/8.1/fpm/php.ini"
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