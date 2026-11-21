# Start here

On Windows, install Docker Desktop and Git, copy `.env.example` to `.env`, then run `docker compose up --build`. Set `PRISM_API_KEY` for protected review intake; leave it empty only for local development. For a backend-only check, use a Python 3.12 environment and run `python -m pytest backend/tests`.

Development happens on `arjunpush`; open a pull request targeting `main` after each verified increment. Do not commit `.env` or private keys.
