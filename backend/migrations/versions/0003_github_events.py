"""add GitHub installation, webhook, and outbox tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_github_events"
down_revision = "0002_review_leases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("github_installations", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("installation_id", sa.Integer(), nullable=False, unique=True), sa.Column("account_login", sa.String(255), nullable=False), sa.Column("suspended_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_github_installations_installation_id", "github_installations", ["installation_id"])
    op.create_index("ix_github_installations_account_login", "github_installations", ["account_login"])
    op.create_table("webhook_deliveries", sa.Column("delivery_id", sa.String(128), primary_key=True), sa.Column("event_name", sa.String(64), nullable=False), sa.Column("payload_hash", sa.String(64), nullable=False), sa.Column("processed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("outbox_events", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("event_type", sa.String(128), nullable=False), sa.Column("aggregate_id", sa.String(128), nullable=False), sa.Column("payload", postgresql.JSONB(), nullable=False), sa.Column("attempts", sa.Integer(), server_default="0", nullable=False), sa.Column("published_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_outbox_events_event_type", "outbox_events", ["event_type"])
    op.create_index("ix_outbox_events_aggregate_id", "outbox_events", ["aggregate_id"])


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("webhook_deliveries")
    op.drop_index("ix_github_installations_account_login", table_name="github_installations")
    op.drop_index("ix_github_installations_installation_id", table_name="github_installations")
    op.drop_table("github_installations")
