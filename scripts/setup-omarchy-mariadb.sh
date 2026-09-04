#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d /usr/share/omarchy ]]; then
  echo "This installer is only intended for Omarchy."
  exit 1
fi

omarchy pkg add phpmyadmin

# phpMyAdmin and other PHP database clients need the mysqli extension.
if grep -q '^;extension=mysqli$' /etc/php/php.ini; then
  sudo sed -i 's/^;extension=mysqli$/extension=mysqli/' /etc/php/php.ini
  sudo systemctl restart php-fpm
fi

container=mariadb11
if [[ "${1:-}" == "--container" ]]; then
  [[ $# -ge 2 ]] || { echo "--container requires a value." >&2; exit 2; }
  container="$2"
  shift 2
fi
if (($#)); then
  echo "Unknown option: $1" >&2
  exit 2
fi
if [[ "$container" != mysql8 && "$container" != mariadb11 ]]; then
  echo "Invalid database container: $container" >&2
  exit 2
fi

container_running=false
if sudo docker inspect --format '{{.State.Running}}' "$container" 2>/dev/null | grep -qx true; then
  container_running=true
fi

if timeout 1 bash -c '</dev/tcp/127.0.0.1/3306' 2>/dev/null; then
  if [[ "$container_running" != true ]]; then
    echo "Port 3306 is occupied, but the selected container '$container' is stopped." >&2
    echo "Stop the other database runtime before continuing." >&2
    exit 1
  fi
  echo "The selected database '$container' is already listening on 127.0.0.1:3306."
elif sudo docker inspect "$container" >/dev/null 2>&1; then
  echo "Database container already exists: $container"
  sudo docker start "$container" >/dev/null
else
  if [[ "$container" == mysql8 ]]; then
    echo "The mysql8 container does not exist." >&2
    echo "Install it through Omarchy first or use --container mariadb11." >&2
    exit 1
  fi
  echo "Installing MariaDB through Omarchy..."
  omarchy install docker dbs MariaDB
fi

echo "Waiting for MySQL/MariaDB..."
for attempt in {1..30}; do
  if timeout 1 bash -c '</dev/tcp/127.0.0.1/3306' 2>/dev/null; then
    echo "MySQL/MariaDB is ready on 127.0.0.1:3306."
    exit 0
  fi
  sleep 1
done

echo "MariaDB did not become ready within 30 seconds." >&2
sudo docker logs --tail 30 "$container" >&2 || true
exit 1
