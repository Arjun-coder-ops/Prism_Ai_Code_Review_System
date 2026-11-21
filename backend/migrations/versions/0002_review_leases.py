"""add durable review lease fields"""
from alembic import op
import sqlalchemy as sa

revision = "0002_review_leases"
down_revision = "0001_review_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("reviews", sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "lease_until")
    op.drop_column("reviews", "attempt_count")
