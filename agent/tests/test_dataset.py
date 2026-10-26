import hashlib
import json
import subprocess
import sys
from pathlib import Path
import pytest
from common import ROOT, TESTBED, sandbox
from generate_events import stream
from make_fixtures import generate


def test_reproducible_fixtures_and_streams():
    first = generate(seed=42)
    second = generate(seed=42)
    assert first == second and len(first) == 170
    for row in first:
        assert (
            hashlib.sha256((TESTBED / row["path"]).read_bytes()).hexdigest()
            == row["sha256"]
        )
    for scenario in [
        "B1",
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
        "B7",
        "M1",
        "M2",
        "M3",
        "M4",
        "M5",
        "M6",
    ]:
        assert stream(scenario, 42, first) == stream(scenario, 42, first)


def test_sandbox_rejections(tmp_path):
    with pytest.raises(ValueError):
        sandbox(tmp_path)
    script = ROOT / "dataset/attack_emulator.py"
    for args in [[], ["--target", str(tmp_path), "--i-understand-this-is-a-sandbox"]]:
        result = subprocess.run(
            [sys.executable, str(script), *args], capture_output=True
        )
        assert result.returncode != 0


def test_emulator_contains_no_forbidden_imports():
    import ast

    tree = ast.parse((ROOT / "dataset/attack_emulator.py").read_text())
    imports = {
        a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names
    }
    assert not imports & {
        "socket",
        "requests",
        "http",
        "urllib",
        "cryptography",
        "Crypto",
        "hashlib",
    }
