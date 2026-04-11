#!/bin/bash

# WSLaragon Quick Start Script
# Setup a development environment quickly

# Source shared variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/vars.sh"

set -e

echo "🚀 WSLaragon Quick Start"
echo "========================"

# Check if WSLaragon is installed
if ! command -v wslaragon &> /dev/null; then
    print_warning "WSLaragon not found. Please install it first:"
    echo "curl -fsSL https://raw.githubusercontent.com/your-username/wslaragon/main/scripts/install.sh | bash"
    exit 1
fi

# Start services
print_status "Starting development services..."
sudo systemctl start "$NGINX_SERVICE" 2>/dev/null || echo "Nginx already running"
sudo systemctl start "$MARIADB_SERVICE" 2>/dev/null || echo "MariaDB already running"
sudo systemctl start "$PHP_SERVICE" 2>/dev/null || echo "PHP-FPM already running"

# Show status
print_status "Service status:"
wslaragon service status

echo ""
print_status "Quick start completed!"
echo ""
echo "Next steps:"
echo "1. Create your first site: wslaragon site create myproject --php --mysql"
echo "2. Open web interface: http://localhost:${WEBSERVICE_PORT}"
echo "3. Navigate to your site: http://myproject.test"
echo ""
echo "For more commands, run: wslaragon --help"