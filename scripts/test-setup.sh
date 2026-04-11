#!/bin/bash

# WSLaragon Test Script
# Verifies your setup

# Source shared variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/vars.sh"

set -e

echo "🧪 WSLaragon Environment Test"
echo "============================"

# Additional print functions for this script
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error_msg() {
    echo -e "${RED}✗${NC} $1"
}

echo ""
echo "Testing WSLaragon installation..."

# Test 1: Python environment
echo "1. Python Environment:"
if [ -d "$INSTALL_DIR/venv" ]; then
    if source "$INSTALL_DIR/venv/bin/activate" 2>/dev/null; then
        if command -v wslaragon &> /dev/null; then
            print_success "WSLaragon CLI installed"
            wslaragon --version
        else
            print_error_msg "WSLaragon CLI not found in venv"
        fi
    else
        print_error_msg "Cannot activate virtual environment"
    fi
else
    print_error_msg "Virtual environment not found"
fi

# Test 2: Configuration
echo ""
echo "2. Configuration:"
if [ -f "$CONFIG_DIR/config.yaml" ]; then
    print_success "Configuration file exists"
    echo "  Location: $CONFIG_DIR"
    
    # Check key configurations
    if grep -q "document_root:" "$CONFIG_DIR/config.yaml"; then
        print_success "Document root configured"
    else
        print_warning "Document root not configured"
    fi
    
    if grep -q "version: \"$PHP_VERSION\"" "$CONFIG_DIR/config.yaml"; then
        print_success "PHP $PHP_VERSION configured"
    else
        print_warning "PHP version might not be $PHP_VERSION"
    fi
    
    if grep -q "mariadb" "$CONFIG_DIR/config.yaml"; then
        print_success "MariaDB configured"
    else
        print_warning "MariaDB might not be configured"
    fi
else
    print_error_msg "Configuration file not found"
fi

# Test 3: Services status
echo ""
echo "3. System Services:"
services=("$NGINX_SERVICE" "$MARIADB_SERVICE" "$PHP_SERVICE")
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
if systemctl is-active --quiet "$WSLARAGON_WEB_SERVICE"; then
    print_success "WSLaragon web service is running"
    echo "  Access: http://localhost:${WEBSERVICE_PORT}"
else
    print_warning "WSLaragon web service is not running"
    echo "  Start with: sudo systemctl start $WSLARAGON_WEB_SERVICE"
fi

# Test 5: Project directory
echo ""
echo "5. Project Directory:"
if [ -d "$WEB_ROOT" ]; then
    print_success "Project directory exists"
    echo "  Location: $WEB_ROOT"
    echo "  Permissions: $(ls -ld "$WEB_ROOT" | awk '{print $3":"$4}')"
else
    print_error_msg "Project directory not found"
    echo "  Creating it: mkdir -p $WEB_ROOT"
    mkdir -p "$WEB_ROOT"
fi

# Test 6: SSL Certificates
echo ""
echo "6. SSL Setup:"
if command -v mkcert &> /dev/null; then
    print_success "mkcert is installed"
    CAROOT=$(mkcert -CAROOT 2>/dev/null)
    echo "  CA Root: $CAROOT"
    
    if [ -f "$SSL_DIR/rootCA.pem" ]; then
        print_success "CA certificate copied to WSLaragon"
    else
        print_warning "CA certificate not found in WSLaragon dir"
    fi
else
    print_error_msg "mkcert not found"
fi

# Test 7: Ports
echo ""
echo "7. Network Ports:"
ports=("$NGINX_HTTP_PORT:Nginx" "$MARIADB_PORT:MariaDB" "$WEBSERVICE_PORT:WSLaragon Web")
for port_info in "${ports[@]}"; do
    port="${port_info%%:*}"
    service="${port_info#*:}"
    
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        print_success "Port $port ($service) is listening"
    else
        print_warning "Port $port ($service) is not listening"
    fi
done

# Test 8: WSL access to Windows hosts
echo ""
echo "8. Windows Hosts Access:"
if [ -f "$WINDOWS_HOSTS_FILE" ]; then
    print_success "Windows hosts file is accessible"
    echo "  Location: $WINDOWS_HOSTS_FILE"
else
    print_error_msg "Cannot access Windows hosts file"
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
echo "1. Activate environment: source $INSTALL_DIR/venv/bin/activate"
echo "2. Start web interface: sudo systemctl start $WSLARAGON_WEB_SERVICE"
echo "3. Create first site: wslaragon site create test --php --mysql"
echo "4. Access from Windows: http://localhost:${WEBSERVICE_PORT}"
echo ""
echo "Access your site: http://test.test"
echo "Project files: $WEB_ROOT/test/"
echo ""
echo "🚀 Happy coding with WSLaragon!"