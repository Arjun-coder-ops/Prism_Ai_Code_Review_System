# Milestone audit (current checkpoint)

This checkpoint covers the foundation, durable review slice, and the first authorization/recovery hardening increment.

| Milestone | Evidence | State |
|---|---|---|
| M0 | FastAPI factory, typed settings/errors, SQLAlchemy models, Alembic `0006_ai_usage`, Docker PostgreSQL/Redis/Beat, CI, 32 unit tests plus 5 integration tests, Ruff and mypy | Implemented for current slice |
| M1 | Canonical URL validation, GitHub metadata/files adapters, unified diff parser, SHA persistence, findings API | Implemented for current slice; authenticated GitHub integration not live-tested |
| M2 | Row-lock claim, attempt/lease fields, Celery retries, stale-lease recovery, bounded outbox retries, idempotent terminal states, enqueue failure handling | Implemented and Docker-integration tested; crash-kill and long-running worker tests remain |
| M3 | App JWT helper, installation-token adapter, installation-scoped repository authorization, repository allowlist, HMAC webhook verification, idempotent delivery/outbox models, PR event intake | Implemented and locally tested; live GitHub App credentials and publication pending |
| M4–M7 | Hybrid providers, repository intelligence, test-gap engine, evaluations | Groq-first/Gemini-fallback adapters are integrated into worker analysis with private-source gating, usage capture, and evidence verification; M5/M6 deterministic APIs and M7 fixture remain; live keys and broader datasets pending |
| M8–M10 | Full security hardening, complete workspace UI, deployment audit | API-key/rate-limit/metrics, endpoint authorization, Beat scheduling, and workspace slice added; browser/deployment audit not complete |

No milestone is marked complete merely from documentation. External credentials and live publication remain intentionally unverified.
