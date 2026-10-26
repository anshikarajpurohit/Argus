import os
from unittest.mock import Mock
import pytest
from edr_agent import responder


@pytest.mark.parametrize(
    "pid,name",
    [
        (0, "unknown"),
        (1, "unknown"),
        (4, "unknown"),
        (os.getpid(), "unknown"),
        (os.getppid(), "unknown"),
        (987654, "node"),
        (987654, "CHROME"),
    ],
)
def test_protected_processes_never_suspended(monkeypatch, cfg, pid, name):
    monkeypatch.setattr(responder, "attribute", lambda _: (pid, name))
    process = Mock()
    monkeypatch.setattr(responder.psutil, "Process", process)
    cfg["responseMode"] = "suspend"
    alert = {"severity": "CRITICAL", "affectedFiles": ["/a"], "responseTaken": "none"}
    responder.respond(alert, cfg)
    process.assert_not_called()
    assert alert["responseTaken"] == "none"


def test_default_alert_only(monkeypatch, cfg):
    monkeypatch.setattr(responder, "attribute", lambda _: (12345, "editor"))
    process = Mock()
    monkeypatch.setattr(responder.psutil, "Process", process)
    responder.respond({"severity": "CRITICAL", "affectedFiles": []}, cfg)
    process.assert_not_called()


def test_suspend_and_failure(monkeypatch, cfg):
    monkeypatch.setattr(responder, "attribute", lambda _: (12345, "editor"))
    proc = Mock()
    proc.name.return_value = "editor"
    monkeypatch.setattr(responder.psutil, "Process", lambda _: proc)
    cfg["responseMode"] = "suspend"
    alert = {"severity": "CRITICAL", "affectedFiles": []}
    responder.respond(alert, cfg)
    assert alert["responseTaken"] == "suspended"
    proc.suspend.side_effect = responder.psutil.AccessDenied(12345)
    responder.respond(alert, cfg)
    assert alert["responseTaken"] == "suspend_failed"
