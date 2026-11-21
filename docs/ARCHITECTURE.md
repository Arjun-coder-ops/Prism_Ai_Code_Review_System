# Architecture

PRISM is a modular monolith. `app/api.py` owns HTTP contracts; `app/github` contains App authentication and webhook validation; `app/services` contains pure GitHub URL, retrieval, and diff logic; `app/analysis` and `app/verification` produce and verify evidence-backed candidates; `app/models.py` defines durable review, delivery, and outbox state; `app/workers` owns Celery wiring. Repository content is treated as data, never as executable instructions. The outbox and row-lock claim paths are designed to survive duplicate deliveries and worker restarts.
