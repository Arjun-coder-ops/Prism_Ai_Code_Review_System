"""create review foundation tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_review_foundation"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("repositories", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("full_name", sa.String(255), nullable=False, unique=True), sa.Column("github_id", sa.Integer(), nullable=True, unique=True), sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_repositories_full_name", "repositories", ["full_name"], unique=False)
    op.create_table("reviews", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("repository_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id"), nullable=False), sa.Column("pr_number", sa.Integer(), nullable=False), sa.Column("url", sa.String(512), nullable=False), sa.Column("head_sha", sa.String(64), nullable=True), sa.Column("status", sa.Enum("queued", "fetching", "analyzing", "completed", "failed", "canceled", name="reviewstatus"), nullable=False), sa.Column("error_message", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_reviews_repository_id", "reviews", ["repository_id"])
    op.create_index("ix_reviews_head_sha", "reviews", ["head_sha"])
    op.create_index("ix_reviews_status", "reviews", ["status"])
    op.create_table("findings", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("review_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False), sa.Column("path", sa.String(512), nullable=False), sa.Column("start_line", sa.Integer(), nullable=False), sa.Column("end_line", sa.Integer(), nullable=False), sa.Column("severity", sa.String(16), nullable=False), sa.Column("category", sa.String(64), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("explanation", sa.Text(), nullable=False), sa.Column("evidence", postgresql.JSONB(), nullable=False), sa.Column("verification_state", sa.String(32), nullable=False))
    op.create_index("ix_findings_review_id", "findings", ["review_id"])

def downgrade() -> None:
    op.drop_table("findings")
    op.drop_table("reviews")
    op.drop_index("ix_repositories_full_name", table_name="repositories")
    op.drop_table("repositories")
    sa.Enum(name="reviewstatus").drop(op.get_bind(), checkfirst=True)
