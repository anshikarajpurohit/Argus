# API examples

Use `http://127.0.0.1:5000`. Examples use shell variables so secrets are not stored in source. Set `AGENT_API_KEY`, `ADMIN_USER`, and `ADMIN_PASS` locally. Obtain a token with a JSON body containing `username` and `password` at `POST /api/auth/login`, then set `TOKEN` to the returned token. Login is limited to 10 attempts per minute and tokens expire after eight hours.

```sh
curl http://127.0.0.1:5000/api/health
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:5000/api/stats/summary
curl -H "Authorization: Bearer $TOKEN" 'http://127.0.0.1:5000/api/events?limit=100&action=moved'
curl -H "Authorization: Bearer $TOKEN" 'http://127.0.0.1:5000/api/alerts?status=open&severity=CRITICAL'
curl -H "x-agent-key: $AGENT_API_KEY" http://127.0.0.1:5000/api/settings
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"status":"acknowledged"}' http://127.0.0.1:5000/api/alerts/ALERT_UUID
curl -X PUT -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"responseMode":"alert_only","warningThreshold":40,"criticalThreshold":70,"processAllowlist":["explorer.exe","systemd","python","node","mongod","code","chrome","firefox"]}' \
  http://127.0.0.1:5000/api/settings
```

Event ingestion is `POST /api/events/batch`, agent-authenticated, with `{ "events": [Event] }`. It accepts 1–200 complete events. Duplicate event UUIDs are idempotent. Responses contain the count of newly inserted records. `GET /api/events` supports `limit` (1–500), `action`, `isCanary=true|false`, `from`, and `to` as numeric Unix seconds.

Alerts are ingested at `POST /api/alerts` with the complete SRS alert schema and the same agent header. Duplicate alert UUIDs do not emit duplicate socket notifications. Status patches accept only `open`, `acknowledged`, or `resolved`.

`GET /api/stats/timeline` returns 60 minute buckets `{ts,events,alerts}`, including zero buckets. `filesAffected24h` counts distinct paths referenced by alerts from the last 24 hours.

All `/api/vault` operations require an administrator JWT. Upload uses multipart fields `file` and `password`. `GET /api/vault` lists metadata. `POST /api/vault/:itemId/decrypt` accepts JSON `{password}` and returns an attachment. `DELETE /api/vault/:itemId` deletes the stored ciphertext and metadata. Use the dashboard to avoid typing vault passwords into shell history.

Invalid bodies and query fields return 400; missing/invalid authentication returns 401; failed decryption returns 403; missing resources return 404; uploads larger than 50 MB return 413. Error responses never echo passwords or plaintext.

Socket.IO uses the same origin as the backend. Connect with `auth: {token}`; unauthenticated handshakes are rejected and established connections are disconnected at JWT expiry. Events are `alert:new`, `event:new` (count and last 20 events), and `settings:updated`.
