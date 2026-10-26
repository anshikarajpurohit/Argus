# Reproducible synthetic data

Run from the repository root with the virtual environment active:

```sh
python dataset/make_fixtures.py --seed 42
python dataset/generate_events.py --seed 42 --runs 30
python dataset/train_model.py --seed 42
python dataset/replay_evaluation.py
```

`make_fixtures` creates 150 text-like fixtures, 10 ZIP files, 10 random binary files named JPG/PNG (not decodable images), and a SHA-256 manifest. Its `--count` option changes the text-file count. ZIP timestamps are fixed for reproducibility. Forty deterministic high-entropy copy payloads are written to `dataset/out/noise_pool`. All files in `testbed/` are disposable.

`generate_events` emits 390 JSONL streams, each covering 300 simulated seconds, and `labels.csv`. UUIDs and byte content are seeded; paths in event streams use `/argus/testbed/` to remain stable between machines. Malicious-like intervals begin at second 60; earlier windows in those runs are benign. Build bursts use one project directory and archive backups reuse archive paths. Generation does not sleep or mutate real monitored files.

`train_model` uses the runtime's exact 12-feature extraction function, ten-second windows, two-second steps, and run-level 70/30 splitting. A window is positive when it overlaps a labeled interval by at least three seconds. Output is `agent/models/rf_model.joblib`, plus `dataset/out/ml_report.md` and `split.json`. The held-out test set is not used for tuning. The model and streams are git-ignored.

## Harmless live emulator

```sh
python dataset/attack_emulator.py --mode fast --count 60 --seed 42 --i-understand-this-is-a-sandbox
python dataset/attack_emulator.py --mode slow --count 8 --seed 42 --i-understand-this-is-a-sandbox
python dataset/attack_emulator.py --mode rename --count 60 --seed 42 --i-understand-this-is-a-sandbox
python dataset/attack_emulator.py --mode canary --seed 42 --i-understand-this-is-a-sandbox
python dataset/attack_emulator.py --mode benign --count 201 --seed 42 --i-understand-this-is-a-sandbox
```

Fast mode copies random payloads and renames; slow mode copies one payload every two seconds; rename mode only renames; canary mode appends one harmless line; benign mode appends an ordinary line every three seconds. Canary mode requires a running agent's canary file. No network calls, encryption, malware, or ransom notes occur in the emulator.

`--target` must resolve inside this repository's `testbed/`. The emulator checks every manifest destination and rejects symlink escapes. Noise inputs are read only from `dataset/out/noise_pool`. Fresh targets are preferred for benchmarks, because the fixture generator does not erase unrelated files left by prior runs.

See [run_e2e.md](run_e2e.md) for timing and overhead measurements.
