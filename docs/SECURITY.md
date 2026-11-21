# Security notes

The intake boundary accepts only `https://github.com/{owner}/{repo}/pull/{number}` and constructs provider URLs from parsed components, preventing arbitrary redirects and SSRF through submitted URLs. Private-source AI transmission remains disabled by default (`PRISM_ALLOW_PRIVATE_AI=false`). Secrets belong in environment configuration and are excluded by `.gitignore`.

GitHub webhooks require an `X-Hub-Signature-256` HMAC checked with constant-time comparison and an idempotent delivery ID. Pull-request event records and review requests are committed together with an outbox event. AI providers receive no private source unless the explicit privacy setting is enabled; the default provider is an abstaining adapter.

Installation-scoped pull-request events must reference a known, unsuspended GitHub installation, and repositories cannot be rebound across installations. The optional `PRISM_API_KEY` protects review intake with a constant-time comparison; a bounded per-client rate limiter protects expensive intake and webhook endpoints. Outbox attempts are capped and scheduled for retry, while stale worker leases are recoverable. These controls are process-local and require a shared gateway or Redis-backed limiter for multi-instance production deployments.
