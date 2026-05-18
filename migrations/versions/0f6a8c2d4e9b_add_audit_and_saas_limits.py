"""add audit and saas limits

Revision ID: 0f6a8c2d4e9b
Revises: c9d8e7f6a5b4
Create Date: 2026-05-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0f6a8c2d4e9b"
down_revision = "c9d8e7f6a5b4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tenants") as batch_op:
        batch_op.add_column(sa.Column("plano_codigo", sa.String(length=40), nullable=False, server_default="starter"))
        batch_op.add_column(sa.Column("assinatura_status", sa.String(length=30), nullable=False, server_default="trial"))
        batch_op.add_column(sa.Column("limite_empresas", sa.Integer(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("limite_funcionarios", sa.Integer(), nullable=False, server_default="5"))
        batch_op.add_column(sa.Column("limite_produtos", sa.Integer(), nullable=False, server_default="500"))
        batch_op.add_column(sa.Column("limite_vendas_mes", sa.Integer(), nullable=False, server_default="1500"))
        batch_op.add_column(sa.Column("trial_ate", sa.Date(), nullable=True))

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("empresa_id", sa.Integer(), nullable=True),
        sa.Column("actor_scope", sa.String(length=30), nullable=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="SUCCESS"),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("request_path", sa.String(length=255), nullable=True),
        sa.Column("request_method", sa.String(length=10), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"], unique=False)
    op.create_index("ix_audit_logs_empresa_id", "audit_logs", ["empresa_id"], unique=False)
    op.create_index("ix_audit_logs_tenant_action_created", "audit_logs", ["tenant_id", "action", "criado_em"], unique=False)
    op.create_index("ix_audit_logs_tenant_entity", "audit_logs", ["tenant_id", "entity_type", "entity_id"], unique=False)


def downgrade():
    op.drop_index("ix_audit_logs_tenant_entity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_action_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_empresa_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    with op.batch_alter_table("tenants") as batch_op:
        batch_op.drop_column("trial_ate")
        batch_op.drop_column("limite_vendas_mes")
        batch_op.drop_column("limite_produtos")
        batch_op.drop_column("limite_funcionarios")
        batch_op.drop_column("limite_empresas")
        batch_op.drop_column("assinatura_status")
        batch_op.drop_column("plano_codigo")
