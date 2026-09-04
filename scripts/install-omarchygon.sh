#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
database_container=""
install_database=true
install_laravel=true
install_node=true
install_wordpress=true
install_pma=true

usage() {
  cat <<'EOF'
Usage: ./scripts/install-omarchygon.sh [OPTIONS]

Install or update the complete WSLaragon environment for Omarchy.

Options:
  --database <mysql8|mariadb11>  Select the persistent database container
  --skip-database                Do not install or configure a database
  --skip-laravel                 Do not install Laravel prerequisites
  --skip-node                    Do not install Node.js, pnpm, and PM2
  --skip-wordpress               Do not install WordPress prerequisites
  --skip-pma                     Do not create the pma.test site
  -h, --help                     Show this help

The installer is idempotent and leaves the WSLaragon runtime stopped. Start it
when needed with: wslaragon on
EOF
}

while (($#)); do
  case "$1" in
    --database)
      [[ $# -ge 2 ]] || { echo "--database requires a value." >&2; exit 2; }
      database_container="$2"
      shift 2
      ;;
    --skip-database)
      install_database=false
      shift
      ;;
    --skip-laravel)
      install_laravel=false
      shift
      ;;
    --skip-node)
      install_node=false
      shift
      ;;
    --skip-wordpress)
      install_wordpress=false
      shift
      ;;
    --skip-pma)
      install_pma=false
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -n "$database_container" && "$database_container" != mysql8 && "$database_container" != mariadb11 ]]; then
  echo "Invalid database container: $database_container" >&2
  echo "Use mysql8 or mariadb11." >&2
  exit 2
fi

if [[ ! -d /usr/share/omarchy ]]; then
  echo "This installer is only intended for Omarchy." >&2
  exit 1
fi

if ((EUID == 0)); then
  echo "Run this installer as your regular user, not with sudo." >&2
  echo "It will request sudo only for the steps that need it." >&2
  exit 1
fi

if [[ "$install_database" == true && -z "$database_container" ]]; then
  mysql8_exists=false
  mariadb11_exists=false
  if command -v docker >/dev/null 2>&1; then
    sudo docker inspect mysql8 >/dev/null 2>&1 && mysql8_exists=true
    sudo docker inspect mariadb11 >/dev/null 2>&1 && mariadb11_exists=true
  fi

  if [[ "$mysql8_exists" == true && "$mariadb11_exists" == true ]]; then
    echo "Both mysql8 and mariadb11 exist and may use different volumes." >&2
    echo "Rerun with --database mysql8 or --database mariadb11." >&2
    echo "See docs/TROUBLESHOOTING.md before choosing if you are unsure." >&2
    exit 1
  elif [[ "$mysql8_exists" == true ]]; then
    database_container=mysql8
  else
    database_container=mariadb11
  fi
fi

if [[ "$install_database" != true ]]; then
  install_laravel=false
  install_wordpress=false
  install_pma=false
fi

echo "Omarchygon unified installer"
echo "Repository: $repo_root"

echo
echo "[1/7] Installing the web and HTTPS foundation..."
"$repo_root/scripts/setup-omarchy-phase1.sh"

echo
echo "[2/7] Installing the WSLaragon CLI..."
if [[ ! -x "$repo_root/.venv/bin/python" ]]; then
  python -m venv "$repo_root/.venv"
fi
"$repo_root/.venv/bin/python" -m pip install -e "$repo_root"
export PATH="$HOME/.local/bin:$PATH"
"$repo_root/scripts/install-omarchy-cli.sh"
wslaragon_cli="$repo_root/.venv/bin/wslaragon"

if [[ "$install_database" == true ]]; then
  echo
  echo "[3/7] Installing and selecting the database runtime..."
  "$repo_root/scripts/setup-omarchy-mariadb.sh" --container "$database_container"
  "$wslaragon_cli" mysql use "$database_container"
else
  echo
  echo "[3/7] Database, Laravel, WordPress, and phpMyAdmin installation skipped."
fi

echo
echo "[4/7] Installing framework prerequisites..."
if [[ "$install_laravel" == true ]]; then
  "$repo_root/scripts/setup-omarchy-laravel.sh"
fi
if [[ "$install_wordpress" == true ]]; then
  "$repo_root/scripts/setup-omarchy-wordpress.sh"
fi

echo
echo "[5/7] Installing the JavaScript runtime..."
if [[ "$install_node" == true ]]; then
  "$repo_root/scripts/setup-omarchy-node.sh"
else
  echo "Node.js installation skipped."
fi

echo
echo "[6/7] Configuring phpMyAdmin..."
if [[ "$install_pma" == true ]]; then
  if "$wslaragon_cli" site list | grep -Fq 'pma.test'; then
    echo "pma.test is already configured."
  else
    "$wslaragon_cli" site create pma --phpmyadmin
  fi
else
  echo "phpMyAdmin site creation skipped."
fi

echo
echo "[7/7] Validating and stopping the on-demand runtime..."
"$wslaragon_cli" doctor
"$wslaragon_cli" off

echo
echo "Omarchygon is installed and currently stopped."
echo "Start working: wslaragon on"
echo "Check status:  wslaragon status"
echo "Stop it:       wslaragon off"
