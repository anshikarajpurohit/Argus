"""Harmless copy/rename operations restricted to disposable manifest fixtures."""

import argparse
import json
import random
import shutil
import time
from pathlib import Path
from common import TESTBED, OUT, sandbox


def run(mode: str, target: Path, seed: int, count: int) -> None:
    target = sandbox(target)
    rng = random.Random(seed)
    manifest = json.loads(sandbox(target / "MANIFEST.json").read_text())
    files = [
        sandbox(TESTBED / item["path"])
        for item in manifest
        if item["label"] == "benign_text"
    ]
    if any(not p.is_relative_to(target) for p in files):
        raise ValueError("Manifest contains paths outside target")
    rng.shuffle(files)
    start = time.time()
    touched = 0
    if mode == "canary":
        p = sandbox(target / "_important_passwords.txt")
        if not p.is_file():
            raise ValueError("Start the agent to create canaries first")
        with p.open("a") as f:
            f.write("Harmless tripwire test.\n")
        touched = 1
    else:
        pool = OUT / "noise_pool"
        if pool.is_symlink() or pool.resolve() != pool.absolute():
            raise ValueError("Invalid noise pool")
        sources = sorted(pool.glob("*.bin"))
        if mode in ("fast", "slow") and not sources:
            raise ValueError("Run make_fixtures.py first")
        for i in range(count):
            path = sandbox(files[i % len(files)])
            if not path.is_file():
                continue
            if mode == "benign":
                with path.open("a") as f:
                    f.write("Ordinary document editing.\n")
            elif mode == "rename":
                path.rename(sandbox(path.with_suffix(".locked")))
            else:
                source = rng.choice(sources)
                if source.is_symlink() or source.resolve().parent != pool:
                    raise ValueError("Invalid noise payload")
                shutil.copyfile(source, path)
                if mode == "fast":
                    path.rename(sandbox(path.with_suffix(".locked")))
            touched += 1
            if i + 1 < count:
                time.sleep({"fast": 0.05, "slow": 2, "rename": 0.05, "benign": 3}[mode])
    print(
        json.dumps(
            {"mode": mode, "filesTouched": touched, "start": start, "end": time.time()}
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--target", type=Path, default=TESTBED)
    p.add_argument(
        "--mode", choices=["fast", "slow", "rename", "canary", "benign"], default="fast"
    )
    p.add_argument("--count", type=int, default=60)
    p.add_argument("--i-understand-this-is-a-sandbox", action="store_true")
    a = p.parse_args()
    if not a.i_understand_this_is_a_sandbox:
        p.error("Requires --i-understand-this-is-a-sandbox")
    try:
        run(a.mode, a.target, a.seed, a.count)
    except (ValueError, OSError) as error:
        p.error(str(error))
