# PRISM milestone plan

| Milestone | Thin vertical slice / acceptance criteria | Status |
|---|---|---|
| M0 Foundation | FastAPI factory, health/readiness, typed config/errors, PostgreSQL models/migration, Celery config, Vite client, Compose and CI | Current slice verified |
| M1 Public PR analysis | Validated canonical GitHub URL, commit-pinned retrieval, unified-diff parser, persisted review state and findings UI | Current slice verified; live credentials pending |
| M2 Durable processing | Atomic claims, leases, retries, cancellation and outage recovery tests | Claims, stale-lease recovery, bounded outbox retry and idempotency implemented; live crash integration pending |
| M3 GitHub App | JWT, installation tokens, webhook signature/idempotency, publication | Installation-scoped webhook authorization implemented; live App and publication pending |
| M4 AI verification | Provider adapters, structured candidates, independent evidence verification/abstention | Groq-first/Gemini-fallback pipeline integrated with bounded retries, private-source gating, usage capture, and evidence verification; live credentials pending |
| M5 Intelligence | Tree-sitter context and change impact | Persisted changed paths and impact API implemented; Tree-sitter pending |
| M6 Test gaps | Test discovery and actionable gap recommendations | Test-gap API implemented; repository test discovery pending |
| M7 Evaluations | Versioned datasets, graders and reports | Versioned `review-v1` fixture and executable regression test implemented; broader labeled datasets pending |
| M8 Security/observability | Auth, rate limits, metrics/traces, retention and recovery tests | API-key gate, intake rate limit, metrics and security regression tests implemented; distributed auth/tracing/retention pending |
| M9 Frontend | Accessible repository/review workspace and responsive browser coverage | In progress |
| M10 Deployment | Hardened images, CI gates, migration and recovery runbooks | In progress |
