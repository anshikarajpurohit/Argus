"""Persistent tripwire paths; reads cannot be detected by filesystem notifications."""

import hashlib
import json
import time
from pathlib import Path


class Canaries:
    def __init__(self, cfg: dict, state: Path):
        self.cfg, self.state = cfg, state
        self.paths = {
            str((Path(root) / name).resolve())
            for root in cfg["watch_paths"]
            for name in cfg["canary_names"]
        }
        self.pending = {}
        self.suppressed = {}
        self.own_hashes = {}
        for path in self.paths:
            self.create(path)
        self.save()

    def create(self, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            self.suppressed[path] = time.monotonic() + 5
            try:
                with target.open("x") as handle:
                    handle.write(
                        ("Argus harmless decoy fixture. Do not edit.\n" * 70)[:3072]
                    )
            except FileExistsError:
                pass
            self.own_hashes[path] = hashlib.sha256(target.read_bytes()).hexdigest()

    def save(self) -> None:
        self.state.parent.mkdir(parents=True, exist_ok=True)
        records = []
        for path in sorted(self.paths):
            try:
                digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            except OSError:
                digest = None
            records.append({"path": path, "sha256": digest})
        temporary = self.state.with_suffix(".tmp")
        temporary.write_text(json.dumps(records, indent=2))
        temporary.replace(self.state)

    def arm(self) -> None:
        # Model loading/baselining can take longer than the notification debounce.
        for path in self.own_hashes:
            self.suppressed[path] = time.monotonic() + 5

    def internal(self, path: str, action: str) -> bool:
        if action not in (
            "created",
            "modified",
        ) or time.monotonic() >= self.suppressed.get(path, 0):
            return False
        try:
            return hashlib.sha256(
                Path(path).read_bytes()
            ).hexdigest() == self.own_hashes.get(path)
        except OSError:
            return False

    def deleted(self, path: str) -> None:
        self.pending[path] = time.monotonic() + 5

    def tick(self) -> None:
        for path, due in list(self.pending.items()):
            if time.monotonic() >= due:
                self.create(path)
                del self.pending[path]
                self.save()
