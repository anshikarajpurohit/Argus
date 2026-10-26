"""Fixed output roots and symlink-aware sandbox checks."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTBED = ROOT / "testbed"
OUT = ROOT / "dataset/out"
sys.path.insert(0, str(ROOT / "agent"))


def sandbox(path: Path) -> Path:
    resolved = path.resolve()
    # Refuse a symlink for the sandbox root itself, as well as escaped children.
    if TESTBED.is_symlink() or not resolved.is_relative_to(TESTBED.absolute()):
        raise ValueError("Target must be inside the repository testbed directory")
    return resolved


def output_dir() -> Path:
    if OUT.is_symlink() or OUT.resolve() != OUT.absolute():
        raise ValueError("dataset/out must not be a symlink")
    OUT.mkdir(parents=True, exist_ok=True)
    return OUT
