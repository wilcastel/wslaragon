#!/bin/bash

# WSLaragon Quick Start Script
# Setup a development environment quickly

set -e

echo "🚀 WSLaragon Quick Start"
echo "========================"

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

# Check if WSLaragon is installed
if ! command -v wslaragon &> /dev/null; then
    print_warning "WSLaragon not found. Please install it first:"
    echo "curl -fsSL https://raw.githubusercontent.com/your-username/wslaragon/main/scripts/install.sh | bash"
    exit 1
fi

# Start services
print_status "Starting development services..."
sudo systemctl start nginx 2>/dev/null || echo "Nginx already running"
sudo systemctl start mariadb 2>/dev/null || echo "MariaDB already running"
sudo systemctl start php8.3-fpm 2>/dev/null || echo "PHP-FPM already running"

# Show status
print_status "Service status:"
wslaragon service status

echo ""
print_status "Quick start completed!"
echo ""
echo "Next steps:"
echo "1. Create your first site: wslaragon site create myproject --php --mysql"
echo "2. Open web interface: http://localhost:8080"
echo "3. Navigate to your site: http://myproject.test"
echo ""
echo "For more commands, run: wslaragon --help"