# Evaluation report (current checkpoint)

The deterministic regression suite currently covers health output, canonical URL rejection (including invalid owner/repository and PR numbers), unified-diff line locations, Celery enqueue success/failure behavior, webhook signatures, App JWT claims, evidence verification, impact/test-gap helpers, and precision/recall scoring. It reports 21 passing tests in the local Python 3.15 environment.

Precision/recall metrics are intentionally not reported: no labeled review dataset or live provider credentials are configured yet. The next evaluation slice should add versioned fixtures for clean PR abstention, duplicate findings, and source-location accuracy.
