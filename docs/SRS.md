# Software Requirements Specification: Mini-EDR
## Ransomware Detection and Secure File Protection System

Version 1.0 | Audience: AI coding assistant (Astra) and the human developer

---

## 0. Rules for the AI builder (READ FIRST)

1. Build **only** what this document specifies. Do not add features, services, or libraries that are not listed.
2. Work **one phase at a time** (Section 10). Do not start Phase N+1 until every acceptance test of Phase N passes.
3. Use **only** the libraries named in Section 3.3. If you need another one, STOP and ask the developer. Never invent a package name, function name, or API. If unsure whether a function exists, check the official documentation or ask.
4. Every config value, threshold, field name, endpoint, and file path in this document is **normative**. Use the exact names given.
5. If any requirement is ambiguous or missing, write the question under "OPEN QUESTIONS" in `docs/open_questions.md` and ask. Do not guess.
6. Pin dependency versions in `requirements.txt` / `package-lock.json` after installing the latest stable releases. Do not hard-code version numbers from memory.
7. **Safety rule:** This project is purely defensive. Do NOT write, download, or run real malware or real ransomware. Do NOT implement any file-encrypting code other than the Vault (Section 5.7), which only encrypts files the user explicitly submits. Testing uses only the synthetic data and harmless file copies described in Section 9.
8. After each phase, output: (a) files created/changed, (b) how to run, (c) results of the acceptance tests, (d) known limitations.
9. Write unit tests for every module (pytest for Python, Jest or Vitest for Node/React).

---

## 1. Introduction

### 1.1 Purpose
A lightweight Endpoint Detection and Response (EDR) prototype that detects ransomware-like behavior on a monitored folder, raises alerts on a live web dashboard, optionally responds automatically, and offers an encrypted vault for protecting sensitive files.

### 1.2 Scope (IN)
- Real-time monitoring of one or more watched folders
- Entropy-based detection of file content turning "random" (encrypted-looking)
- Canary (decoy) file tripwires
- Behavioral scoring over a sliding time window
- ML classifier (Random Forest) as an additional signal
- Alerting, event history, and statistics on a React dashboard
- Optional automatic response (suspend suspicious process)
- Secure vault (AES-256-GCM) for user-submitted files
- Synthetic dataset generator and test harness

### 1.3 Scope (OUT)
- Kernel drivers, system-call hooking, or anything requiring admin/root privileges for detection
- Network traffic analysis, email filtering, or antivirus signature scanning
- Real malware samples; any offensive tooling
- Multi-machine fleet management (a single agent is enough; the design allows more later)
- Cloud deployment, mobile apps

### 1.4 Definitions
| Term | Meaning |
|---|---|
| Agent | Python program running on the monitored machine; watches files and sends events |
| Event | One file-system action (create, modify, delete, rename) with metadata |
| Window | A sliding 10-second period of events used for scoring |
| Entropy | Shannon entropy of file bytes, 0 to 8 bits per byte. About 8 means random/encrypted/compressed |
| Canary | A decoy file no legitimate user should touch |
| Alert | A record created when the risk score crosses a threshold or a canary is touched |

### 1.5 Environment assumptions
- Development OS: Windows 10/11 or Linux. Code must run on both (use `pathlib`, no OS-specific calls unless guarded).
- Python 3.10 or newer. Node.js LTS. MongoDB (local install or Atlas free tier).
- Agent runs without administrator rights. Because of this, **process attribution is best-effort only** (see 5.5).

---

## 2. Overall description

### 2.1 Users
- **Admin (single role):** logs into the dashboard, views alerts/events, configures the response mode, manages vault files.
- **Agent:** non-human client authenticated with an API key.

### 2.2 Constraints
- Must work on a student laptop; CPU use of the agent under 10% average while idle-monitoring.
- No paid services. All components free/open source.

### 2.3 Key limitation to document honestly
User-space file watching cannot reliably identify which process changed a file. The system therefore records a "suspect process" only when it can be found with `psutil` (open file handles), and marks the field `null` otherwise. Do not claim certainty.

---

## 3. System architecture

### 3.1 Component diagram

```
 +---------------------- Monitored machine ----------------------+
 |  Watched folder(s)                                              |
 |        |  file events (watchdog)                                |
 |        v                                                        |
 |  +-----------------------------+                                |
 |  | AGENT (Python)              |                                |
 |  |  watcher -> analyzer        |                                |
 |  |  (entropy, ext, canary)     |                                |
 |  |  -> window aggregator       |                                |
 |  |  -> scoring engine + ML     |                                |
 |  |  -> responder (optional)    |                                |
 |  +--------------+--------------+                                |
 +-----------------|-----------------------------------------------+
                   | HTTP POST (batched JSON, header x-agent-key)
                   v
 +-----------------------------+      Socket.IO       +---------------------+
 | BACKEND (Node + Express)    | -------------------> | DASHBOARD (React)   |
 |  REST API, auth, Vault svc  | <------------------- |  live alerts, stats |
 |  MongoDB (events, alerts,   |    REST (JWT)        |  vault UI, settings |
 |  vault metadata, settings)  |                      +---------------------+
 +-----------------------------+
```

