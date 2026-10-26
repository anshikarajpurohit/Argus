# End-to-end evaluation

1. Install dependencies, start MongoDB and the backend, seed an administrator, and start the dashboard using the root README.
2. Generate fixtures, streams, and the model. Leave response mode `alert_only`.
3. Set `AGENT_API_KEY`, `ADMIN_USER`, and `ADMIN_PASS` in the benchmark shell environment. These are only used against your local backend.
4. Run `python dataset/benchmark_live.py --backend http://127.0.0.1:5000 --runs 10 --seed 42`.
5. Read `dataset/out/benchmark_report.json`. It contains ten fresh-directory trials for each fast/slow/rename/canary mode, first-alert and first-Critical latencies, a 60-second CPU sample with 1,000 files, and a 600-second benign append workload. `null` means no alert observed, not zero latency. A separate benign agent prevents attack events from affecting its scoring. No suspension is enabled.
6. Confirm in the browser that new alerts appear without refresh; inspect details, acknowledge a test alert, filter event actions/canaries/time, save settings, and exercise vault upload/decrypt/delete with a disposable file.
7. Test backend downtime separately: stop the API, create ten files, restart it with the same secrets/database, and confirm those UUIDs arrive once. In-memory queues survive backend failure but not agent shutdown.
8. For canary restoration, delete a registered canary while the agent runs. Verify an immediate Critical alert and recreation about five seconds later. Reading a canary must produce no alert.

The benchmark starts and stops only its own agents. It creates fresh subdirectories under `testbed/benchmark_<id>/` and secret-bearing runtime YAML under ignored `dataset/out/benchmark_<id>/`. Do not commit generated runtime artifacts. It does not start your database/backend or delete your monitoring data.

Run `python dataset/replay_evaluation.py` for the longer simulated benign evaluation and the with/without-ML comparison. Live and simulated results are different evidence; report them separately. Report missed latency targets and absent detections explicitly. Repeat platform-specific validation on Windows and Linux before claiming those platforms have been verified.
