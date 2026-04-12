"""add empresa visual mode

Revision ID: d4e5f6a7b8c9
Revises: b7c9d1e2f3a4
Create Date: 2026-04-10 01:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "b7c9d1e2f3a4"
branch_labels = None
depends_on = None


visual_mode_enum = sa.Enum("MODERNO", "LEGADO", name="modovisualempresa")


def upgrade():
    visual_mode_enum.create(op.get_bind(), checkfirst=True)

    with op.batch_alter_table("empresas", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "visual_modo",
                visual_mode_enum,
                nullable=False,
                server_default="MODERNO",
            )
        )


def downgrade():
    with op.batch_alter_table("empresas", schema=None) as batch_op:
        batch_op.drop_column("visual_modo")

    visual_mode_enum.drop(op.get_bind(), checkfirst=True)
