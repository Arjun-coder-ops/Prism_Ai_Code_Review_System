# Test report

The focused suite is in `backend/tests` and covers the health endpoint, unsafe URL rejection, canonical URL parsing, and unified-diff line tracking.

Observed in this workspace:

- `python -m compileall -q backend/app backend/tests`: passed.
- `python -m pytest backend/tests -q`: not run because `pytest` is not installed (`No module named pytest`).

Live PostgreSQL, Redis, GitHub, and browser checks remain pending because no external credentials were supplied.
