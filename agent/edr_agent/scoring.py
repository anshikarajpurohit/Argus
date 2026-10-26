"""Configurable scoring, thresholding, and per-severity deduplication."""

import uuid
from .features import features


class Scorer:
    def __init__(self, cfg: dict):
        self.cfg, self.last = cfg, {}

    def score(
        self, values: dict, probability: float | None = None
    ) -> tuple[int, list[str]]:
        s = self.cfg["scoring"]
        points = 0
        reasons = []
        checks = [
            ("canary_touched", values["canary_hit"] == 1, s["canary_hit"]),
            (
                "mass_modify",
                values["n_modified"] >= s["mass_modify"]["min_count"],
                s["mass_modify"]["points"],
            ),
            (
                "entropy_spike",
                values["n_entropy_spike"] >= s["entropy_spike"]["min_count"],
                s["entropy_spike"]["points"],
            ),
            (
                "ext_change",
                values["n_ext_change"] >= s["ext_change"]["min_count"],
                s["ext_change"]["points"],
            ),
            (
                "mass_delete",
                values["n_deleted"] >= s["mass_delete"]["min_count"],
                s["mass_delete"]["points"],
            ),
            (
                "wide_spread",
                values["n_dirs"] >= s["wide_spread"]["min_dirs"]
                and values["n_unique_files"] >= s["wide_spread"]["min_files"],
                s["wide_spread"]["points"],
            ),
            (
                "ml_high_probability",
                probability is not None and probability >= s["ml"]["min_probability"],
                s["ml"]["points"],
            ),
        ]
        for reason, hit, amount in checks:
            if hit:
                points += amount
                reasons.append(reason)
        return min(100, points), reasons

    def alert(
        self,
        events: list[dict],
        now: float,
        settings: dict,
        probability: float | None = None,
        immediate: bool = False,
    ) -> dict | None:
        if not events:
            return None
        score, reasons = self.score(features(events, self.cfg), probability)
        severity = (
            "CRITICAL"
            if score >= settings["criticalThreshold"]
            else "WARNING" if score >= settings["warningThreshold"] else None
        )
        if severity is None:
            return None
        if not immediate and now - self.last.get(severity, float("-inf")) < 30:
            return None
        self.last[severity] = now
        return dict(
            alertId=str(uuid.uuid4()),
            agentId=self.cfg["agent_id"],
            ts=now,
            severity=severity,
            score=score,
            reasons=reasons,
            mlProbability=probability,
            affectedFiles=list(dict.fromkeys(e["path"] for e in events))[:50],
            suspectPid=None,
            suspectProcess=None,
            responseTaken="none",
            status="open",
        )
