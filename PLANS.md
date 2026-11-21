# PRISM milestone plan

| Milestone | Thin vertical slice / acceptance criteria | Status |
|---|---|---|
| M0 Foundation | FastAPI factory, health/readiness, typed config/errors, PostgreSQL models/migration, Celery config, Vite client, Compose and CI | Current slice verified |
| M1 Public PR analysis | Validated canonical GitHub URL, commit-pinned retrieval, unified-diff parser, persisted review state and findings UI | Current slice verified; live credentials pending |
| M2 Durable processing | Atomic claims, leases, retries, cancellation and outage recovery tests | Current slice implemented; crash-recovery integration pending |
| M3 GitHub App | JWT, installation tokens, webhook signature/idempotency, publication | Current slice implemented; live App pending |
| M4 AI verification | Provider adapters, structured candidates, independent evidence verification/abstention | Current slice implemented; live providers pending |
| M5 Intelligence | Tree-sitter context and change impact | Change-impact helper implemented; Tree-sitter pending |
| M6 Test gaps | Test discovery and actionable gap recommendations | Recommendation helper implemented; discovery pending |
| M7 Evaluations | Versioned datasets, graders and reports | Scoring helper implemented; datasets pending |
| M8 Security/observability | Auth, rate limits, metrics/traces, retention and recovery tests | Planned |
| M9 Frontend | Accessible repository/review workspace and responsive browser coverage | In progress |
| M10 Deployment | Hardened images, CI gates, migration and recovery runbooks | In progress |
