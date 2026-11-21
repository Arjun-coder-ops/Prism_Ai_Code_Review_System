# PRISM security report

## Verified in this increment

- Canonical GitHub pull-request URL parsing remains HTTPS-only and rejects query, fragment, traversal, and malformed repository identifiers.
- GitHub webhook HMAC validation uses constant-time comparison.
- Pull-request webhook events require a known, unsuspended installation and cannot associate a repository with a different installation.
- Optional `PRISM_API_KEY` enforcement uses a constant-time digest comparison; the default remains disabled for local development.
- Review intake and webhook endpoints have bounded process-local rate limiting.
- Private AI transmission remains disabled unless `PRISM_ALLOW_PRIVATE_AI=true`.
- Review workers re-check the head SHA after file retrieval and reject stale analyses.
- Evidence verification requires an exact normalized changed-line match instead of substring containment.
- Outbox dispatch is capped at ten attempts with exponential delay metadata; stale review leases are recoverable by a scheduled task.

## Remaining blockers

- User identity/session authentication and GitHub OAuth are not implemented.
- Distributed rate limiting, tracing, retention, and production secret rotation remain deployment work.
- Live GitHub App credentials and private-repository integration tests were not available in this environment.
- Semgrep/Ruff/ESLint and live Groq/Gemini pipeline integration remain unfinished.