### 3.2 Data flow
1. Watchdog emits a raw file event.
2. Agent analyzer enriches it (size, extension, entropy, canary flag) and builds an **Event** (Section 4.1).
3. Events are buffered and POSTed to the backend every 2 seconds in a batch (max 200 events per batch).
4. Agent's aggregator keeps a 10-second sliding window; scoring engine computes a **risk score** every 2 seconds.
5. If score crosses a threshold, or a canary is touched, the agent creates an **Alert** and POSTs it immediately.
6. Backend stores everything in MongoDB and pushes new alerts/events to dashboards via Socket.IO.
7. If response mode is `suspend`, the agent's responder acts on the suspect process (5.5).

### 3.3 Technology stack (fixed)
| Layer | Technology | Notes |
|---|---|---|
| Agent | Python 3.10+, `watchdog`, `psutil`, `requests`, `numpy`, `pandas`, `scikit-learn`, `joblib`, `PyYAML`, `pytest` | No other libraries |
| Backend | Node.js, `express`, `mongoose`, `socket.io`, `jsonwebtoken`, `bcryptjs`, `multer`, `dotenv`, `cors`, `helmet`, `express-rate-limit`, `zod`; Node built-in `crypto` for vault | Use Jest for tests |
| Database | MongoDB | via mongoose |
| Dashboard | React (Vite), `socket.io-client`, `axios`, `react-router-dom`, `recharts`, plain CSS or Tailwind | Vitest for tests |

### 3.4 Repository layout
```
mini-edr/
  README.md
  docs/
    SRS.md                  (this file)
    open_questions.md
  agent/
    config.yaml
    requirements.txt
    main.py
    edr_agent/
      __init__.py
      watcher.py
      analyzer.py           (entropy, extension rules, canary check)
      canary.py
      window.py             (sliding window aggregator)
      features.py           (feature extraction, shared by runtime + training)
      scoring.py
      ml_model.py
      responder.py
      transport.py          (batching, retries, POST to backend)
    tests/
  backend/
    package.json
    .env.example
    src/
      server.js
      config.js
      models/               (Event.js, Alert.js, VaultItem.js, Settings.js, Admin.js)
      routes/               (auth.js, events.js, alerts.js, stats.js, vault.js, settings.js)
      middleware/           (agentAuth.js, adminAuth.js, validate.js)
      services/             (vaultService.js, socket.js)
    tests/
  dashboard/
    package.json
    src/ (pages, components, api, socket)
  dataset/
    make_fixtures.py
    generate_events.py
    attack_emulator.py
    train_model.py
    README.md
    out/                    (generated, git-ignored)
  testbed/                  (generated, git-ignored; sandbox only)
```

---

## 4. Data models

### 4.1 Event (agent -> backend; stored in `events`)
| Field | Type | Description |
|---|---|---|
| `eventId` | string (UUID v4) | unique |
| `agentId` | string | from config |
| `ts` | number | Unix time in seconds (float) |
| `action` | enum | `created`, `modified`, `deleted`, `moved` |
| `path` | string | absolute path of file |
| `destPath` | string or null | new path for `moved` |
| `ext` | string | lower-case extension with dot, or `""` |
| `destExt` | string or null | extension after rename |
| `sizeBytes` | number or null | null if file is gone |
| `entropy` | number or null | 0.0-8.0; null if not computed (deleted, too small, unreadable) |
| `prevEntropy` | number or null | last known entropy of the same path from the agent's in-memory cache |
| `isCanary` | boolean | path is a registered canary |
| `suspectPid` | number or null | best-effort |
| `suspectProcess` | string or null | best-effort process name |

### 4.2 Alert (stored in `alerts`)
| Field | Type | Description |
|---|---|---|
| `alertId` | string (UUID v4) | |
| `agentId` | string | |
| `ts` | number | |
| `severity` | enum | `WARNING`, `CRITICAL` |
| `score` | number | 0-100 |
| `reasons` | array of strings | e.g. `canary_touched`, `mass_modify`, `entropy_spike`, `ext_change`, `mass_delete`, `ml_high_probability` |
| `mlProbability` | number or null | 0.0-1.0 |
| `affectedFiles` | array of strings | max 50 paths |
| `suspectPid` / `suspectProcess` | number/string or null | |
| `responseTaken` | enum | `none`, `suspended`, `suspend_failed` |
| `status` | enum | `open`, `acknowledged`, `resolved` (default `open`) |

### 4.3 VaultItem (stored in `vaultitems`)
`itemId`, `originalName`, `storedName` (random UUID + `.vault`), `sizeBytes`, `createdAt`, `sha256Plaintext` (hex hash of the original file, for integrity check after decryption). **The password and the key are never stored.**

### 4.4 Settings (single document)
`responseMode` (`alert_only` | `suspend`, default `alert_only`), `warningThreshold` (default 40), `criticalThreshold` (default 70), `processAllowlist` (array of process names).

