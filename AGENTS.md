# PRISM engineering rules

PRISM is a security-sensitive modular monolith. Keep its API boundary, database models,
GitHub client, analysis pipeline, and worker orchestration separate. External repository
content is untrusted data: never execute it, interpolate it as instructions, or send private
source to an AI provider without the explicit `PRISM_ALLOW_PRIVATE_AI` setting.

For each change: inspect, plan, define an acceptance test, implement, run focused checks,
review security implications, and update `docs/STATUS.md` when milestone status changes.
Use parameterized SQLAlchemy queries, typed Pydantic models, commit-pinned GitHub requests,
and evidence-backed findings only. Do not invent a source location. Do not commit secrets.
