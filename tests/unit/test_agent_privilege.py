"""Unit tests for the fixed agent privilege protocol client."""
import json
from unittest.mock import Mock, patch


def _process(stdout=b'{"version":1,"ok":true,"code":"ok"}\n', stderr=b"", returncode=0):
    process = Mock()
    process.communicate.return_value = (stdout, stderr)
    process.returncode = returncode
    return process


def test_ready_uses_fixed_non_interactive_argv_and_one_json_record():
    from wslaragon.services.agent_privilege import PrivilegeClient

    process = _process(stderr=b"private diagnostic")
    with patch("wslaragon.services.agent_privilege.subprocess.Popen", return_value=process) as popen:
        result = PrivilegeClient(timeout=3).ready()

    assert result.ok is True
    assert result.code == "ok"
    assert result.stderr is None
    popen.assert_called_once_with(
        ["sudo", "-n", "--", "/usr/lib/wslaragon/agent-privilege-helper"],
        stdin=-1,
        stdout=-1,
        stderr=-1,
        shell=False,
    )
    assert process.communicate.call_args.args == (b'{"version":1,"op":"ready"}\n',)


def test_apply_registration_serializes_only_scalar_protocol_fields():
    from wslaragon.services.agent_privilege import PrivilegeClient

    process = _process()
    with patch("wslaragon.services.agent_privilege.subprocess.Popen", return_value=process):
        result = PrivilegeClient().apply_registration(
            "shop", "normal-public", ssl=True, php=False, proxy_port=3000
        )

    assert result.code == "ok"
    assert process.communicate.call_args.args == (
        b'{"version":1,"op":"apply_registration","site":"shop","layout":"normal-public","ssl":true,"php":false,"proxy_port":3000}\n',
    )


def test_client_maps_transport_and_protocol_failures_to_safe_codes(caplog):
    from wslaragon.services.agent_privilege import PrivilegeClient
    from wslaragon.services.agent_privilege import PrivilegeResult
    import subprocess

    timeout_process = Mock()
    timeout_process.communicate.side_effect = subprocess.TimeoutExpired("helper", 3)
    cases = [
        (FileNotFoundError(), "helper_missing"),
        (_process(returncode=1, stderr=b"sudo password for alice"), "authorization_denied"),
        (timeout_process, "timeout"),
        (_process(stdout=b"not json\n"), "protocol_invalid"),
        (_process(stdout=b'{"version":1,"ok":true,"code":"ok"}\n{}\n'), "protocol_invalid"),
        (_process(stdout=b"x" * 4097 + b"\n"), "protocol_invalid"),
        (_process(stdout=b'{"version":1,"ok":true,"code":"secret"}\n'), "protocol_invalid"),
    ]
    for process, code in cases:
        with patch("wslaragon.services.agent_privilege.subprocess.Popen", side_effect=process if isinstance(process, OSError) else None, return_value=None if isinstance(process, OSError) else process):
            result = PrivilegeClient(timeout=3).ready()
        assert result == PrivilegeResult(False, code)

    assert timeout_process.kill.called
    assert "sudo password for alice" not in caplog.text


def test_request_model_rejects_non_scalar_or_unknown_operations_before_transport():
    from wslaragon.services.agent_privilege import PrivilegeRequest
    import pytest

    with pytest.raises(ValueError):
        PrivilegeRequest("shell", (("command", "id"),)).record()
    with pytest.raises(ValueError):
        PrivilegeRequest.apply_registration("shop", "normal-root", ssl=1, php=False, proxy_port=None)


def test_client_accepts_only_one_valid_finite_result_code():
    from wslaragon.services.agent_privilege import PrivilegeClient

    for stdout, expected in [
        (b'{"version":1,"ok":false,"code":"operation_failed"}\n', (False, "operation_failed")),
        (b'{"version":2,"ok":true,"code":"ok"}\n', (False, "protocol_invalid")),
        (b'{"version":1,"ok":1,"code":"ok"}\n', (False, "protocol_invalid")),
    ]:
        with patch("wslaragon.services.agent_privilege.subprocess.Popen", return_value=_process(stdout=stdout)):
            result = PrivilegeClient().ready()
        assert (result.ok, result.code) == expected
