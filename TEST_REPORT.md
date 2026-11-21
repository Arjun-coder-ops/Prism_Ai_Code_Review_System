# Test report

The focused suite is in `backend/tests` and covers the health endpoint, unsafe URL rejection, canonical URL parsing, and unified-diff line tracking.

Observed in this workspace:

- `python -m ruff check app tests`: passed.
- `python -m mypy app`: passed with no issues.
- `python -m pytest -q`: passed, 32 tests with 5 integration tests skipped by default, including provider selection/fallback, stale-SHA, strict evidence, API-key, repository allowlist, retry-state, and executable `review-v1` regression coverage.
- `PRISM_INTEGRATION=1 python -m pytest -q tests/integration` against Docker PostgreSQL/Redis: passed, 5 tests covering Redis reachability, duplicate deliveries, expired leases, concurrent claims, and pending outbox retry state.
- `python -m alembic upgrade head` from `backend/` against Docker PostgreSQL: passed; current revision `0006_ai_usage`.
- PostgreSQL schema query: installation-bound repositories, bounded outbox retry fields, M3 event/outbox tables, and the `reviews.changed_paths` intelligence field are present.
- `npm run build`: passed with Vite.
- The local in-app browser could not reach the Vite dev server, so rendered viewport/accessibility evidence is explicitly untested; source and production-build checks passed.
- `docker compose config`: passed.
- `docker compose up -d --build api worker frontend`, then `GET http://localhost:8000/api/health`: passed (`{"status":"ok","version":"0.1.0"}`); frontend returned HTTP 200.
- `.github/workflows/ci.yml` parsed locally and now provisions PostgreSQL/Redis, runs Ruff, mypy, migrations, the default pytest suite, and the integration suite before the frontend job. Compose includes a dedicated Celery Beat service.
- Full tracked-source checkpoint archive is verified after clean extraction; its SHA-256 is recorded in the adjacent `.sha256` sidecar file.

Live PostgreSQL, Redis, GitHub, and browser checks remain pending because no external credentials were supplied.
