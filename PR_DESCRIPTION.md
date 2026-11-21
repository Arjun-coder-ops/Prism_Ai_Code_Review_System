# PRISM reliability and authorization hardening

This pull request advances `arjunpush` toward `main` with a focused security and recovery increment.

## Included

- Installation-scoped GitHub webhook authorization and repository binding.
- Optional API-key protection and bounded intake rate limiting.
- Scheduled stale-review lease recovery and bounded, delayed outbox retries.
- Commit-SHA revalidation after changed-file retrieval.
- Exact changed-line evidence verification to reduce false positives.
- Celery Beat is now a first-class Compose service for scheduled outbox dispatch and stale-review recovery.
- Review-detail, findings, impact, and test-gap reads enforce API-key and repository allowlist checks.
- Retry exhaustion is terminal and stale recovery emits durable redispatch work without duplicating findings.
- Docker PostgreSQL/Redis integration tests cover duplicate deliveries, expired leases, concurrent claims, and outbox durability.
- M4 Groq-first/Gemini-fallback adapters with structured untrusted-diff prompts, bounded retries, private-source gating, usage capture, and worker integration.
- Migrations `0005_authorization_recovery` and `0006_ai_usage`.
- M6 persists the commit-pinned GitHub repository tree and uses it for test-gap recommendations.
- Regression coverage expanded to 32 local tests plus 5 Docker integration tests.

## Verification

- Ruff: passed
- Mypy: passed
- Pytest: 32 passed locally; 5 Docker integration tests passed
- Alembic upgrade against Docker PostgreSQL: passed at `0007_test_paths`

Live GitHub credentials, distributed deployment checks, and production provider credentials remain explicitly out of scope for this local verification.
