"""convert quantities to integer

Revision ID: c3a1f9d4e8b2
Revises: 9d1dca4d2bc5
Create Date: 2026-04-07 10:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3a1f9d4e8b2"
down_revision = "9d1dca4d2bc5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("produtos_empresa", schema=None) as batch_op:
        batch_op.alter_column(
            "estoque_atual",
            existing_type=sa.Numeric(precision=14, scale=3),
            type_=sa.Integer(),
            existing_nullable=False,
            postgresql_using="ROUND(estoque_atual)::integer",
        )
        batch_op.alter_column(
            "estoque_minimo",
            existing_type=sa.Numeric(precision=14, scale=3),
            type_=sa.Integer(),
            existing_nullable=False,
            postgresql_using="ROUND(estoque_minimo)::integer",
        )

    with op.batch_alter_table("movimentos_estoque", schema=None) as batch_op:
        batch_op.alter_column(
            "quantidade",
            existing_type=sa.Numeric(precision=14, scale=3),
            type_=sa.Integer(),
            existing_nullable=False,
            postgresql_using="ROUND(quantidade)::integer",
        )

    with op.batch_alter_table("itens_venda", schema=None) as batch_op:
        batch_op.alter_column(
            "quantidade",
            existing_type=sa.Numeric(precision=14, scale=3),
            type_=sa.Integer(),
            existing_nullable=False,
            postgresql_using="ROUND(quantidade)::integer",
        )


def downgrade():
    with op.batch_alter_table("itens_venda", schema=None) as batch_op:
        batch_op.alter_column(
            "quantidade",
            existing_type=sa.Integer(),
            type_=sa.Numeric(precision=14, scale=3),
            existing_nullable=False,
            postgresql_using="quantidade::numeric(14,3)",
        )

    with op.batch_alter_table("movimentos_estoque", schema=None) as batch_op:
        batch_op.alter_column(
            "quantidade",
            existing_type=sa.Integer(),
            type_=sa.Numeric(precision=14, scale=3),
            existing_nullable=False,
            postgresql_using="quantidade::numeric(14,3)",
        )

    with op.batch_alter_table("produtos_empresa", schema=None) as batch_op:
        batch_op.alter_column(
            "estoque_minimo",
            existing_type=sa.Integer(),
            type_=sa.Numeric(precision=14, scale=3),
            existing_nullable=False,
            postgresql_using="estoque_minimo::numeric(14,3)",
        )
        batch_op.alter_column(
            "estoque_atual",
            existing_type=sa.Integer(),
            type_=sa.Numeric(precision=14, scale=3),
            existing_nullable=False,
            postgresql_using="estoque_atual::numeric(14,3)",
        )
