"""add platform owners

Revision ID: 4b2d8b0f6c11
Revises: c3a1f9d4e8b2
Create Date: 2026-04-07 11:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4b2d8b0f6c11"
down_revision = "c3a1f9d4e8b2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "platform_owners",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("usuario", sa.String(length=80), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario"),
    )


def downgrade():
    op.drop_table("platform_owners")
