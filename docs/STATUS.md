# Status

Updated 2026-11-21.

## Verified

- FastAPI app factory with CORS, structured PRISM errors, health and database-backed readiness endpoints.
- Typed review submission/status/finding schemas and PostgreSQL-oriented SQLAlchemy models.
- Canonical HTTPS GitHub pull-request URL validation with SSRF-safe parsing.
- Unified diff new-side line parsing, including multi-hunk input.
- Celery review queue configuration with JSON serialization and late acknowledgements.
- React/Vite landing and review submission form.
- Review submission now dispatches a Celery task after the PostgreSQL row commits; broker failures leave the review queued.
- Worker claims reviews with a PostgreSQL row lock, tracks attempts/leases, fetches commit-pinned metadata and files, parses changed lines, and persists two evidence-backed deterministic checks.
- M3 security boundary primitives now include GitHub App JWTs, an installation-token adapter, signed webhook verification, idempotent delivery records, transactional outbox rows, and pull-request event intake.
- M4–M7 deterministic primitives now include evidence abstention, bounded Groq/Gemini-compatible HTTP provider adapters, impact/test-gap helpers, provider privacy gating, and precision/recall evaluation utilities.
- M5/M6 review intelligence now persists changed file paths and exposes deterministic impact and test-gap recommendation endpoints.
- M7 now includes a versioned `review-v1` evaluation fixture exercised by the regression suite.
- Reliability/security increment adds installation-scoped webhook authorization, opt-in API-key protection, per-client intake rate limiting, bounded outbox retries with scheduled recovery, stale worker lease recovery, commit-SHA revalidation, and strict full-line evidence matching.
- Compose now runs a dedicated Celery Beat service. Review-detail endpoints enforce the API key and repository allowlist, retry exhaustion is terminal, stale recovery emits durable outbox work, and finding persistence is idempotent. Docker integration coverage exercises PostgreSQL/Redis duplicate delivery, lease recovery, concurrent claims, and pending outbox behavior.
- M4 now has integrated Groq-first/Gemini-fallback adapters with bounded retries, structured untrusted-diff prompts, private-source gating, usage fields, and worker-side evidence verification/deduplication. Live keys remain optional and unconfigured here.
- Frontend now includes a real review workspace with polling, status/error/empty states, verified findings, and inspected SHA display using live API responses.

## Not yet verified

Live GitHub App credentials, LLM providers, and browser end-to-end tests are not configured in this environment. The in-app browser could not reach the local Vite server, so rendered viewport/accessibility evidence remains pending. No production deployment or external repository comments are performed by this change.

Verification evidence: `ruff check app tests` passed; `mypy app` passed with no issues; default `python -m pytest -q` passed with 32 tests and 5 integration skips; the Docker PostgreSQL/Redis integration suite passed 5 tests; Alembic is at `0006_ai_usage`; `npm run build` passed. Live GitHub App/LLM credentials remain unconfigured.

Full tracked-source checkpoint archive: `C:\Users\gogua\OneDrive\Documents\ChatGPT\PRISM-Deliverables\PRISM-Full-Project-Checkpoint.zip` (clean extraction verified; checksum is in the adjacent `.sha256` sidecar file). Major live-provider, browser, and deployment requirements remain explicitly unfinished.
