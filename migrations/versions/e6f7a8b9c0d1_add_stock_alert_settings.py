"""add stock alert settings

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-04-11 21:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e6f7a8b9c0d1"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


permission_code = "gerenciar_alerta_estoque"
permission_name = "Gerenciar configuracoes de alertas"


def _scalar(connection, query, params):
    return connection.execute(sa.text(query), params).scalar()


def upgrade():
    op.create_table(
        "configuracoes_notificacao_estoque",
        sa.Column("popup_ao_entrar", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("alertar_estoque_baixo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("alertar_sem_estoque", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("alertar_validade", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("dias_vencimento_alerta", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("email_habilitado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("email_destinatarios", sa.Text(), nullable=True),
        sa.Column("whatsapp_habilitado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("whatsapp_destinatarios", sa.Text(), nullable=True),
        sa.Column("resumo_diario", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("dias_vencimento_alerta >= 1", name="ck_config_notificacao_dias_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", name="uq_config_notificacao_estoque_tenant"),
    )
    op.create_index(
        op.f("ix_configuracoes_notificacao_estoque_tenant_id"),
        "configuracoes_notificacao_estoque",
        ["tenant_id"],
        unique=False,
    )

    connection = op.get_bind()
    tenants = connection.execute(sa.text("SELECT id FROM tenants")).fetchall()

    for tenant in tenants:
        tenant_id = tenant[0]

        permission_id = _scalar(
            connection,
            "SELECT id FROM permissions WHERE tenant_id = :tenant_id AND codigo = :codigo",
            {"tenant_id": tenant_id, "codigo": permission_code},
        )
        if permission_id:
            connection.execute(
                sa.text(
                    """
                    UPDATE permissions
                    SET nome = :nome, ativo = TRUE, atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = :permission_id
                    """
                ),
                {"nome": permission_name, "permission_id": permission_id},
            )
        else:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO permissions (nome, codigo, descricao, ativo, criado_em, atualizado_em, tenant_id)
                    VALUES (:nome, :codigo, NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id)
                    """
                ),
                {"tenant_id": tenant_id, "nome": permission_name, "codigo": permission_code},
            )

        role_id = _scalar(
            connection,
            "SELECT id FROM role WHERE tenant_id = :tenant_id AND codigo = 'administrador'",
            {"tenant_id": tenant_id},
        )
        permission_id = _scalar(
            connection,
            "SELECT id FROM permissions WHERE tenant_id = :tenant_id AND codigo = :codigo",
            {"tenant_id": tenant_id, "codigo": permission_code},
        )
        if role_id and permission_id:
            vinculo_id = _scalar(
                connection,
                """
                SELECT id FROM role_permission
                WHERE tenant_id = :tenant_id AND role_id = :role_id AND permission_id = :permission_id
                """,
                {
                    "tenant_id": tenant_id,
                    "role_id": role_id,
                    "permission_id": permission_id,
                },
            )
            if not vinculo_id:
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO role_permission (role_id, permission_id, criado_em, atualizado_em, tenant_id)
                        VALUES (:role_id, :permission_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id)
                        """
                    ),
                    {
                        "tenant_id": tenant_id,
                        "role_id": role_id,
                        "permission_id": permission_id,
                    },
                )

        existe_config = _scalar(
            connection,
            "SELECT id FROM configuracoes_notificacao_estoque WHERE tenant_id = :tenant_id",
            {"tenant_id": tenant_id},
        )
        if not existe_config:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO configuracoes_notificacao_estoque (
                        popup_ao_entrar,
                        alertar_estoque_baixo,
                        alertar_sem_estoque,
                        alertar_validade,
                        dias_vencimento_alerta,
                        email_habilitado,
                        whatsapp_habilitado,
                        resumo_diario,
                        criado_em,
                        atualizado_em,
                        tenant_id
                    )
                    VALUES (
                        TRUE,
                        TRUE,
                        TRUE,
                        TRUE,
                        30,
                        FALSE,
                        FALSE,
                        FALSE,
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP,
                        :tenant_id
                    )
                    """
                ),
                {"tenant_id": tenant_id},
            )


def downgrade():
    connection = op.get_bind()

    connection.execute(
        sa.text(
            """
            DELETE FROM role_permission
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE codigo = :codigo
            )
            """
        ),
        {"codigo": permission_code},
    )
    connection.execute(
        sa.text("DELETE FROM permissions WHERE codigo = :codigo"),
        {"codigo": permission_code},
    )

    op.drop_index(op.f("ix_configuracoes_notificacao_estoque_tenant_id"), table_name="configuracoes_notificacao_estoque")
    op.drop_table("configuracoes_notificacao_estoque")
