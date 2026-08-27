#!/usr/bin/env python3
"""Immutable, no-argument root boundary for agent site registrations."""
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

MAX_REQUEST = 8192
MAX_RESPONSE = 4096
CONFIG = Path("/etc/wslaragon/agent-privilege.json")
VERSION = 1
OPS = {"ready", "apply_registration", "remove_registration"}
LAYOUTS = {
    "normal-root": (), "normal-public": ("public",), "normal-dist": ("dist",),
    "headless-backend-root": ("backend",), "headless-backend-public": ("backend", "public"),
    "headless-frontend-root": ("frontend",), "headless-frontend-dist": ("frontend", "dist"),
}
SITE = re.compile(r"(?:api\.)?[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def response(ok, code):
    text = json.dumps({"version": VERSION, "ok": ok, "code": code}, separators=(",", ":"))
    return text if len(text.encode()) <= MAX_RESPONSE else '{"version":1,"ok":false,"code":"operation_failed"}'


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("protocol_invalid")
        result[key] = value
    return result


def parse_request(raw):
    if not isinstance(raw, bytes) or not raw.endswith(b"\n") or len(raw) > MAX_REQUEST or raw.count(b"\n") != 1:
        raise ValueError("protocol_invalid")
    try:
        request = json.loads(raw[:-1].decode("utf-8"), object_pairs_hook=_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ValueError("protocol_invalid")
    if not isinstance(request, dict):
        raise ValueError("protocol_invalid")
    return request


def validate(request):
    op = request.get("op")
    if request.get("version") != VERSION or op not in OPS:
        raise ValueError("request_invalid")
    expected = {"version", "op"}
    if op != "ready":
        expected |= {"site", "layout"}
    if op == "apply_registration":
        expected |= {"ssl", "php", "proxy_port"}
    if set(request) != expected:
        raise ValueError("request_invalid")
    if op == "ready":
        return
    site, layout = request["site"], request["layout"]
    if not isinstance(site, str) or not SITE.fullmatch(site) or not isinstance(layout, str) or layout not in LAYOUTS:
        raise ValueError("request_invalid")
    if layout.startswith("headless-backend") != site.startswith("api."):
        raise ValueError("request_invalid")
    if op == "apply_registration":
        if type(request["ssl"]) is not bool or type(request["php"]) is not bool:
            raise ValueError("request_invalid")
        port = request["proxy_port"]
        if port is not None and (type(port) is not int or not 1024 <= port <= 65535):
            raise ValueError("request_invalid")
        if port is not None and request["php"]:
            raise ValueError("request_invalid")


def _native_ubuntu():
    try:
        values = dict(line.strip().split("=", 1) for line in Path("/etc/os-release").read_text().splitlines() if "=" in line)
        return platform.system() == "Linux" and "microsoft" not in platform.release().lower() and values.get("ID", "").strip('"') == "ubuntu"
    except OSError:
        return False


def _inside(root, candidate):
    try:
        root, candidate = root.resolve(strict=True), candidate.resolve(strict=True)
        candidate.relative_to(root)
        current = root
        for part in candidate.relative_to(root).parts:
            current /= part
            if current.is_symlink():
                return False
        return candidate.is_dir()
    except (OSError, ValueError):
        return False


def derived_root(request, config):
    root = Path(config["project_root"])
    candidate = root / request["site"].removeprefix("api.")
    for part in LAYOUTS[request["layout"]]:
        candidate /= part
    if not _inside(root, candidate):
        raise ValueError("layout_invalid")
    return candidate


def _config():
    try:
        stat = CONFIG.lstat()
        if not CONFIG.is_file() or stat.st_uid != 0 or stat.st_mode & 0o022:
            raise ValueError
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not all(isinstance(value.get(key), str) for key in ("project_root", "tld", "nginx_available", "nginx_enabled", "hosts")):
            raise ValueError
        return value
    except (OSError, ValueError, json.JSONDecodeError):
        raise ValueError("not_ready")


def _paths(request, config):
    name = request["site"] + config["tld"]
    available = Path(config["nginx_available"]) / ("wslaragon-agent-" + name)
    enabled = Path(config["nginx_enabled"]) / available.name
    return name, available, enabled


def _run(argv):
    subprocess.run(argv, check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)


def _apply(request, config):
    root = derived_root(request, config)
    name, available, enabled = _paths(request, config)
    if available.is_symlink() or enabled.exists() and not enabled.is_symlink():
        raise ValueError("operation_failed")
    marker = "# wslaragon-agent-managed\n"
    body = marker + "server {\n    listen 80;\n    server_name " + name + ";\n    root " + str(root) + ";\n}\n"
    temporary = available.with_suffix(".tmp")
    temporary.write_text(body, encoding="utf-8")
    os.replace(temporary, available)
    if not enabled.exists():
        enabled.symlink_to(available)
    try:
        _run(["/usr/sbin/nginx", "-t"])
        _run(["/bin/systemctl", "reload", "nginx"])
    except (OSError, subprocess.CalledProcessError):
        enabled.unlink(missing_ok=True)
        available.unlink(missing_ok=True)
        raise ValueError("operation_failed")


def _remove(request, config):
    derived_root(request, config)
    _, available, enabled = _paths(request, config)
    if available.exists() and (available.is_symlink() or not available.read_text(encoding="utf-8").startswith("# wslaragon-agent-managed\n")):
        raise ValueError("operation_failed")
    enabled.unlink(missing_ok=True)
    available.unlink(missing_ok=True)
    _run(["/usr/sbin/nginx", "-t"])
    _run(["/bin/systemctl", "reload", "nginx"])


def handle(raw, config=None):
    try:
        request = parse_request(raw)
        validate(request)
        config = config if config is not None else _config()
        if request["op"] == "ready":
            return {"version": VERSION, "ok": _native_ubuntu(), "code": "ok" if _native_ubuntu() else "platform_unsupported"}
        derived_root(request, config)
        if not _native_ubuntu():
            return {"version": VERSION, "ok": False, "code": "platform_unsupported"}
        (_apply if request["op"] == "apply_registration" else _remove)(request, config)
        return {"version": VERSION, "ok": True, "code": "ok"}
    except ValueError as error:
        return {"version": VERSION, "ok": False, "code": str(error)}
    except (OSError, subprocess.CalledProcessError):
        return {"version": VERSION, "ok": False, "code": "operation_failed"}


def main():
    result = {"version": VERSION, "ok": False, "code": "authorization_denied"} if os.geteuid() != 0 else handle(sys.stdin.buffer.read())
    sys.stdout.write(response(result["ok"], result["code"]) + "\n")


if __name__ == "__main__":
    main()
