"""Measure the real agent against a running local backend using fresh fixture directories.

No suspension is enabled. Authentication is read from environment variables.
The optional benign workload runs on a separate agent and never shares attack paths.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

import psutil
import requests
import yaml
from common import ROOT, TESTBED, output_dir
from make_fixtures import generate


def benchmark(args: argparse.Namespace) -> None:
    output = output_dir()
    tag = uuid.uuid4().hex[:10]
    runtime = output / ("benchmark_" + tag)
    runtime.mkdir()
    key = os.environ["AGENT_API_KEY"]
    response = requests.post(
        args.backend + "/api/auth/login",
        json={
            "username": os.environ["ADMIN_USER"],
            "password": os.environ["ADMIN_PASS"],
        },
        timeout=5,
    )
    response.raise_for_status()
    headers = {"Authorization": "Bearer " + response.json()["token"]}
    settings = requests.get(
        args.backend + "/api/settings", headers=headers, timeout=5
    ).json()
    if settings["responseMode"] != "alert_only":
        raise ValueError(
            "Benchmark requires alert_only mode; it does not change settings"
        )
    report = {
        "platform": sys.platform,
        "seed": args.seed,
        "runs": args.runs,
        "trials": [],
    }
    errors = []

    def read_alerts(agent_id: str) -> list[dict]:
        response = requests.get(
            args.backend + "/api/alerts?limit=500", headers=headers, timeout=5
        )
        response.raise_for_status()
        return [a for a in response.json() if a["agentId"] == agent_id]

    def launch(name: str, target: Path):
        cfg = yaml.safe_load((ROOT / "agent/config.yaml").read_text())
        cfg.update(
            agent_id=name,
            backend_url=args.backend,
            agent_api_key=key,
            watch_paths=[str(target)],
            ml_model_path=str(ROOT / "agent/models/rf_model.joblib"),
        )
        config_path = runtime / (name + ".yaml")
        config_path.write_text(yaml.safe_dump(cfg))
        config_path.chmod(0o600)
        log_path = runtime / (name + ".log")
        handle = log_path.open("w")
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "agent/main.py"), "--config", str(config_path)],
            cwd=ROOT,
            stdout=handle,
            stderr=subprocess.STDOUT,
        )
        for _ in range(300):
            if process.poll() is not None:
                raise RuntimeError("Agent exited: " + log_path.read_text())
            if "Monitoring " in log_path.read_text():
                # Drain any platform startup notifications before timing a workload.
                time.sleep(3)
                return process, handle
            time.sleep(0.1)
        process.terminate()
        raise RuntimeError("Agent startup timeout")

    def stop(pair):
        process, handle = pair
        process.terminate()
        process.wait(timeout=15)
        handle.close()

    def emulate(target: Path, mode: str, count: int, seed: int) -> dict:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "dataset/attack_emulator.py"),
                "--target",
                str(target),
                "--mode",
                mode,
                "--count",
                str(count),
                "--seed",
                str(seed),
                "--i-understand-this-is-a-sandbox",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    def save():
        (output / args.report).write_text(json.dumps(report, indent=2) + "\n")

    benign = None
    if args.benign_seconds > 0 or args.idle_seconds > 0:
        target = TESTBED / ("benchmark_" + tag) / "benign"
        generate(args.seed, 1000, target)
        benign_target = target
        benign = launch("bench-" + tag + "-benign", benign_target)

        def benign_work():
            try:
                process = psutil.Process(benign[0].pid)
                before = sum(process.cpu_times()[:2])
                started = time.monotonic()
                if args.idle_seconds:
                    time.sleep(args.idle_seconds)
                elapsed = time.monotonic() - started
                report["idle"] = {
                    "seconds": elapsed,
                    "files": 1000,
                    "cpuPercent": 100
                    * (sum(process.cpu_times()[:2]) - before)
                    / elapsed,
                }
                if args.benign_seconds:
                    result = emulate(
                        benign_target,
                        "benign",
                        int(args.benign_seconds / 3) + 1,
                        args.seed,
                    )
                    time.sleep(3)
                    records = [
                        a
                        for a in read_alerts("bench-" + tag + "-benign")
                        if a["ts"] >= result["start"]
                    ]
                    report["benign"] = {
                        "seconds": result["end"] - result["start"],
                        "alerts": len(records),
                        "filesTouched": result["filesTouched"],
                    }
                    if result["end"] - result["start"] < args.benign_seconds * 0.95:
                        raise RuntimeError(
                            "Benign workload ended before its requested duration"
                        )
            except Exception as error:
                errors.append(str(error))
            finally:
                stop(benign)

        thread = threading.Thread(target=benign_work)
        thread.start()
    try:
        for mode in ["fast", "slow", "rename", "canary"]:
            for run in range(args.runs):
                target = TESTBED / ("benchmark_" + tag) / f"{mode}_{run:02}"
                generate(args.seed + run, 150, target)
                name = f"bench-{tag}-{mode}-{run:02}"
                agent = launch(name, target)
                try:
                    summary = emulate(
                        target, mode, 8 if mode == "slow" else 60, args.seed + run
                    )
                    time.sleep(3)
                    records = [
                        a for a in read_alerts(name) if a["ts"] >= summary["start"]
                    ]
                    latencies = [a["ts"] - summary["start"] for a in records]
                    critical = [
                        a["ts"] - summary["start"]
                        for a in records
                        if a["severity"] == "CRITICAL"
                    ]
                    trial = {
                        "mode": mode,
                        "run": run,
                        "latencySeconds": min(latencies, default=None),
                        "criticalLatencySeconds": min(critical, default=None),
                        "severities": sorted({a["severity"] for a in records}),
                        "alerts": len(records),
                        "filesTouched": summary["filesTouched"],
                    }
                    report["trials"].append(trial)
                    print(json.dumps(trial), flush=True)
                    save()
                finally:
                    stop(agent)
    finally:
        if benign:
            thread.join()
        report["errors"] = errors
        save()
    if errors:
        raise RuntimeError("; ".join(errors))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="http://127.0.0.1:5000")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--idle-seconds", type=int, default=60)
    parser.add_argument("--benign-seconds", type=int, default=600)
    parser.add_argument("--report", default="benchmark_report.json")
    args = parser.parse_args()
    if Path(args.report).name != args.report:
        parser.error("--report must be a filename")
    benchmark(args)
