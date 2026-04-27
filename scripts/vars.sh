#!/bin/bash

# WSLaragon Shared Variables
# Source this file in other scripts: source "$(dirname "$0")/vars.sh"
#
# This file contains all configurable variables used across WSLaragon scripts.
# Change values here to customize your installation.

# Project directory (auto-detected from script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Installation paths
INSTALL_DIR="${WSLARAGON_INSTALL_DIR:-/opt/wslaragon}"
VENV_DIR="${PROJECT_DIR}/venv"
BIN_DIR="${VENV_DIR}/bin"
CONFIG_DIR="${HOME}/.wslaragon"
SITES_DIR="${CONFIG_DIR}/sites"
SSL_DIR="${CONFIG_DIR}/ssl"
LOGS_DIR="${CONFIG_DIR}/logs"
WEB_ROOT="${WSLARAGON_WEB_ROOT:-$HOME/web}"

# Service names
NGINX_SERVICE="nginx"
MARIADB_SERVICE="mariadb"
PHP_SERVICE="php8.5-fpm"
WSLARAGON_WEB_SERVICE="wslaragon-web"

# PHP version (default: 8.5, also available: 8.4)
PHP_VERSION="8.5"
PHP_INI="/etc/php/${PHP_VERSION}/fpm/php.ini"
PHP_EXTENSIONS_DIR="/usr/lib/php/20250925"

# MySQL/MariaDB
MYSQL_USER="${DB_USER:-root}"
MYSQL_HOST="localhost"
MYSQL_PORT="3306"

# Ports
NGINX_HTTP_PORT="80"
NGINX_HTTPS_PORT="443"
MARIADB_PORT="3306"
WEBSERVICE_PORT="8080"
REDIS_PORT="6379"

# Windows paths
WINDOWS_HOSTS_FILE="/mnt/c/Windows/System32/drivers/etc/hosts"

# Colors for output (can be overridden)
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Print functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root
check_not_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root. Run as a regular user."
        exit 1
    fi
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (sudo)."
        echo "Run: sudo $0"
        exit 1
    fi
}

# Check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check if a service is active
service_is_active() {
    systemctl is-active --quiet "$1" 2>/dev/null
}