"""İlk şema: katılımcılar, denemeler, yapay zekâ yorumları

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _schema() -> str:
    return op.get_context().opts["version_table_schema"]


def upgrade() -> None:
    schema = _schema()
    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nickname", sa.String(30), nullable=False),
        sa.Column("nickname_key", sa.String(30), nullable=False, unique=True),
        sa.Column("pin_hash", sa.LargeBinary(), nullable=False),
        sa.Column("pin_salt", sa.LargeBinary(), nullable=False),
        sa.Column("failed_pins", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_table(
        "attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("participant_id", sa.Integer(), sa.ForeignKey(f"{schema}.participants.id"), nullable=False),
        sa.Column("answers", sa.CHAR(30), nullable=False),
        sa.Column("score_rekabet", sa.SmallInteger(), nullable=False),
        sa.Column("score_isbirligi", sa.SmallInteger(), nullable=False),
        sa.Column("score_uzlasma", sa.SmallInteger(), nullable=False),
        sa.Column("score_kacinma", sa.SmallInteger(), nullable=False),
        sa.Column("score_iltifat", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema=schema,
    )
    op.create_index(
        "ix_attempts_participant_created", "attempts", ["participant_id", "created_at"], schema=schema
    )
    op.create_table(
        "ai_comments",
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey(f"{schema}.attempts.id"), primary_key=True),
        sa.Column("model", sa.String(60), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema=schema,
    )


def downgrade() -> None:
    schema = _schema()
    op.drop_table("ai_comments", schema=schema)
    op.drop_index("ix_attempts_participant_created", table_name="attempts", schema=schema)
    op.drop_table("attempts", schema=schema)
    op.drop_table("participants", schema=schema)
