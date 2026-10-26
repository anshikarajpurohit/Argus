"""Trailing-edge debounce; all enrichment is performed off the watchdog callback."""

import fnmatch
import time
from pathlib import Path
from threading import Lock
from watchdog.events import FileSystemEventHandler


class Handler(FileSystemEventHandler):
    def __init__(self, cfg: dict, sink):
        self.cfg, self.sink = cfg, sink
        self.pending = {}
        self.lock = Lock()

    def ignored(self, path: str) -> bool:
        p = Path(path).resolve()
        if any(
            p == Path(x) or Path(x) in p.parents
            for x in self.cfg.get("excluded_paths", [])
        ):
            return True
        for pattern in self.cfg["ignore_patterns"]:
            if (
                fnmatch.fnmatch(p.name, pattern)
                or fnmatch.fnmatch(p.as_posix(), pattern)
                or any(
                    fnmatch.fnmatch("/".join(p.parts[i:]), pattern)
                    for i in range(len(p.parts))
                )
            ):
                return True
        return False

    def on_any_event(self, event) -> None:
        if event.is_directory or event.event_type not in (
            "created",
            "modified",
            "deleted",
            "moved",
        ):
            return
        if self.ignored(event.src_path):
            return
        action = event.event_type
        dest = getattr(event, "dest_path", None) or None
        if dest and self.ignored(dest):
            dest = None
            action = "deleted"
        with self.lock:
            if action == "modified":
                self.pending[event.src_path] = (
                    time.monotonic() + 0.5,
                    action,
                    event.src_path,
                    dest,
                )
            else:
                previous = self.pending.pop(event.src_path, None)
                if previous:
                    self.sink(previous[1:])
                self.sink((action, event.src_path, dest))

    def flush(self, force: bool = False) -> None:
        with self.lock:
            for path, item in list(self.pending.items()):
                if force or item[0] <= time.monotonic():
                    self.sink(item[1:])
                    del self.pending[path]
