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
if timeout 1 bash -c '</dev/tcp/127.0.0.1/3306' 2>/dev/null; then
  echo "A MySQL-compatible database is already listening on 127.0.0.1:3306."
elif sudo docker inspect "$container" >/dev/null 2>&1; then
  echo "MariaDB container already exists: $container"
  sudo docker start "$container" >/dev/null
else
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
