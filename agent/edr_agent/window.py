"""Thread-safe sliding event window."""

from collections import deque
from threading import Lock


class Window:
    def __init__(self, seconds: float = 10):
        self.seconds, self.events, self.lock = seconds, deque(), Lock()

    def add(self, event: dict) -> None:
        with self.lock:
            self.events.append(event)

    def snapshot(self, now: float) -> list[dict]:
        with self.lock:
            self.events = deque(e for e in self.events if e["ts"] > now - self.seconds)
            return [e for e in self.events if e["ts"] <= now]
