# Status

Updated 2026-11-21.

## Verified

- FastAPI app factory with CORS, structured PRISM errors, health and database-backed readiness endpoints.
- Typed review submission/status/finding schemas and PostgreSQL-oriented SQLAlchemy models.
- Canonical HTTPS GitHub pull-request URL validation with SSRF-safe parsing.
- Unified diff new-side line parsing, including multi-hunk input.
- Celery review queue configuration with JSON serialization and late acknowledgements.
- React/Vite landing and review submission form.

## Not yet verified

Live GitHub App credentials, webhook signature verification, LLM providers, migrations against PostgreSQL, and browser end-to-end tests are not configured in this environment. No production deployment or external repository comments are performed by this change.

Verification evidence: Python `compileall` passed; the focused pytest command was attempted but could not start because pytest is not installed in the current interpreter.