### 4.5 Admin
`username`, `passwordHash` (bcrypt). Created by a seed script `npm run seed:admin` reading `ADMIN_USER` / `ADMIN_PASS` from `.env`. No public registration endpoint.

---

## 5. Functional requirements

### 5.1 Agent: Watcher (FR-AGT)
- FR-AGT-1: Watch every folder in `config.yaml -> watch_paths`, recursively, using `watchdog`.
- FR-AGT-2: Convert watchdog events to the Event schema (4.1). Ignore directory events and any path matching `ignore_patterns` (default: `*.tmp`, `~$*`, `.git/*`, `__pycache__/*`).
- FR-AGT-3: Debounce: if the same path emits multiple `modified` events within 0.5 s, keep only the last.
- FR-AGT-4: Never crash on a vanished or locked file; catch `FileNotFoundError` / `PermissionError` and set size/entropy to null.
- FR-AGT-5: Agent must ignore its own log files and its own config.

### 5.2 Agent: Entropy and extension analysis (FR-ENT)
- FR-ENT-1: Shannon entropy over bytes: `H = -sum(p_i * log2(p_i))` over the 256 byte values; result 0-8.
- FR-ENT-2: Read at most the first **65,536 bytes** of a file (config `entropy_sample_bytes`). Skip files smaller than **512 bytes** (entropy = null).
- FR-ENT-3: Maintain an in-memory dict `path -> last entropy`. On each `modified`/`created` event, set `prevEntropy` from it, then update it.
- FR-ENT-4: An event is an **entropy spike** when ALL are true: `entropy >= 7.5` AND `prevEntropy is not null` AND `(entropy - prevEntropy) >= 2.0`, AND the file's extension is not in `high_entropy_ok_ext`.
- FR-ENT-5: `high_entropy_ok_ext` (naturally high-entropy formats, default): `.zip .gz .7z .rar .jpg .jpeg .png .mp3 .mp4 .mkv .pdf .docx .xlsx .pptx .webp`. For these, entropy alone never counts as a spike.
- FR-ENT-6: A **suspicious extension change** is a `moved` event where `destExt` differs from `ext` AND `destExt` is NOT in `known_ext` (a config list of common extensions) OR `destExt` is in `suspicious_ext` (default: `.locked .enc .encrypted .crypt .crypted .lock .xxx`). These strings are generic placeholders for testing; the list is configurable.

### 5.3 Agent: Canary files (FR-CAN)
- FR-CAN-1: On startup, for each watch path, create 3 decoy files inside it if missing: `_important_passwords.txt`, `_financial_records.csv`, `_backup_keys.docx.txt` (names configurable under `canary_names`). Contents: harmless plain text filler, 2-4 KB, generated once.
- FR-CAN-2: Store the canary file list and the SHA-256 of each in `agent/state/canaries.json`.
- FR-CAN-3: Any event on a canary path (`modified`, `deleted`, `moved`) sets `isCanary = true` and immediately triggers a CRITICAL alert with reason `canary_touched`. A `created` event during agent-initiated creation is ignored.
- FR-CAN-4: Opening/reading a canary cannot be detected by watchdog; do not claim it. Only modify/delete/move are detected.
- FR-CAN-5: Re-create a deleted canary 5 seconds after the alert so monitoring continues.

### 5.4 Agent: Window, scoring, ML (FR-SCR)
**Window (FR-SCR-1):** keep events of the last `window_seconds` (default 10). Every `score_interval_seconds` (default 2) compute these counters:

| Counter | Definition |
|---|---|
| `n_modified` | count of `modified` events |
| `n_created` | count of `created` events |
| `n_deleted` | count of `deleted` events |
| `n_moved` | count of `moved` events |
| `n_unique_files` | distinct paths touched |
| `n_entropy_spike` | events that satisfy FR-ENT-4 |
| `n_ext_change` | events that satisfy FR-ENT-6 |
| `mean_entropy` | mean of non-null entropy values (0 if none) |
| `max_entropy` | max of non-null entropy values (0 if none) |
| `n_dirs` | distinct parent directories touched |
| `files_per_sec` | `n_unique_files / window_seconds` |
| `canary_hit` | 1 if any canary event in window else 0 |

**Rule-based score (FR-SCR-2):** start at 0, add, then cap at 100:

| Condition | Points |
|---|---|
| `canary_hit == 1` | +100 |
| `n_modified >= 20` | +30 |
| `n_entropy_spike >= 5` | +40 |
| `n_ext_change >= 5` | +20 |
| `n_deleted >= 10` | +10 |
| `n_dirs >= 5` AND `n_unique_files >= 20` | +10 |

All numbers are read from `config.yaml -> scoring` (do not hard-code).

**ML signal (FR-SCR-3):** if a trained model file exists at `agent/models/rf_model.joblib`, compute `mlProbability` = `predict_proba` of the "ransomware-like" class on the feature vector (Section 9.5). If `mlProbability >= 0.8`, add **+30** to the score (before capping). If no model exists, skip silently and set `mlProbability = null`.

