#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d /usr/share/omarchy ]]; then
  echo "This installer is only intended for Omarchy."
  exit 1
fi

echo "Installing the maintained Arch WordPress distribution..."
omarchy pkg add wordpress

if ! timeout 1 bash -c '</dev/tcp/127.0.0.1/3306' 2>/dev/null; then
  echo "MySQL/MariaDB is not reachable on 127.0.0.1:3306." >&2
  echo "Run ./scripts/setup-omarchy-mariadb.sh first." >&2
  exit 1
fi

if ! php -m | grep -qx mysqli; then
  echo "PHP mysqli is not enabled. Run ./scripts/setup-omarchy-mariadb.sh first." >&2
  exit 1
fi

echo "WordPress scaffolding prerequisites are ready."
echo "Create a site with: .venv/bin/wslaragon site create myblog --wordpress"
