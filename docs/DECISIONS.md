# Decisions

1. Keep a modular monolith with Celery workers until measured load requires decomposition.
2. Use PostgreSQL as the authoritative review store; Redis is a queue/cache only.
3. Parse and validate GitHub URLs before performing network access.
