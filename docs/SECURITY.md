# Security notes

The intake boundary accepts only `https://github.com/{owner}/{repo}/pull/{number}` and constructs provider URLs from parsed components, preventing arbitrary redirects and SSRF through submitted URLs. Private-source AI transmission remains disabled by default (`PRISM_ALLOW_PRIVATE_AI=false`). Secrets belong in environment configuration and are excluded by `.gitignore`.

GitHub webhooks require an `X-Hub-Signature-256` HMAC checked with constant-time comparison and an idempotent delivery ID. Pull-request event records and review requests are committed together with an outbox event. AI providers receive no private source unless the explicit privacy setting is enabled; the default provider is an abstaining adapter.
