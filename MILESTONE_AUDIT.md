# Milestone audit (current checkpoint)

This checkpoint covers the foundation and the first durable review slice only.

| Milestone | Evidence | State |
|---|---|---|
| M0 | FastAPI factory, typed settings/errors, SQLAlchemy models, Alembic `0003_github_events`, Docker PostgreSQL/Redis, CI, 23 tests, Ruff and mypy | Implemented for current slice |
| M1 | Canonical URL validation, GitHub metadata/files adapters, unified diff parser, SHA persistence, findings API | Implemented for current slice; authenticated GitHub integration not live-tested |
| M2 | Row-lock claim, attempt/lease fields, Celery retries, idempotent terminal states, enqueue failure handling, deterministic findings | Implemented for current slice; crash-recovery integration tests still needed |
| M3 | App JWT helper, installation-token adapter, HMAC webhook verification, idempotent delivery/outbox models, PR event intake | Implemented and locally tested; live GitHub App pending |
| M4–M7 | Hybrid providers, repository intelligence, test-gap engine, evaluations | Provider adapters and deterministic primitives implemented; live credentials and datasets pending |
| M8–M10 | Full security hardening, complete workspace UI, deployment audit | Workspace slice and metrics added; browser/deployment audit not complete |

No milestone is marked complete merely from documentation. External credentials and live publication remain intentionally unverified.
