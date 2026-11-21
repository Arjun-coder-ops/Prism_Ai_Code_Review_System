"""record review AI provider usage"""
from alembic import op
import sqlalchemy as sa

revision = "0006_ai_usage"
down_revision = "0005_authorization_recovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("ai_provider", sa.String(32), nullable=True))
    op.add_column("reviews", sa.Column("ai_tokens", sa.Integer(), server_default="0", nullable=False))
    op.add_column("reviews", sa.Column("ai_cost_usd", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "ai_cost_usd")
    op.drop_column("reviews", "ai_tokens")
    op.drop_column("reviews", "ai_provider")
