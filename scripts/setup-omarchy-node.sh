#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d /usr/share/omarchy ]]; then
  echo "This installer is only intended for Omarchy."
  exit 1
fi

echo "Installing Node.js, pnpm, and PM2..."
omarchy pkg add nodejs pnpm pm2

for executable in node pnpm pm2; do
  if ! command -v "$executable" >/dev/null; then
    echo "$executable was not found after installation." >&2
    exit 1
  fi
done

echo "Node.js $(node --version), pnpm $(pnpm --version), and PM2 $(pm2 --version) are ready."
echo "Create a site with: .venv/bin/wslaragon site create node-demo --node"
echo "Start it with: .venv/bin/wslaragon node start node-demo"
