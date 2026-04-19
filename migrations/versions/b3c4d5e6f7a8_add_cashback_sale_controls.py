"""add cashback sale controls

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-04-18 16:20:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "b3c4d5e6f7a8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def _get_existing_columns(table_name):
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade():
    config_columns = _get_existing_columns("configuracoes_cliente_empresa")
    with op.batch_alter_table("configuracoes_cliente_empresa") as batch_op:
        if "cashback_percentual_limite_resgate_venda" not in config_columns:
            batch_op.add_column(
                sa.Column(
                    "cashback_percentual_limite_resgate_venda",
                    sa.Numeric(5, 2),
                    nullable=False,
                    server_default="100",
                )
            )

    venda_columns = _get_existing_columns("vendas")
    with op.batch_alter_table("vendas") as batch_op:
        if "cashback_ativado" not in venda_columns:
            batch_op.add_column(
                sa.Column(
                    "cashback_ativado",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.true(),
                )
            )


def downgrade():
    venda_columns = _get_existing_columns("vendas")
    with op.batch_alter_table("vendas") as batch_op:
        if "cashback_ativado" in venda_columns:
            batch_op.drop_column("cashback_ativado")

    config_columns = _get_existing_columns("configuracoes_cliente_empresa")
    with op.batch_alter_table("configuracoes_cliente_empresa") as batch_op:
        if "cashback_percentual_limite_resgate_venda" in config_columns:
            batch_op.drop_column("cashback_percentual_limite_resgate_venda")
