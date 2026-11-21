# Manual commit guide

Suggested sequence (run from the repository root):

```powershell
git add .; git commit -m "chore: initialize PRISM monorepo"
git add backend; git commit -m "feat(api): establish FastAPI review foundation"
git add frontend; git commit -m "feat(ui): add PRISM review submission experience"
git add docs README.md; git commit -m "docs: document verified scope and limitations"
```

Review `git diff` before each commit. This file is intentionally a guide; the repository owner controls commits and merges.
