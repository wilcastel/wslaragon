"""Safe unprivileged transport for the fixed agent privilege helper."""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from typing import Any, Optional, Tuple

_HELPER_ARGV = ["sudo", "-n", "--", "/usr/lib/wslaragon/agent-privilege-helper"]
_VERSION = 1
_MAX_RESPONSE = 4096
_MAX_STDERR = 4096
_SAFE_CODES = frozenset({
    "ok", "not_ready", "authorization_denied", "helper_missing", "protocol_invalid",
    "request_invalid", "platform_unsupported", "layout_invalid", "operation_failed",
})
_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class PrivilegeRequest:
    """One immutable, scalar-only protocol request."""

    op: str
    fields: Tuple[Tuple[str, Any], ...] = ()

    @classmethod
    def ready(cls) -> "PrivilegeRequest":
        return cls("ready")

    @classmethod
    def apply_registration(
        cls, site: str, layout: str, *, ssl: bool, php: bool, proxy_port: Optional[int]
    ) -> "PrivilegeRequest":
        return cls("apply_registration", (("site", site), ("layout", layout), ("ssl", ssl),
                                             ("php", php), ("proxy_port", proxy_port)))

    @classmethod
    def remove_registration(cls, site: str, layout: str) -> "PrivilegeRequest":
        return cls("remove_registration", (("site", site), ("layout", layout)))

    def __post_init__(self) -> None:
        expected = {"ready": (), "remove_registration": ("site", "layout"),
                    "apply_registration": ("site", "layout", "ssl", "php", "proxy_port")}
        if self.op not in expected or tuple(key for key, _ in self.fields) != expected[self.op]:
            raise ValueError("invalid privilege request")
        values = dict(self.fields)
        if self.op != "ready" and (
            not isinstance(values["site"], str) or not isinstance(values["layout"], str)
        ):
            raise ValueError("invalid privilege request")
        if self.op == "apply_registration" and (
            type(values["ssl"]) is not bool or type(values["php"]) is not bool
            or (
                values["proxy_port"] is not None
                and (
                    type(values["proxy_port"]) is not int
                    or not 1024 <= values["proxy_port"] <= 65535
                )
            )
        ):
            raise ValueError("invalid privilege request")

    def record(self) -> bytes:
        record = {"version": _VERSION, "op": self.op}
        record.update(self.fields)
        return json.dumps(record, separators=(",", ":")).encode("utf-8") + b"\n"


@dataclass(frozen=True)
class PrivilegeResult:
    """A validated, non-secret helper outcome."""

    ok: bool
    code: str
    stderr: None = None


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _parse_result(stdout: bytes) -> PrivilegeResult:
    if len(stdout) > _MAX_RESPONSE or not stdout.endswith(b"\n") or stdout.count(b"\n") != 1:
        return PrivilegeResult(False, "protocol_invalid")
    try:
        record = json.loads(stdout[:-1].decode("utf-8"), object_pairs_hook=_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return PrivilegeResult(False, "protocol_invalid")
    if (
        not isinstance(record, dict)
        or set(record) != {"version", "ok", "code"}
        or record["version"] != _VERSION
        or type(record["ok"]) is not bool
        or not isinstance(record["code"], str)
        or record["code"] not in _SAFE_CODES
        or (record["ok"] and record["code"] != "ok")
        or (not record["ok"] and record["code"] == "ok")
    ):
        return PrivilegeResult(False, "protocol_invalid")
    return PrivilegeResult(record["ok"], record["code"])


class PrivilegeClient:
    """Invoke only the no-argument helper without interactive authentication."""

    def __init__(self, timeout: float = 5) -> None:
        self.timeout = timeout

    def ready(self) -> PrivilegeResult:
        return self._send(PrivilegeRequest.ready())

    def apply_registration(
        self, site: str, layout: str, *, ssl: bool, php: bool, proxy_port: Optional[int]
    ) -> PrivilegeResult:
        request = PrivilegeRequest.apply_registration(
            site, layout, ssl=ssl, php=php, proxy_port=proxy_port
        )
        return self._send(request)

    def remove_registration(self, site: str, layout: str) -> PrivilegeResult:
        return self._send(PrivilegeRequest.remove_registration(site, layout))

    def _send(self, request: PrivilegeRequest) -> PrivilegeResult:
        try:
            process = subprocess.Popen(
                _HELPER_ARGV,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
            stdout, stderr = process.communicate(request.record(), timeout=self.timeout)
        except OSError:
            return PrivilegeResult(False, "helper_missing")
        except subprocess.TimeoutExpired:
            process.kill()
            return PrivilegeResult(False, "timeout")
        if stderr:
            _LOG.warning("agent privilege helper stderr: %d bytes", min(len(stderr), _MAX_STDERR))
        if process.returncode != 0:
            return PrivilegeResult(False, "authorization_denied")
        return _parse_result(stdout)
