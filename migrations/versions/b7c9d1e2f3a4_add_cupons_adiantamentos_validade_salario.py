"""add cupons adiantamentos validade salario

Revision ID: b7c9d1e2f3a4
Revises: 8f6e4c2a1b9d
Create Date: 2026-04-08 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b7c9d1e2f3a4"
down_revision = "8f6e4c2a1b9d"
branch_labels = None
depends_on = None


tipo_adiantamento_enum = sa.Enum("DINHEIRO", "PRODUTO", name="tipoadiantamentofuncionario")


def upgrade():
    with op.batch_alter_table("funcionarios", schema=None) as batch_op:
        batch_op.add_column(sa.Column("salario", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("meta", sa.Numeric(12, 2), nullable=False, server_default="0"))

    with op.batch_alter_table("produtos_empresa", schema=None) as batch_op:
        batch_op.add_column(sa.Column("data_validade", sa.Date(), nullable=True))

    with op.batch_alter_table("cupons", schema=None) as batch_op:
        batch_op.add_column(sa.Column("criado_por_funcionario_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_cupons_criado_por_funcionario",
            "funcionarios",
            ["criado_por_funcionario_id"],
            ["id"],
        )

    op.create_table(
        "adiantamentos_funcionario",
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("funcionario_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=True),
        sa.Column("forma_pagamento_id", sa.Integer(), nullable=False),
        sa.Column("lancamento_financeiro_id", sa.Integer(), nullable=True),
        sa.Column("movimento_estoque_id", sa.Integer(), nullable=True),
        sa.Column("tipo_adiantamento", tipo_adiantamento_enum, nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=True),
        sa.Column("valor_unitario", sa.Numeric(12, 2), nullable=True),
        sa.Column("valor_total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("data_adiantamento", sa.Date(), nullable=False),
        sa.Column("competencia", sa.Date(), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("quantidade IS NULL OR quantidade > 0", name="ck_adiantamento_quantidade_positive"),
        sa.CheckConstraint("valor_unitario IS NULL OR valor_unitario >= 0", name="ck_adiantamento_valor_unitario_non_negative"),
        sa.CheckConstraint("valor_total >= 0", name="ck_adiantamento_valor_total_non_negative"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["forma_pagamento_id"], ["formas_pagamento.id"]),
        sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"]),
        sa.ForeignKeyConstraint(["lancamento_financeiro_id"], ["lancamentos_financeiros.id"]),
        sa.ForeignKeyConstraint(["movimento_estoque_id"], ["movimentos_estoque.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_adiantamento_tenant_funcionario_competencia",
        "adiantamentos_funcionario",
        ["tenant_id", "funcionario_id", "competencia"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_adiantamento_tenant_funcionario_competencia", table_name="adiantamentos_funcionario")
    op.drop_table("adiantamentos_funcionario")

    with op.batch_alter_table("cupons", schema=None) as batch_op:
        batch_op.drop_constraint("fk_cupons_criado_por_funcionario", type_="foreignkey")
        batch_op.drop_column("criado_por_funcionario_id")

    with op.batch_alter_table("produtos_empresa", schema=None) as batch_op:
        batch_op.drop_column("data_validade")

    with op.batch_alter_table("funcionarios", schema=None) as batch_op:
        batch_op.drop_column("meta")
        batch_op.drop_column("salario")

    tipo_adiantamento_enum.drop(op.get_bind(), checkfirst=False)
