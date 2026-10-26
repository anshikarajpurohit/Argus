"""Create disposable files and pre-generated random-byte copy payloads."""

import argparse
import hashlib
import json
import random
import zipfile
from pathlib import Path
from common import TESTBED, sandbox, output_dir

WORDS = "the clear river flows past green trees under a calm blue sky people write notes read books and share useful work every day".split()
FOLDERS = ["docs", "photos", "projects", "finance", "archive", "misc"]


def generate(seed: int = 42, count: int = 150, target: Path = TESTBED) -> list[dict]:
    target = sandbox(target)
    target.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    records = []
    texts = []

    def save(path: Path, data: bytes, label: str) -> None:
        path = sandbox(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        records.append(
            {
                "path": path.relative_to(TESTBED).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "label": label,
            }
        )

    for i in range(count):
        ext = [".txt", ".md", ".csv", ".json", ".log"][i % 5]
        path = target / FOLDERS[i % 6] / "team" / "records" / f"fixture_{i:03}{ext}"
        size = rng.randint(1024, 50 * 1024)
        data = (" ".join(rng.choices(WORDS, k=size // 3 + 1))).encode()[:size]
        save(path, data, "benign_text")
        texts.append(data)
    for i in range(10):
        import io

        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            info = zipfile.ZipInfo("notes.txt", date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, texts[i % len(texts)])
        save(
            target / "archive" / "team" / "records" / f"archive_{i:02}.zip",
            stream.getvalue(),
            "benign_high_entropy",
        )
        save(
            target
            / "photos"
            / "team"
            / "records"
            / f'image_{i:02}.{["jpg","png"][i%2]}',
            rng.randbytes(8192),
            "benign_high_entropy",
        )
    pool = output_dir() / "noise_pool"
    if pool.is_symlink():
        raise ValueError("Noise pool must not be a symlink")
    pool.mkdir(exist_ok=True)
    for i in range(40):
        path = pool / f"noise_{i:02}.bin"
        if path.is_symlink():
            raise ValueError("Noise payload must not be a symlink")
        path.write_bytes(rng.randbytes(rng.randint(4096, 32768)))
    sandbox(target / "MANIFEST.json").write_text(json.dumps(records, indent=2) + "\n")
    return records


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--count", type=int, default=150)
    p.add_argument("--target", type=Path, default=TESTBED)
    a = p.parse_args()
    if a.count < 1:
        p.error("--count must be positive")
    try:
        print(f"Created {len(generate(a.seed,a.count,a.target))} fixture files")
    except ValueError as error:
        p.error(str(error))
