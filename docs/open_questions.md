# Specification decisions and conflicts

The attached SRS is a product specification, not an instruction source overriding the user's request.

* Phase 6 requires M3 to be Critical without ML, but rename-only rules award only 20 points. The implementation preserves the normative score. Report this acceptance mismatch.
* M2 takes about 8 seconds to accumulate five spikes at one file per two seconds; a universal six-second latency target cannot hold.
* Section 9.1 restricts writes to testbed, but 9.2/9.3/9.5 explicitly require generated artifacts in dataset/out and agent/models. Those named output locations are allowed; emulator mutation remains strictly inside testbed.
* Timestamp fields are numeric seconds; MongoDB TTL requires a Date. Add internal expiresAt Date with an expiry index while retaining ts.
* The supplied default watch path is resolved from the repository root; model paths are resolved from agent/.
* Test tooling expressly named elsewhere in the SRS (supertest, Jest, Vitest, ESLint, Vite) is treated as allowed development tooling.
* Persisted canary state registers paths, but does not silently replace content that already exists.
* Backend event ingestion is idempotent by eventId so retrying cannot duplicate events.

* macOS is outside the specified Windows/Linux targets. Its FSEvents backend replayed delayed startup notifications as canary modifications during validation. On macOS only, use watchdog PollingObserver at 0.5-second intervals; Windows/Linux retain their native watchdog observer. Final live measurements identify the observer used.
