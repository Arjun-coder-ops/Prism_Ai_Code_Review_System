# Evaluation report (current checkpoint)

The deterministic regression suite currently covers health output, canonical URL rejection (including invalid owner/repository and PR numbers), unified-diff line locations, Celery enqueue success/failure behavior, webhook signatures, App JWT claims, strict evidence verification, provider privacy/structured candidate parsing, API-key protection, impact/test-gap helpers, stale-SHA rejection, and precision/recall scoring. It reports 28 passing tests in the local Python 3.15 environment, including the versioned `review-v1` fixture. M5/M6 API persistence and M8 recovery fields are migration-verified at `0005_authorization_recovery`.

Precision/recall metrics are intentionally not reported: no labeled review dataset or live provider credentials are configured yet. The next evaluation slice should add versioned fixtures for clean PR abstention, duplicate findings, and source-location accuracy.
