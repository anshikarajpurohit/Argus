"""The identical feature implementation is used in training and monitoring."""

from pathlib import Path
from .analyzer import entropy_spike, extension_change

FEATURE_NAMES = [
    "n_modified",
    "n_created",
    "n_deleted",
    "n_moved",
    "n_unique_files",
    "n_entropy_spike",
    "n_ext_change",
    "mean_entropy",
    "max_entropy",
    "n_dirs",
    "files_per_sec",
    "canary_hit",
]


def features(events: list[dict], cfg: dict) -> dict:
    counts = {
        f"n_{action}": sum(e["action"] == action for e in events)
        for action in ("modified", "created", "deleted", "moved")
    }
    paths = {e["path"] for e in events}
    hs = [e["entropy"] for e in events if e["entropy"] is not None]
    counts.update(
        n_unique_files=len(paths),
        n_entropy_spike=sum(entropy_spike(e, cfg) for e in events),
        n_ext_change=sum(extension_change(e, cfg) for e in events),
        mean_entropy=sum(hs) / len(hs) if hs else 0,
        max_entropy=max(hs, default=0),
        n_dirs=len({str(Path(p).parent) for p in paths}),
        files_per_sec=len(paths) / cfg["window_seconds"],
        canary_hit=int(any(e["isCanary"] and e["action"] != "created" for e in events)),
    )
    return counts


def vector(values: dict) -> list[float]:
    return [values[name] for name in FEATURE_NAMES]
