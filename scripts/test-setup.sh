#!/bin/bash

# WSLaragon Test Script
# Verifies your setup

set -e

echo "🧪 WSLaragon Environment Test"
echo "============================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

echo ""
echo "Testing WSLaragon installation..."

# Test 1: Python environment
echo "1. Python Environment:"
if [ -d "/opt/wslaragon/venv" ]; then
    if source /opt/wslaragon/venv/bin/activate 2>/dev/null; then
        if command -v wslaragon &> /dev/null; then
            print_success "WSLaragon CLI installed"
            wslaragon --version
        else
            print_error "WSLaragon CLI not found in venv"
        fi
    else
        print_error "Cannot activate virtual environment"
    fi
else
    print_error "Virtual environment not found"
fi

# Test 2: Configuration
echo ""
echo "2. Configuration:"
CONFIG_FILE="$HOME/.wslaragon/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    print_success "Configuration file exists"
    echo "  Location: $CONFIG_FILE"
    
    # Check key configurations
    if grep -q "document_root: /home/wil/web" "$CONFIG_FILE"; then
        print_success "Document root configured for /home/wil/web"
    else
        print_warning "Document root might not be configured for /home/wil/web"
    fi
    
    if grep -q "version: \"8.3\"" "$CONFIG_FILE"; then
        print_success "PHP 8.3 configured"
    else
        print_warning "PHP version might not be 8.3"
    fi
    
    if grep -q "mariadb" "$CONFIG_FILE"; then
        print_success "MariaDB configured"
    else
        print_warning "MariaDB might not be configured"
    fi
else
    print_error "Configuration file not found"
fi

# Test 3: Services status
echo ""
echo "3. System Services:"
services=("nginx" "mariadb" "php8.3-fpm")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        print_success "$service is running"
    else
        print_warning "$service is not running"
    fi
done

# Test 4: Web interface
echo ""
echo "4. Web Interface:"
if systemctl is-active --quiet "wslaragon-web"; then
    print_success "WSLaragon web service is running"
    echo "  Access: http://localhost:8080"
else
    print_warning "WSLaragon web service is not running"
    echo "  Start with: sudo systemctl start wslaragon-web"
fi

# Test 5: Project directory
echo ""
echo "5. Project Directory:"
PROJECT_DIR="/home/wil/web"
if [ -d "$PROJECT_DIR" ]; then
    print_success "Project directory exists"
    echo "  Location: $PROJECT_DIR"
    echo "  Permissions: $(ls -ld "$PROJECT_DIR" | awk '{print $3:$4}')"
else
    print_error "Project directory not found"
    echo "  Creating it: mkdir -p $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
fi

# Test 6: SSL Certificates
echo ""
echo "6. SSL Setup:"
if command -v mkcert &> /dev/null; then
    print_success "mkcert is installed"
    CAROOT=$(mkcert -CAROOT 2>/dev/null)
    echo "  CA Root: $CAROOT"
    
    if [ -f "$HOME/.wslaragon/ssl/rootCA.pem" ]; then
        print_success "CA certificate copied to WSLaragon"
    else
        print_warning "CA certificate not found in WSLaragon dir"
    fi
else
    print_error "mkcert not found"
fi

# Test 7: Ports
echo ""
echo "7. Network Ports:"
ports=("80:Nginx" "3306:MariaDB" "8080:WSLaragon Web")
for port_info in "${ports[@]}"; do
    port=$(echo "$port_info" | cut -d':' -f1)
    service=$(echo "$port_info" | cut -d':' -f2)
    
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        print_success "Port $port ($service) is listening"
    else
        print_warning "Port $port ($service) is not listening"
    fi
done

# Test 8: WSL access to Windows hosts
echo ""
echo "8. Windows Hosts Access:"
HOSTS_FILE="/mnt/c/Windows/System32/drivers/etc/hosts"
if [ -f "$HOSTS_FILE" ]; then
    print_success "Windows hosts file is accessible"
    echo "  Location: $HOSTS_FILE"
else
    print_error "Cannot access Windows hosts file"
    echo "  Check WSL2 network configuration"
fi

# Summary
echo ""
echo "🎯 Test Summary:"
echo "=================="
echo ""
echo "If all tests show green ✓, you're ready to go!"
echo ""
echo "Next commands:"
echo "1. Activate environment: source /opt/wslaragon/venv/bin/activate"
echo "2. Start web interface: sudo systemctl start wslaragon-web"
echo "3. Create first site: wslaragon site create test --php --mysql"
echo "4. Access from Windows: http://localhost:8080"
echo ""
echo "Access your site: http://test.test"
echo "Project files: /home/wil/web/test/"
echo ""
echo "🚀 Happy coding with WSLaragon!"