**Thresholds (FR-SCR-4):** `score >= criticalThreshold (70)` -> CRITICAL; `score >= warningThreshold (40)` -> WARNING; otherwise no alert. Thresholds are fetched from backend Settings every 30 s, with fallback to config.

**Alert de-duplication (FR-SCR-5):** at most one alert per severity per 30 seconds per agent, except `canary_touched`, which is always sent.

### 5.5 Agent: Responder (FR-RSP)
- FR-RSP-1: Default mode `alert_only`: no action besides the alert.
- FR-RSP-2: Mode `suspend` (set from dashboard): on a CRITICAL alert with a known `suspectPid`, call `psutil.Process(pid).suspend()`. Record `responseTaken = suspended`, or `suspend_failed` on exception.
- FR-RSP-3: **Never** act on: the agent's own PID, PID 0/1/4, the parent of the agent, or any process name in `processAllowlist` (defaults: `explorer.exe`, `systemd`, `python`, `node`, `mongod`, `code`, `chrome`, `firefox`).
- FR-RSP-4: Suspect detection: on a CRITICAL alert, iterate `psutil.process_iter()` and for each process try `proc.open_files()`; pick the first process holding a handle to any of the `affectedFiles`. Wrap in try/except for `AccessDenied`/`NoSuchProcess`. If none is found, `suspectPid = null`. This is best-effort and must be documented as such.
- FR-RSP-5: The dashboard offers a "Resume process" action only as a manual note in the alert detail (instruction text); the agent does not implement resume in v1.

### 5.6 Agent: Transport (FR-TRN)
- FR-TRN-1: Buffer events; flush every 2 s or at 200 events.
- FR-TRN-2: POST to `{backend_url}/api/events/batch` with header `x-agent-key`.
- FR-TRN-3: On failure, retry with exponential backoff (1, 2, 4, 8, max 30 s); keep at most 5,000 buffered events, dropping oldest first.
- FR-TRN-4: Alerts are POSTed immediately to `/api/alerts`.

### 5.7 Vault (FR-VLT) (implemented in the backend)
- FR-VLT-1: Encrypt with Node built-in `crypto`, algorithm `aes-256-gcm`.
- FR-VLT-2: Key derivation: `crypto.scrypt` with a random **16-byte salt per file**, key length 32, parameters `N=32768, r=8, p=1`.
- FR-VLT-3: A random **12-byte IV (nonce) per file** from `crypto.randomBytes`. Never reuse an IV.
- FR-VLT-4: Stored file layout (binary): `MEDR1` (5 ASCII bytes) | salt (16) | iv (12) | auth tag (16) | ciphertext.
- FR-VLT-5: Upload: `POST /api/vault/upload` (multipart, field `file`, field `password`). Max file size 50 MB. Compute `sha256Plaintext`, encrypt, save to `backend/vault_store/<uuid>.vault`, save metadata.
- FR-VLT-6: Download/decrypt: `POST /api/vault/:itemId/decrypt` with `{password}` returns the plaintext file. Wrong password or tampered file -> auth-tag failure -> HTTP 403 with a generic message "Decryption failed". After decryption, verify the SHA-256 matches; if not, return 500 "Integrity check failed".
- FR-VLT-7: Delete: removes the `.vault` file and the metadata.
- FR-VLT-8: The server never logs passwords, keys, or plaintext. Passwords are only in memory during the request.
- FR-VLT-9: Vault directory `vault_store/` is **excluded** from the agent's watch paths by default (document this).

