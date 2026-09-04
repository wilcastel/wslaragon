#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv_cli="$repo_root/.venv/bin/wslaragon"
local_bin="${HOME}/.local/bin"
launcher="$local_bin/wslaragon"

if [[ ! -x "$venv_cli" ]]; then
  echo "WSLaragon is not installed in $repo_root/.venv." >&2
  echo "Run: python -m venv .venv && .venv/bin/pip install -e ." >&2
  exit 1
fi

mkdir -p "$local_bin"
ln -sfn "$venv_cli" "$launcher"

if [[ ":${PATH}:" != *":${local_bin}:"* ]]; then
  echo "Installed $launcher, but $local_bin is not currently in PATH." >&2
  exit 1
fi

echo "Installed: $launcher -> $venv_cli"
echo "You can now run: wslaragon --help"
