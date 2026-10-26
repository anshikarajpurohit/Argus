# Synthetic replay evaluation

390 five-minute runs. Rules and thresholds were not changed to fit acceptance expectations.

| Scenario | Rules: runs with alerts | Rules: Critical runs | ML: runs with alerts | ML: Critical runs |
|---|---:|---:|---:|---:|
| B1 | 0/30 | 0/30 | 0/30 | 0/30 |
| B2 | 0/30 | 0/30 | 0/30 | 0/30 |
| B3 | 0/30 | 0/30 | 0/30 | 0/30 |
| B4 | 0/30 | 0/30 | 0/30 | 0/30 |
| B5 | 0/30 | 0/30 | 0/30 | 0/30 |
| B6 | 0/30 | 0/30 | 0/30 | 0/30 |
| B7 | 0/30 | 0/30 | 0/30 | 0/30 |
| M1 | 30/30 | 30/30 | 30/30 | 30/30 |
| M2 | 30/30 | 0/30 | 30/30 | 30/30 |
| M3 | 0/30 | 0/30 | 30/30 | 0/30 |
| M4 | 0/30 | 0/30 | 30/30 | 0/30 |
| M5 | 30/30 | 30/30 | 30/30 | 30/30 |
| M6 | 30/30 | 30/30 | 30/30 | 30/30 |

Benign false alerts with ML=False: 0 over 17.50 simulated hours (0.000/hour).

Benign false alerts with ML=True: 0 over 17.50 simulated hours (0.000/hour).

The generator constrains build paths to one project directory and backups to archive paths; these rates describe these fixtures only. Replay uses fixed scoring ticks. Real filesystem coalescing, startup baseline races, and scheduling can differ.

Rename-only activity cannot reach the specified Critical threshold from extension points alone; adding the ML contribution does not guarantee Critical. Slow attacks cannot universally meet a six-second latency threshold. These are specification conflicts, not hidden changes to scoring.