### 5.8 Backend API (FR-API)
All JSON. Admin routes need header `Authorization: Bearer <JWT>`; agent routes need `x-agent-key` matching `AGENT_API_KEY` in `.env`. Validate every body with `zod`; return HTTP 400 with field errors on invalid input.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/login` | none (rate-limited 10/min) | `{username,password}` -> `{token}` (JWT, 8 h expiry) |
| POST | `/api/events/batch` | agent | body `{events:[Event...]}` max 200; stores; emits socket `event:new` (only a summary count + last 20 events, to avoid flooding) |
| GET | `/api/events` | admin | query `limit` (default 100, max 500), `action`, `isCanary`, `from`, `to` |
| POST | `/api/alerts` | agent | stores Alert; emits socket `alert:new` |
| GET | `/api/alerts` | admin | query `status`, `severity`, `limit` |
| PATCH | `/api/alerts/:alertId` | admin | `{status}` |
| GET | `/api/stats/summary` | admin | `{eventsLast24h, alertsOpen, alertsCritical24h, filesAffected24h}` |
| GET | `/api/stats/timeline` | admin | events and alerts per minute for the last 60 minutes |
| GET | `/api/settings` | admin or agent | returns Settings |
| PUT | `/api/settings` | admin | validates thresholds (0-100, warning < critical) and mode |
| POST | `/api/vault/upload` | admin | see FR-VLT-5 |
| GET | `/api/vault` | admin | list metadata |
| POST | `/api/vault/:itemId/decrypt` | admin | see FR-VLT-6 |
| DELETE | `/api/vault/:itemId` | admin | see FR-VLT-7 |
| GET | `/api/health` | none | `{status:"ok"}` |

Socket.IO: clients must send the JWT in `auth.token` on connection; reject otherwise. Events: `alert:new`, `event:new`, `settings:updated`.

Use `helmet`, `cors` (origin from `.env`), and `express-rate-limit`. Index MongoDB on `events.ts`, `alerts.ts`, `alerts.status`. Add a TTL index to delete events older than 7 days.

### 5.9 Dashboard (FR-UI)
Pages (React Router): `/login`, `/` (Overview), `/alerts`, `/events`, `/vault`, `/settings`.
- Overview: 4 summary cards (from `/api/stats/summary`), a line chart (recharts) of events/alerts per minute, a live alert feed (via socket), and a status badge: green "Normal" / amber "Warning" / red "Critical" based on the newest open alert within the last 5 minutes.
- Alerts: table with severity, time, score, reasons, suspect process, response taken, status; click opens a detail panel (affected files, ML probability) with buttons to set status.
- Events: filterable table (action, canary only, time range), 100 rows, "load more".
- Vault: upload form (file + password), list of items, decrypt (prompt for password, then browser download), delete with confirm.
- Settings: response mode toggle (with warning text: "Suspend mode may freeze a legitimate program if misidentified"), threshold sliders, process allowlist editor.
- Store the JWT in memory plus `sessionStorage`; on 401 redirect to `/login`.

---

## 6. Non-functional requirements
- NFR-1 Detection latency: from the first malicious-looking event to alert, at most 6 seconds in tests.
- NFR-2 Agent overhead: under 10% average CPU on a mid-range laptop while monitoring a folder with 1,000 files and idle.
- NFR-3 Security: no secrets in source; `.env` git-ignored; bcrypt cost 10+; JWT secret at least 32 random characters; all admin routes protected; input validated.
- NFR-4 Reliability: agent keeps running if the backend is down (buffering per FR-TRN-3).
- NFR-5 Portability: runs on Windows and Linux.
- NFR-6 Maintainability: type-hinted Python, ESLint-clean JS, README with setup steps.
- NFR-7 False positives: on the benign scenarios of Section 9, at most 2 false alerts per hour of simulated benign activity at the default thresholds.

---

## 7. Configuration files

### 7.1 `agent/config.yaml` (defaults)
```yaml
agent_id: "agent-001"
backend_url: "http://localhost:5000"
agent_api_key: "CHANGE_ME"        # must equal AGENT_API_KEY in backend .env
watch_paths:
  - "./testbed"
ignore_patterns: ["*.tmp", "~$*", ".git/*", "__pycache__/*"]
entropy_sample_bytes: 65536
entropy_min_file_bytes: 512
entropy_spike_min: 7.5
entropy_spike_delta: 2.0
high_entropy_ok_ext: [".zip", ".gz", ".7z", ".rar", ".jpg", ".jpeg", ".png", ".mp3", ".mp4", ".mkv", ".pdf", ".docx", ".xlsx", ".pptx", ".webp"]
known_ext: [".txt", ".csv", ".json", ".md", ".log", ".pdf", ".docx", ".xlsx", ".pptx", ".jpg", ".png", ".zip", ".py", ".js", ".html"]
suspicious_ext: [".locked", ".enc", ".encrypted", ".crypt", ".crypted", ".lock", ".xxx"]
canary_names: ["_important_passwords.txt", "_financial_records.csv", "_backup_keys.docx.txt"]
window_seconds: 10
score_interval_seconds: 2
scoring:
  canary_hit: 100
  mass_modify: {min_count: 20, points: 30}
  entropy_spike: {min_count: 5, points: 40}
  ext_change: {min_count: 5, points: 20}
  mass_delete: {min_count: 10, points: 10}
  wide_spread: {min_dirs: 5, min_files: 20, points: 10}
  ml: {min_probability: 0.8, points: 30}
