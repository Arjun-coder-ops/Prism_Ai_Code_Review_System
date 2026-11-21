# Architecture

PRISM is a modular monolith. `app/api.py` owns HTTP contracts; `app/services` contains pure GitHub URL and diff logic; `app/models.py` defines durable review state; `app/workers` owns Celery wiring. Repository content is treated as data, never as executable instructions. The next integration stage will add commit-pinned GitHub retrieval and an outbox-backed worker task.
