#!/bin/bash

# WSLaragon Web Service Setup
# Instala y activa el servicio web

# Source shared variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/vars.sh"

set -e

echo "🌐 Setting up WSLaragon Web Service"
echo "=================================="

# Check if running as root (MUST be root for this script)
check_root

# Navigate to project directory
cd "$PROJECT_DIR"

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
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=FLASK_APP=src.wslaragon.web.app
Environment=FLASK_ENV=production
ExecStart=$PROJECT_DIR/venv/bin/python -m flask run --host=0.0.0.0 --port=$WEBSERVICE_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup permissions
print_status "Setting permissions..."
chown -R www-data:www-data "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"

# Reload systemd
print_status "Reloading systemd..."
systemctl daemon-reload

# Enable and start service
print_status "Enabling and starting WSLaragon web service..."
systemctl enable "$WSLARAGON_WEB_SERVICE"
systemctl start "$WSLARAGON_WEB_SERVICE"

# Check service status
print_status "Checking service status..."
sleep 2
if systemctl is-active --quiet "$WSLARAGON_WEB_SERVICE"; then
    echo "✅ WSLaragon web service is running!"
    echo "🌐 Access it at: http://localhost:${WEBSERVICE_PORT}"
    echo ""
    echo "To check status: sudo systemctl status $WSLARAGON_WEB_SERVICE"
    echo "To view logs: sudo journalctl -u $WSLARAGON_WEB_SERVICE -f"
else
    echo "❌ Failed to start WSLaragon web service"
    echo "Checking logs:"
    journalctl -u "$WSLARAGON_WEB_SERVICE" --no-pager -n 20
fi

echo ""
echo "🎯 Next steps:"
echo "1. Open Windows browser: http://localhost:${WEBSERVICE_PORT}"
echo "2. If still not accessible, check WSL2 network configuration"
echo "3. Run test script: $SCRIPT_DIR/test-setup.sh"
echo ""
echo "🚀 WSLaragon ready for your development!"