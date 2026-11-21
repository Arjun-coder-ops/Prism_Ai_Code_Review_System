# PRISM

PRISM (Pull Request Intelligence, Security, and Monitoring) is an evidence-first review workspace. This repository contains a working foundation: FastAPI health/readiness APIs, PostgreSQL review records, safe GitHub PR URL validation, unified-diff parsing, Celery/Redis queue wiring, and a small React client that submits reviews.

## Run locally

1. Copy `.env.example` to `.env`.
2. Start dependencies and services with `docker compose up --build`.
3. Open <http://localhost:5173> and submit a canonical GitHub pull-request URL.

The current slice does not claim live GitHub or LLM execution without credentials. Review retrieval and provider adapters are the next milestone; invalid hosts and malformed paths are rejected before any network request.

## Checks

```powershell
python -m pytest backend/tests
```

See [docs/STATUS.md](docs/STATUS.md) for verified scope and limitations.
