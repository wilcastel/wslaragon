#!/bin/bash

# WSLaragon Uninstall Script
# Removes WSLaragon and its dependencies on Ubuntu/Debian.
# Default mode preserves site data and databases.
# Use --purge to remove all data (requires confirmation).

# Source shared variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/vars.sh"

set -e

PURGE=false

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --purge)
            PURGE=true
            ;;
        -h|--help)
            echo "Usage: $0 [--purge]"
            echo ""
            echo "Options:"
            echo "  --purge    Remove site data, databases, and configuration (requires confirmation)"
            echo "  -h, --help Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $arg"
            echo "Run '$0 --help' for usage."
            exit 1
            ;;
    esac
done

print_status "Detected platform: native Ubuntu"

if [ "$PURGE" = true ]; then
    echo ""
    print_warning "PURGE mode will permanently delete:"
    echo "  - Site directories under $WEB_ROOT"
    echo "  - WSLaragon configuration under $CONFIG_DIR"
    echo "  - MariaDB databases and users created by WSLaragon"
    echo "  - Installed packages and systemd services"
    echo ""
    read -r -p "Type 'yes' to confirm complete removal: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        print_error "Confirmation not given. Aborting."
        exit 1
    fi
fi

# Stop services before removal
print_status "Stopping services..."
sudo systemctl stop "$NGINX_SERVICE" 2>/dev/null || true
sudo systemctl stop "$WSLARAGON_WEB_SERVICE" 2>/dev/null || true
sudo systemctl stop "php${PHP_VERSION}-fpm" 2>/dev/null || true
sudo systemctl stop "$MARIADB_SERVICE" 2>/dev/null || true

# Disable WSLaragon web service
if [ -f /etc/systemd/system/wslaragon-web.service ]; then
    sudo systemctl disable "$WSLARAGON_WEB_SERVICE" 2>/dev/null || true
    sudo rm -f /etc/systemd/system/wslaragon-web.service
    sudo systemctl daemon-reload
fi

# Remove packages
print_status "Removing installed packages..."
sudo apt remove -y --purge \
    "php${PHP_VERSION}-fpm" \
    "php${PHP_VERSION}" \
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
    "php${PHP_VERSION}-sqlite3" \
    phpmyadmin \
    nginx \
    mariadb-server \
    supervisor \
    2>/dev/null || true

sudo apt autoremove -y || true
sudo apt autoclean -y || true

# Remove pip-installed package
print_status "Removing Python package..."
pip uninstall -y wslaragon 2>/dev/null || true

# Remove installed project files
if [ -d "$INSTALL_DIR" ]; then
    print_status "Removing WSLaragon installation directory..."
    sudo rm -rf "$INSTALL_DIR"
fi

# Remove sudoers file
if [ -f /etc/sudoers.d/wslaragon ]; then
    print_status "Removing sudoers configuration..."
    sudo rm -f /etc/sudoers.d/wslaragon
fi

if [ "$PURGE" = true ]; then
    print_warning "Purging site data and databases..."

    if [ -d "$CONFIG_DIR" ]; then
        sudo rm -rf "$CONFIG_DIR"
    fi

    if [ -d "$WEB_ROOT" ]; then
        sudo rm -rf "$WEB_ROOT"
    fi

    # Drop wslaragon database user
    sudo mariadb -u root <<EOF 2>/dev/null || true
DROP USER IF EXISTS 'wslaragon'@'localhost';
FLUSH PRIVILEGES;
EOF
else
    print_status "Preserving site data and databases."
    print_info "To remove data later, run: $0 --purge"
fi

echo ""
if [ "$PURGE" = true ]; then
    echo "✅ WSLaragon has been completely removed."
else
    echo "✅ WSLaragon packages removed. Site data preserved at:"
    echo "   - Sites: $WEB_ROOT"
    echo "   - Config: $CONFIG_DIR"
fi
echo ""
