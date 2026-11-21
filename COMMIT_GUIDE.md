# Manual commit guide

Suggested sequence (run from the repository root):

```powershell
git add .; git commit -m "chore: initialize PRISM monorepo"
git add backend/app backend/migrations backend/tests; git commit -m "feat(api): establish durable review foundation"
git add frontend; git commit -m "feat(ui): add PRISM review submission experience"
git add docs README.md TEST_REPORT.md MILESTONE_AUDIT.md EVALUATION_REPORT.md; git commit -m "docs: record verification evidence and milestone scope"
```

For the current uncommitted checkpoint, the second commit contains the CI fixes, strict GitHub URL validation, paginated file retrieval, Celery dispatch/retry workflow, PostgreSQL lease migration, M3 webhook/outbox primitives, deterministic analysis/evaluation helpers, and 21-test regression suite. Run `git diff --check` before staging.

Review `git diff` before each commit. This file is intentionally a guide; the repository owner controls commits and merges.
