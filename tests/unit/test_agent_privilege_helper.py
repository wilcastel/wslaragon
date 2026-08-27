"""Unit tests for the immutable agent privilege helper boundary."""
import importlib.util
import json
from pathlib import Path

import pytest


HELPER = Path(__file__).parents[2] / "scripts" / "agent-privilege-helper.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("agent_privilege_helper", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_one_record_protocol_accepts_ready_and_rejects_extra_record():
    helper = load_helper()
    assert helper.parse_request(b'{"version":1,"op":"ready"}\n') == {"version": 1, "op": "ready"}
    with pytest.raises(ValueError, match="protocol_invalid"):
        helper.parse_request(b'{"version":1,"op":"ready"}\n{}\n')


@pytest.mark.parametrize(
    "raw,code",
    [
        (b'{"version":1,"op":"ready","path":"/tmp"}\n', "request_invalid"),
        (b'{"version":2,"op":"ready"}\n', "request_invalid"),
        (b'{"version":1,"op":"apply_registration","site":"../bad","layout":"normal-root","ssl":true,"php":false,"proxy_port":null}\n', "request_invalid"),
        (b'{"version":1,"op":"apply_registration","site":"site","layout":"normal-root","ssl":true,"php":false,"proxy_port":80}\n', "request_invalid"),
    ],
)
def test_request_validation_rejects_unsafe_or_incompatible_scalars(raw, code):
    helper = load_helper()
    assert helper.handle(raw, {})["code"] == code


def test_parser_rejects_duplicate_json_keys_and_oversized_records():
    helper = load_helper()
    with pytest.raises(ValueError, match="protocol_invalid"):
        helper.parse_request(b'{"version":1,"version":1,"op":"ready"}\n')
    with pytest.raises(ValueError, match="protocol_invalid"):
        helper.parse_request(b"{" + b"x" * helper.MAX_REQUEST + b"}\n")


def test_registration_rejects_symlinked_or_outside_generated_root(tmp_path):
    helper = load_helper()
    project = tmp_path / "projects"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / "demo").symlink_to(outside, target_is_directory=True)
    config = {"project_root": str(project), "tld": ".test"}
    request = b'{"version":1,"op":"apply_registration","site":"demo","layout":"normal-root","ssl":false,"php":false,"proxy_port":null}\n'
    assert helper.handle(request, config)["code"] == "layout_invalid"


def test_registration_uses_only_fixed_nginx_and_systemctl_argv(tmp_path, monkeypatch):
    helper = load_helper()
    project, available, enabled = tmp_path / "projects", tmp_path / "available", tmp_path / "enabled"
    (project / "demo").mkdir(parents=True)
    available.mkdir()
    enabled.mkdir()
    calls = []
    monkeypatch.setattr(helper, "_native_ubuntu", lambda: True)
    monkeypatch.setattr(helper, "_run", calls.append)
    config = {"project_root": str(project), "tld": ".test", "nginx_available": str(available), "nginx_enabled": str(enabled), "hosts": str(tmp_path / "hosts")}
    raw = b'{"version":1,"op":"apply_registration","site":"demo","layout":"normal-root","ssl":false,"php":false,"proxy_port":null}\n'
    assert helper.handle(raw, config) == {"version": 1, "ok": True, "code": "ok"}
    assert calls == [["/usr/sbin/nginx", "-t"], ["/bin/systemctl", "reload", "nginx"]]
    assert (available / "wslaragon-agent-demo.test").read_text().startswith("# wslaragon-agent-managed")


def test_response_is_bounded_schema_without_diagnostics():
    helper = load_helper()
    encoded = helper.response(False, "request_invalid")
    assert json.loads(encoded) == {"version": 1, "ok": False, "code": "request_invalid"}
    assert len(encoded.encode()) <= helper.MAX_RESPONSE
