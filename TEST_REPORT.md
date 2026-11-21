# Test report

The focused suite is in `backend/tests` and covers the health endpoint, unsafe URL rejection, canonical URL parsing, and unified-diff line tracking. Run `python -m pytest backend/tests` in an environment with backend dependencies installed. Live PostgreSQL, Redis, GitHub, and browser checks remain pending because no external credentials were supplied.