ml_model_path: "./models/rf_model.joblib"
```

### 7.2 `backend/.env.example`
```
PORT=5000
MONGO_URI=mongodb://localhost:27017/mini_edr
JWT_SECRET=replace_with_32+_random_chars
AGENT_API_KEY=CHANGE_ME
CLIENT_ORIGIN=http://localhost:5173
ADMIN_USER=admin
ADMIN_PASS=change_me_now
```

---

## 8. Cross-cutting rules for tests
- Every phase has a script or test command listed under its acceptance tests.
- A phase is "done" only when all listed tests pass and the output is shown to the developer.

---

## 9. Test dataset and test harness (FR-DAT)

**Why synthetic:** Real ransomware samples are dangerous and unnecessary. This project tests detection logic using (a) generated benign files, (b) generated event streams that statistically imitate benign and ransomware-like behavior, and (c) a harmless emulator that only copies and renames files inside a sandbox. **No encryption, no malware, no ransom notes, no network access are used anywhere in Section 9.**

### 9.1 Sandbox rules (apply to all dataset scripts)
- All scripts operate **only** inside `./testbed/` (resolve with `Path.resolve()` and refuse to run if the target is not inside the repo's `testbed` directory; exit with an error message).
- Scripts must accept `--seed` (default 42) so results are reproducible.
- `testbed/` and `dataset/out/` are git-ignored.

### 9.2 `dataset/make_fixtures.py`: creates a realistic folder
Creates under `testbed/` (default counts, configurable by flags):
- 150 text-like files (`.txt`, `.md`, `.csv`, `.json`, `.log`) of 1-50 KB filled with random English-like words (use a built-in word list; no downloads). Entropy should land around 3.5-5.0.
- 20 legitimate high-entropy files: 10 `.zip` (made with Python's `zipfile` from the text files) and 10 `.jpg`/`.png`-named binary files containing `random.Random(seed).randbytes(...)`. Label these "benign_high_entropy". They exist to test false positives.
- A folder tree 3 levels deep, 6 subfolders (`docs/`, `photos/`, `projects/`, `finance/`, `archive/`, `misc/`).
- A directory `dataset/out/noise_pool/` containing 40 files of 4-32 KB of `randbytes` data (pre-generated "high-entropy payload files"). These are used by the emulator in 9.4.
- Writes `testbed/MANIFEST.json`: list of every file with its path and SHA-256, so tests can verify nothing outside the plan changed.

### 9.3 `dataset/generate_events.py`: synthetic labeled event streams
Generates JSON Lines files in `dataset/out/` where each line is an Event (Section 4.1). **No real files are touched.** It simulates time with a counter, not real sleeping. Each scenario outputs `<scenario>.jsonl` and an entry in `dataset/out/labels.csv` with columns `scenario,start_ts,end_ts,label` (`0` = benign, `1` = ransomware-like).

Common rules: paths are drawn from the fixture manifest; each stream is 300 simulated seconds; Gaussian jitter on inter-event gaps; entropy for plain files drawn from N(4.2, 0.6) clipped to [1, 6.5]; entropy for high-entropy files from N(7.8, 0.1) clipped to [7.3, 7.99].

**Benign scenarios (label 0):**
| ID | Name | Behavior |
|---|---|---|
| B1 | office_editing | 1 `modified` event per 3-10 s on text files; entropy plain; no deletes |
| B2 | software_build | bursts of 30-80 `created`/`modified` events within 5 s every 60 s on `.py/.js/.log`; entropy plain |
| B3 | archive_extract | 40-120 `created` events within 10 s of mixed extensions; some `.zip` with high entropy (no prior entropy) |
| B4 | photo_import | 30-100 `created` `.jpg` events with entropy about 7.8 over 20 s |
| B5 | backup_tool | 100-300 `modified` events of `.zip`/`.7z` with high entropy, prevEntropy also high (so delta about 0) |
| B6 | idle | 0-1 events per 30 s |
| B7 | cleanup | 15-40 `deleted` events within 10 s, no modifies |

**Ransomware-like scenarios (label 1), simulated as event streams only:**
| ID | Name | Behavior |
|---|---|---|
| M1 | fast_mass_modify | starting at t=60, 15-40 files/s `modified`, each with prevEntropy about 4.2 and entropy about 7.9, across 5+ directories |
| M2 | slow_and_low | 1 file per 2 s, same entropy jump; runs 240 s |
| M3 | rename_only | `moved` events 10-30 files/s to extensions in `suspicious_ext` plus 3-4 random unusual ones (`.q9x7`, `.zz1`), no content change |
| M4 | write_then_delete | per file: `created` new high-entropy file, then `deleted` original within 1 s |
| M5 | canary_first | single `modified` on a canary, followed 5 s later by M1-style behavior |
| M6 | mixed_with_benign | M1 behavior overlaid with B1 and B2 background activity |

Counts: generate **30 runs per scenario** with different seeds (7 benign x 30 + 6 ransomware-like x 30 = 390 streams).

### 9.4 `dataset/attack_emulator.py`: harmless live emulation (sandbox-only)
Purpose: end-to-end test of the real watcher. It performs ONLY: (1) copy a file from `dataset/out/noise_pool/` over a fixture file in `testbed/`, (2) rename the file to a new extension. It does not read, transform, or encrypt the user's data; fixture files are disposable and recreated by `make_fixtures.py`.
- Refuses to run outside `testbed/` (see 9.1) and requires the flag `--i-understand-this-is-a-sandbox`.
- Modes: `--mode fast` (20 files/s), `--mode slow` (1 file per 2 s), `--mode rename`, `--mode canary` (modifies one canary by appending a line), `--mode benign` (appends one line to random text files at 1 per 3 s).
- Prints a summary: files touched, start/end time (used to measure detection latency).
- Must not contain any network code, any crypto library import, any ransom-note text, or any directory walk outside `testbed/`.

### 9.5 ML feature vector and training (`features.py`, `dataset/train_model.py`)
Feature vector per window (same code at runtime and training), in this exact order:
`n_modified, n_created, n_deleted, n_moved, n_unique_files, n_entropy_spike, n_ext_change, mean_entropy, max_entropy, n_dirs, files_per_sec, canary_hit`

Training procedure:
1. Read all `.jsonl` streams; slide a 10-second window with a 2-second step; compute features.
2. Label a window `1` if it overlaps a ransomware-like interval in `labels.csv` by at least 3 seconds, else `0`.
3. Split **by scenario run** (not by window): 70% train / 30% test, with a fixed seed, so windows from the same run never appear in both sets.
4. Train `RandomForestClassifier(n_estimators=200, max_depth=12, class_weight="balanced", random_state=42)`.
5. Report: accuracy, precision, recall, F1, confusion matrix, and feature importances, saved to `dataset/out/ml_report.md`.
6. Save the model with `joblib.dump` to `agent/models/rf_model.joblib`.
7. Target (not guaranteed): recall >= 0.95 and precision >= 0.90 on the test split. If not met, report honestly; do not tune on the test set.

**Honesty rule:** The report must state that the model is trained on synthetic data and its real-world performance is unknown. Do not claim real-world accuracy.

### 9.6 Optional external datasets (NOT required)
A student may later look for public ransomware-behavior or malware-feature datasets (for example on Kaggle) for a separate static-analysis experiment. Astra must not download or execute any malware binaries, and must ask the developer before adding any external dataset.

---

## 10. Phased build plan

Each phase lists: Goal, Tasks, Deliverables, Acceptance tests, Do NOT.

### Phase 0: Project setup
- **Goal:** Empty but runnable skeleton.
- **Tasks:** Create the repository layout (3.4). Create `.gitignore` (node_modules, `.env`, `testbed/`, `dataset/out/`, `agent/state/`, `agent/models/`, `backend/vault_store/`, `__pycache__/`). Create Python venv and `requirements.txt`; `npm init` for backend and dashboard. Add `README.md` with setup steps. Create `docs/open_questions.md`.
- **Deliverables:** Folder tree; install commands that succeed.
- **Acceptance tests:** `pytest` runs (0 tests OK); `npm test` runs in backend and dashboard; `npm run dev` for dashboard shows a blank page.
- **Do NOT:** write feature code.

### Phase 1: Backend core
- **Goal:** API + database + auth working with no agent yet.
- **Tasks:** Express server, config loader (`dotenv`), mongoose models (4.1-4.5), middleware `agentAuth`, `adminAuth`, `validate` (zod), routes for auth, events, alerts, stats, settings, health (5.8); seed-admin script; Socket.IO with JWT handshake; helmet/cors/rate limiting; indexes and TTL.
- **Deliverables:** Running backend; Postman/curl examples in `docs/api_examples.md`.
- **Acceptance tests (Jest + supertest):** login success/failure; admin route without token returns 401; agent route with wrong key returns 401; batch of 200 valid events returns 201; batch of 201 returns 400; invalid event field returns 400; `PUT /api/settings` with warning >= critical returns 400; socket connection without token is rejected.
- **Do NOT:** build the vault or dashboard yet.

### Phase 2: Agent watcher and transport
- **Goal:** Real file events flow into the backend.
- **Tasks:** `config.yaml` loader with validation; `watcher.py` (5.1); `transport.py` (5.6); `main.py` entry. Events have `entropy`, `prevEntropy` set to null for now.
- **Deliverables:** Agent running against a temporary folder.
- **Acceptance tests:** create/modify/delete/rename a file by hand -> corresponding events appear via `GET /api/events` within 3 s; debounce works (5 rapid writes -> 1 event); stop the backend, make 10 changes, restart the backend -> all 10 events arrive; deleting a file during processing does not crash the agent; ignored patterns produce no events.
- **Do NOT:** compute entropy or scores.

### Phase 3: Fixtures and synthetic dataset
- **Goal:** Reproducible test data.
- **Tasks:** Implement `make_fixtures.py` (9.2), `generate_events.py` (9.3), `attack_emulator.py` (9.4) following 9.1 rules; write `dataset/README.md` with exact commands.
- **Deliverables:** Generated `testbed/`, `dataset/out/*.jsonl`, `labels.csv`.
- **Acceptance tests:** running with the same seed twice yields byte-identical `labels.csv` and streams; 390 stream files exist; `MANIFEST.json` lists every fixture file; emulator refuses to run on a path outside `testbed/` and without the sandbox flag; a grep of `attack_emulator.py` finds no network, crypto, or ransom-note code.
- **Do NOT:** use real malware, any encryption, or files outside `testbed/`.

### Phase 4: Entropy and extension analysis
- **Goal:** Enrich events with entropy and flags.
- **Tasks:** `analyzer.py` per 5.2; entropy cache; unit tests.
- **Acceptance tests:** entropy of an all-zero file is 0.0; of `randbytes` data 4096+ bytes is greater than 7.9; of English text between 3.0 and 5.5; file under 512 bytes yields null; overwriting a text fixture with a `noise_pool` file yields an entropy spike; overwriting a `.zip` with high-entropy content does NOT count as a spike; a rename to `.locked` is flagged; a rename `.txt` to `.md` is not flagged.
- **Do NOT:** alert yet.

### Phase 5: Canary files
- **Goal:** Tripwire works.
- **Tasks:** `canary.py` per 5.3; state file; integrate with watcher; send CRITICAL alert via `POST /api/alerts`.
- **Acceptance tests:** startup creates 3 canaries; `attack_emulator --mode canary` produces a CRITICAL alert in under 3 s; deleting a canary triggers an alert and it is re-created after 5 s; reading a canary produces no alert (documented limitation); restarting the agent does not recreate or duplicate existing canaries.

### Phase 6: Window scoring and response
- **Goal:** Rule-based detection and optional suspend.
- **Tasks:** `window.py`, `features.py` (counters from 5.4), `scoring.py` (rule score, thresholds, dedup), `responder.py` (5.5). Leave the ML hook returning null.
- **Acceptance tests (replay `generate_events.py` streams through the scoring engine in a unit test, no real files):** M1, M3, M5 produce CRITICAL; M2 produces at least a WARNING within the run; B1, B2, B3, B4, B5, B6 produce no alert in at least 27 of 30 runs each (record the actual number; if lower, report and do not silently change thresholds); dedup test (2 alerts in 30 s -> 1 sent); responder never acts on allowlisted or protected PIDs (mock `psutil`); live run with `attack_emulator --mode fast` produces a CRITICAL alert within 6 s of start.
- **Do NOT:** enable `suspend` by default.

### Phase 7: Dashboard
- **Goal:** Live UI for alerts, events, settings (no vault yet).
- **Tasks:** Implement login, Overview, Alerts, Events, Settings pages (5.9) with socket updates.
- **Acceptance tests:** login failure shows an error; with the agent running, `attack_emulator --mode fast` makes a red alert appear on Overview without page refresh; changing the response mode in Settings is saved and reflected after refresh; event filters work; unauthorized access redirects to `/login`.

### Phase 8: Vault
- **Goal:** Encrypted storage.
- **Tasks:** `vaultService.js` and routes (5.7); Vault page in dashboard.
- **Acceptance tests (Jest):** upload then decrypt returns byte-identical file; wrong password returns 403; flipping one byte in the `.vault` file makes decryption return 403; two uploads of the same file with the same password produce different ciphertext (random salt/IV); file larger than 50 MB is rejected; `.vault` header begins with `MEDR1`; no password or plaintext appears in server logs.
- **Do NOT:** store passwords or keys anywhere; use ECB/CBC modes; reuse IVs.

### Phase 9: ML layer
- **Goal:** Add the Random Forest signal.
- **Tasks:** `train_model.py` (9.5), `ml_model.py` loader/predictor, integrate with scoring (FR-SCR-3), generate `ml_report.md`.
- **Acceptance tests:** model file created; report contains metrics, confusion matrix, feature importances, and the honesty statement; split is by run (assert in code that no run id appears in both sets); with the model removed, the agent still runs; replay tests from Phase 6 are re-run and results compared with and without ML in a short table.

### Phase 10: Integration, evaluation, documentation
- **Goal:** Final verified system.
- **Tasks:** End-to-end script `dataset/run_e2e.md` (manual steps) covering: start MongoDB, backend, dashboard, agent; run each emulator mode; measure detection latency (time from emulator start to alert timestamp) over 10 runs per mode; run benign mode for 10 minutes and count false alerts. Write `docs/evaluation.md` with a results table. Write `README.md` (setup, architecture summary, screenshots placeholders, limitations section).
- **Acceptance tests:** NFR-1, NFR-2, NFR-7 measured and reported honestly, even if missed; all earlier tests still pass.

---

## 11. Known limitations (must appear in README)
1. User-space monitoring can miss very fast encryption that finishes before the first scoring cycle; detection is heuristic, not guaranteed.
2. Process attribution is best-effort.
3. Reads of canary files are not detectable.
4. ML model is trained on synthetic data; real-world accuracy is unknown.
5. Legitimate tools (backup, archivers) may cause false positives; thresholds and allowlists are tunable.
6. This is an educational prototype, not a replacement for a commercial EDR or antivirus.

## 12. Traceability summary
| Module | Requirement IDs | Phase |
|---|---|---|
| Backend | FR-API | 1 |
| Watcher, transport | FR-AGT, FR-TRN | 2 |
| Dataset | FR-DAT (Section 9) | 3, 9 |
| Entropy | FR-ENT | 4 |
| Canary | FR-CAN | 5 |
| Scoring, response | FR-SCR, FR-RSP | 6, 9 |
| Dashboard | FR-UI | 7, 8 |
| Vault | FR-VLT | 8 |
