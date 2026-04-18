"""add stock alert dispatch tracking

Revision ID: a1b2c3d4e5f6
Revises: f2b4c6d8e9f1
Create Date: 2026-04-18 03:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "f2b4c6d8e9f1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("produtos_empresa") as batch_op:
        batch_op.add_column(sa.Column("ultimo_alerta_estoque_status", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("ultimo_alerta_estoque_em", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("produtos_empresa") as batch_op:
        batch_op.drop_column("ultimo_alerta_estoque_em")
        batch_op.drop_column("ultimo_alerta_estoque_status")
