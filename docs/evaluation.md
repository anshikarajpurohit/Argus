# Evaluation and acceptance status

Measured on 26 October 2026. The implementation includes all application components from the SRS. Not every detection target is satisfied; the distinctions below are intentional.

## Environment and scope

Local live tests: macOS arm64, Python 3.14, Node 24.22.0, MongoDB 8.0.34, watchdog's polling observer (0.5-second interval). Windows and Linux use native watchdog observers. GitHub Actions successfully ran Python tests on Windows and Linux, plus API integration tests, dashboard tests, lint, and production build on Linux. This does not establish native Windows/Linux live detection performance.

All tests used synthetic events or disposable sandbox fixtures. Suspension was mocked; no real process was suspended. No malware or file-encrypting emulator was used.

## Automated and manual checks

| Check | Result |
|---|---|
| Python agent/dataset tests | 25 passed locally |
| Backend Jest integration tests | 8 passed against real MongoDB |
| Dashboard Vitest tests | 10 passed (helpers and all six pages) |
| ESLint | Backend and dashboard passed |
| Vite production build | Passed; upstream directive/chunk-size warnings are non-fatal |
| Seeded synthetic generation | 390 streams; byte-identical streams and labels after regeneration |
| Train/test separation | Run IDs disjoint; 273 training / 117 test runs |
| Browser login | Invalid login displayed an error; valid login entered Overview |
| Browser settings | Values loaded and save confirmed; alert-only preserved |
| Browser event filtering | Selecting moved returned rename records |
| Browser live data | Overview counts and alerts updated while emulation ran |
| Vault | Byte-identical decryption, wrong-password/tamper rejection, random salt/IV, oversized upload rejection |
| Backend outage | Ten created-file events delivered once after restart |
| Canary read/delete | Read produced no alert; deletion alerted and file was recreated |

Backend and dashboard results include the combined Express/Socket.IO server fix. Startup FSEvents artifacts found during development were excluded from final timing trials; final trials use fresh directories and the Mac polling observer. Reports describe first alert timestamp, not time of rendering in the browser.

## Live latency: ten fresh-directory trials per mode

The model is enabled, thresholds are 40/70, and response mode is alert-only. The benchmark waits for agent startup before the timed workload. Null latency represents no detection, not zero seconds.

| Mode | Runs with alerts | Critical runs | First-alert median / max (s) | First-Critical median / max (s) |
|---|---:|---:|---:|---:|
| fast | 10/10 | 10/10 | 0.942 / 0.983 | 2.959 / 3.048 |
| slow | 10/10 | 10/10 | 9.035 / 9.120 | 9.035 / 9.120 |
| rename | 0/10 | 0/10 | — | — |
| canary | 10/10 | 10/10 | 0.990 / 1.050 | 0.990 / 1.050 |

Idle CPU: **4.01%** of one logical CPU on average over 60.0 seconds with 1,000 text fixtures, additional high-entropy fixtures, and canaries. This meets the <10% target on this machine.

Live benign editing: **0 alerts** over **601.7 seconds**. This is a ten-minute observation, not proof of long-term real-world false-positive performance.

## Synthetic replay and model performance

See [the replay table](replay_report.md) for all 13 scenarios with and without ML. Across 210 benign five-minute runs (17.5 simulated hours), both configurations produced zero alerts. Build bursts deliberately remain within one project directory and backup events use archive paths; more diverse real workloads can behave differently.

The held-out synthetic model achieved 0.9995 accuracy, 1.0000 precision, 0.9986 recall, and 0.9993 F1. See [the full model report](ml_report.md) for the confusion matrix and feature importances. The model is trained on synthetic data; real-world performance is unknown. No test-set tuning was performed.

## Unmet targets and limitations

- **Phase 6 M3 Critical requirement is not met by the specified rules.** Rename-only events get 20 extension points plus at most 10 spread points. The 30-point ML addition still cannot guarantee the 70-point Critical threshold. Rules were not changed to manufacture a passing result.
- **A universal six-second alert target is not met.** Slow activity may need five spikes over roughly eight seconds before scoring, plus the scoring interval and observer delay. Fast and canary latency must be assessed separately from this scenario.
- Live rename-only changes produced no alert in the ten measured trials. The ML warning seen in synthetic M3 replay did not generalize to the smaller live rename workload.
- M4 write-then-delete is not detected by rules alone in the synthetic replay; the ML signal raises warnings. The specified scoring design has real coverage gaps.
- Canary read detection is unsupported. The UI and documentation do not claim it.
- The live benchmark measures a local prototype, not resistance to a real adversary or guaranteed interruption before file damage.
- Queues are bounded and memory-only. Backend restarts are supported; agent shutdown/crash is not durable. Oldest events are dropped at the 5,000-event cap.
- Python source targets 3.10+ syntax, but the pinned latest dependency set requires Python 3.12+.

## Phase traceability

| Phase | Implementation and evidence |
|---|---|
| 0 Setup | Repository layout, pinned installs, test/build commands, local configuration examples |
| 1 Backend | Auth, validation, models/indexes/TTL, routes, sockets; Jest integration |
| 2 Watcher/transport | Native Windows/Linux watcher, Mac polling, debounce, ignore paths, real outage recovery |
| 3 Dataset | Deterministic fixtures and 390 streams; guarded copy/rename emulator |
| 4 Entropy | Known entropy distributions, cache transitions, format exclusions, extension rules |
| 5 Canary | Creation/state/restart checks; live read/delete/recreation; startup regression |
| 6 Scoring/response | Shared features, configurable rules, dedup, protected-process mocks; M3 conflict explicitly unmet |
| 7 Dashboard | Six pages, session authentication, live refresh, manual browser validation and page rendering tests |
| 8 Vault | AES-256-GCM, scrypt, random salt/IV, metadata and UI; round-trip/tamper/size tests |
| 9 ML | Optional model, run-level split, metrics/report, rules-versus-ML replay |
| 10 Evaluation | Live timing, idle CPU, benign observation, API examples, setup and limitations |

Raw non-secret measurement summaries are in `live_results.json`, `recovery_results.json`, and `dataset_verification.json`. Generated datasets, trained models, runtime logs, and credentials remain ignored.
