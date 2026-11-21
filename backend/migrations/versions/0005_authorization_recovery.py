"""bind repositories to installations and make outbox recovery observable"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_authorization_recovery"
down_revision = "0004_review_paths"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("repositories", sa.Column("installation_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_repositories_installation_id", "repositories", ["installation_id"])
    op.create_foreign_key("fk_repositories_installation_id", "repositories", "github_installations", ["installation_id"], ["id"])
    op.add_column("outbox_events", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbox_events", sa.Column("last_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("outbox_events", "last_error")
    op.drop_column("outbox_events", "next_attempt_at")
    op.drop_constraint("fk_repositories_installation_id", "repositories", type_="foreignkey")
    op.drop_index("ix_repositories_installation_id", table_name="repositories")
    op.drop_column("repositories", "installation_id")
