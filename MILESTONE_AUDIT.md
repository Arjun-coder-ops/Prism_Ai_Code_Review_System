# Milestone audit (current checkpoint)

This checkpoint covers the foundation, durable review slice, and the first authorization/recovery hardening increment.

| Milestone | Evidence | State |
|---|---|---|
| M0 | FastAPI factory, typed settings/errors, SQLAlchemy models, Alembic `0007_test_paths`, Docker PostgreSQL/Redis/Beat, CI, 32 unit tests plus 5 integration tests, Ruff and mypy | Implemented for current slice |
| M1 | Canonical URL validation, GitHub metadata/files adapters, unified diff parser, SHA persistence, findings API | Implemented for current slice; authenticated GitHub integration not live-tested |
| M2 | Row-lock claim, attempt/lease fields, Celery retries, stale-lease recovery, bounded outbox retries, idempotent terminal states, enqueue failure handling | Implemented and Docker-integration tested; crash-kill and long-running worker tests remain |
| M3 | App JWT helper, installation-token and repository-list adapters, installation add/remove/suspend synchronization, repository-scoped authorization, HMAC webhook verification, idempotent delivery/outbox models, PR event intake | Implemented with unit/static coverage and a FastAPI/PostgreSQL integration test passed in GitHub Actions; live GitHub App credentials remain pending |
| M4–M7 | Hybrid providers, repository intelligence, test-gap engine, evaluations | Groq-first/Gemini-fallback adapters are integrated into worker analysis with configurable usage cost accounting; bounded Semgrep/Ruff/ESLint adapters and high-risk independent evidence checks are implemented; M6 persists a commit-pinned repository tree; Tree-sitter symbol intelligence, live keys, full analyzer wiring, and broader datasets pending |
| M8–M10 | Full security hardening, complete workspace UI, deployment audit | API-key/rate-limit/metrics, endpoint authorization, Beat scheduling, and workspace slice added; browser/deployment audit not complete |

No milestone is marked complete merely from documentation. External credentials and live publication remain intentionally unverified.

## Weighted completion audit

This is a scope-tracking estimate based on implementation plus verification evidence, not a product-quality claim.

| Milestone | Weight | Verified completion | Weighted contribution |
|---|---:|---:|---:|
| M0 Foundation | 10% | 90% | 9.00% |
| M1 Public PR Analysis | 8% | 75% | 6.00% |
| M2 Durable Processing | 12% | 78% | 9.36% |
| M3 GitHub App | 12% | 82% | 9.84% |
| M4 Hybrid AI Review | 20% | 58% | 11.60% |
| M5 Repository Intelligence | 8% | 25% | 2.00% |
| M6 Test-Gap Analysis | 6% | 45% | 2.70% |
| M7 Evaluation | 8% | 30% | 2.40% |
| M8 Security and Observability | 7% | 58% | 4.06% |
| M9 Frontend | 6% | 35% | 2.10% |
| M10 Deployment | 3% | 45% | 1.35% |
| **Overall** | **100%** |  | **60.41%** |

Previous verified audit at `bfb760a` was 57.8%; this increment adds about 2.6 percentage points through installation lifecycle synchronization, bounded analyzer adapters, independent high-risk evidence checks, cost accounting, and the passing CI integration path. Live GitHub App credentials, live AI providers, full analyzer execution, Tree-sitter symbol analysis, browser E2E, and production deployment remain unverified.
