#!/bin/bash

# WSLaragon Web Service Setup
# Instala y activa el servicio web

set -e

echo "🌐 Setting up WSLaragon Web Service"
echo "=================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (sudo)"
   echo "Run: sudo bash $0"
   exit 1
fi

# Navigate to project directory
cd /home/wil/baselog/wslaragon

# Setup virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Install dependencies
print_status "Installing Python dependencies..."
source venv/bin/activate
pip install -e .
pip install flask click pyyaml pymysql psutil requests colorama rich

# Create systemd service
print_status "Creating systemd service..."
cat > /etc/systemd/system/wslaragon-web.service << EOF
[Unit]
Description=WSLaragon Web Interface
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/wil/baselog/wslaragon
Environment=PATH=/home/wil/baselog/wslaragon/venv/bin
Environment=FLASK_APP=src.wslaragon.web.app
Environment=FLASK_ENV=production
ExecStart=/home/wil/baselog/wslaragon/venv/bin/python -m flask run --host=0.0.0.0 --port=8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup permissions
print_status "Setting permissions..."
chown -R www-data:www-data /home/wil/baselog/wslaragon
chmod -R 755 /home/wil/baselog/wslaragon

# Reload systemd
print_status "Reloading systemd..."
systemctl daemon-reload

# Enable and start service
print_status "Enabling and starting WSLaragon web service..."
systemctl enable wslaragon-web
systemctl start wslaragon-web

# Check service status
print_status "Checking service status..."
sleep 2
if systemctl is-active --quiet wslaragon-web; then
    echo "✅ WSLaragon web service is running!"
    echo "🌐 Access it at: http://localhost:8080"
    echo ""
    echo "To check status: sudo systemctl status wslaragon-web"
    echo "To view logs: sudo journalctl -u wslaragon-web -f"
else
    echo "❌ Failed to start WSLaragon web service"
    echo "Checking logs:"
    journalctl -u wslaragon-web --no-pager -n 20
fi

echo ""
echo "🎯 Next steps:"
echo "1. Open Windows browser: http://localhost:8080"
echo "2. If still not accessible, check WSL2 network configuration"
echo "3. Run test script: ./scripts/test-setup.sh"
echo ""
echo "🚀 WSLaragon ready for your development!"