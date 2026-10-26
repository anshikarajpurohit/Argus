"""Validated local configuration. Relative watch paths use the repository root."""

import os
from pathlib import Path
from urllib.parse import urlparse
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict:
    cfg = yaml.safe_load(path.read_text())
    if not isinstance(cfg, dict):
        raise ValueError("Configuration must be a mapping")
    for key in (
        "agent_id",
        "backend_url",
        "agent_api_key",
        "watch_paths",
        "scoring",
        "canary_names",
        "known_ext",
        "suspicious_ext",
        "high_entropy_ok_ext",
        "ignore_patterns",
    ):
        if key not in cfg:
            raise ValueError(f"Missing {key}")
    cfg["agent_api_key"] = os.environ.get("AGENT_API_KEY", cfg["agent_api_key"])
    if not cfg["agent_api_key"] or cfg["agent_api_key"] == "CHANGE_ME":
        raise ValueError("Set AGENT_API_KEY in the environment or config")
    if urlparse(cfg["backend_url"]).scheme not in ("http", "https"):
        raise ValueError("backend_url must use HTTP or HTTPS")
    for key in (
        "window_seconds",
        "score_interval_seconds",
        "entropy_sample_bytes",
        "entropy_min_file_bytes",
    ):
        if not isinstance(cfg.get(key), (int, float)) or cfg[key] <= 0:
            raise ValueError(f"{key} must be positive")
    if not 0 <= cfg["warningThreshold"] < cfg["criticalThreshold"] <= 100:
        raise ValueError("Invalid thresholds")
    if not isinstance(cfg["watch_paths"], list) or not cfg["watch_paths"]:
        raise ValueError("watch_paths must be a nonempty list")
    for name in cfg["canary_names"]:
        if Path(name).name != name or name in (".", ".."):
            raise ValueError("Canary names must be filenames")
    if not all(isinstance(p, str) and p for p in cfg["watch_paths"]):
        raise ValueError("watch_paths must contain nonempty strings")
    for key in (
        "canary_names",
        "known_ext",
        "suspicious_ext",
        "high_entropy_ok_ext",
        "ignore_patterns",
        "processAllowlist",
    ):
        if not isinstance(cfg.get(key), list) or not all(
            isinstance(v, str) for v in cfg[key]
        ):
            raise ValueError(f"{key} must be a list of strings")
    if cfg.get("responseMode") not in ("alert_only", "suspend"):
        raise ValueError("Invalid responseMode")
    if (
        not 0 <= cfg.get("entropy_spike_min", -1) <= 8
        or not 0 <= cfg.get("entropy_spike_delta", -1) <= 8
    ):
        raise ValueError("Invalid entropy thresholds")
    if not isinstance(cfg.get("agent_id"), str) or not cfg["agent_id"]:
        raise ValueError("agent_id must be a nonempty string")
    scoring = cfg["scoring"]
    required = {
        "mass_modify": ["min_count", "points"],
        "entropy_spike": ["min_count", "points"],
        "ext_change": ["min_count", "points"],
        "mass_delete": ["min_count", "points"],
        "wide_spread": ["min_dirs", "min_files", "points"],
        "ml": ["min_probability", "points"],
    }
    if not isinstance(scoring, dict) or not isinstance(
        scoring.get("canary_hit"), (int, float)
    ):
        raise ValueError("Invalid scoring configuration")
    for rule, fields in required.items():
        if not isinstance(scoring.get(rule), dict) or any(
            not isinstance(scoring[rule].get(field), (int, float))
            or scoring[rule][field] < 0
            for field in fields
        ):
            raise ValueError(f"Invalid scoring rule {rule}")
    if (
        not 0 <= scoring["canary_hit"] <= 100
        or not 0 <= scoring["ml"]["min_probability"] <= 1
    ):
        raise ValueError("Invalid scoring bounds")
    cfg["watch_paths"] = [str((ROOT / p).resolve()) for p in cfg["watch_paths"]]
    cfg["ml_model_path"] = str((ROOT / "agent" / cfg["ml_model_path"]).resolve())
    cfg["excluded_paths"] = [
        str(path.resolve()),
        str(ROOT / "agent/state"),
        str(ROOT / "backend/vault_store"),
    ]
    return cfg
