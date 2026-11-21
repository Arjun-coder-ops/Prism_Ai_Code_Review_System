# PRISM reliability and authorization hardening

This pull request advances `arjunpush` toward `main` with a focused security and recovery increment.

## Included

- Installation-scoped GitHub webhook authorization and repository binding.
- Optional API-key protection and bounded intake rate limiting.
- Scheduled stale-review lease recovery and bounded, delayed outbox retries.
- Commit-SHA revalidation after changed-file retrieval.
- Exact changed-line evidence verification to reduce false positives.
- Migration `0005_authorization_recovery`.
- Regression coverage expanded from 24 to 28 tests.

## Verification

- Ruff: passed
- Mypy: passed
- Pytest: 28 passed
- Alembic upgrade against Docker PostgreSQL: passed at `0005_authorization_recovery`

Live GitHub credentials, distributed deployment checks, and production provider credentials remain explicitly out of scope for this local verification.
