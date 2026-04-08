"""add pdv financeiro permissions and defaults

Revision ID: 8f6e4c2a1b9d
Revises: 4b2d8b0f6c11
Create Date: 2026-04-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "8f6e4c2a1b9d"
down_revision = "4b2d8b0f6c11"
branch_labels = None
depends_on = None


permission_definitions = [
    ("visualizar_pdv", "Visualizar PDV"),
    ("registrar_venda", "Registrar vendas"),
    ("cancelar_venda", "Cancelar vendas"),
    ("visualizar_financeiro", "Visualizar financeiro"),
    ("criar_lancamento_financeiro", "Criar lancamentos financeiros"),
    ("fechar_caixa", "Fechar caixa"),
]

role_permission_definitions = {
    "administrador": [codigo for codigo, _ in permission_definitions],
    "operador": [
        "visualizar_pdv",
        "registrar_venda",
        "visualizar_financeiro",
        "criar_lancamento_financeiro",
        "fechar_caixa",
    ],
}

formas_pagamento = [
    "Dinheiro",
    "Pix",
    "Cartao de debito",
    "Cartao de credito",
    "Boleto",
    "Crediario",
]

categorias_financeiras = [
    ("Vendas PDV", "ENTRADA"),
    ("Aporte de caixa", "ENTRADA"),
    ("Outras entradas", "ENTRADA"),
    ("Compras de mercadorias", "SAIDA"),
    ("Despesas operacionais", "SAIDA"),
    ("Estorno de vendas", "SAIDA"),
    ("Sangria de caixa", "SAIDA"),
]

tipos_operacao = [
    ("Venda PDV", "VENDA_PADRAO", "VENDA"),
    ("Entrada manual de estoque", "ENTRADA_ESTOQUE_PADRAO", "ENTRADA_ESTOQUE"),
    ("Ajuste de estoque", "AJUSTE_ESTOQUE_PADRAO", "AJUSTE_ESTOQUE"),
    ("Transferencia interna", "TRANSFERENCIA_PADRAO", "TRANSFERENCIA"),
]


def _scalar(connection, query, params):
    return connection.execute(sa.text(query), params).scalar()


def upgrade():
    connection = op.get_bind()
    tenants = connection.execute(sa.text("SELECT id FROM tenants")).fetchall()

    for tenant in tenants:
        tenant_id = tenant[0]

        for codigo, nome in permission_definitions:
            permission_id = _scalar(
                connection,
                "SELECT id FROM permissions WHERE tenant_id = :tenant_id AND codigo = :codigo",
                {"tenant_id": tenant_id, "codigo": codigo},
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
                    {"nome": nome, "permission_id": permission_id},
                )
            else:
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO permissions (nome, codigo, descricao, ativo, criado_em, atualizado_em, tenant_id)
                        VALUES (:nome, :codigo, NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id)
                        """
                    ),
                    {"nome": nome, "codigo": codigo, "tenant_id": tenant_id},
                )

        for role_code, permissions in role_permission_definitions.items():
            role_id = _scalar(
                connection,
                "SELECT id FROM role WHERE tenant_id = :tenant_id AND codigo = :codigo",
                {"tenant_id": tenant_id, "codigo": role_code},
            )
            if not role_id:
                continue

            for permission_code in permissions:
                permission_id = _scalar(
                    connection,
                    "SELECT id FROM permissions WHERE tenant_id = :tenant_id AND codigo = :codigo",
                    {"tenant_id": tenant_id, "codigo": permission_code},
                )
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

        for nome in formas_pagamento:
            forma_id = _scalar(
                connection,
                "SELECT id FROM formas_pagamento WHERE tenant_id = :tenant_id AND nome = :nome",
                {"tenant_id": tenant_id, "nome": nome},
            )
            if forma_id:
                connection.execute(
                    sa.text(
                        """
                        UPDATE formas_pagamento
                        SET ativo = TRUE, atualizado_em = CURRENT_TIMESTAMP
                        WHERE id = :forma_id
                        """
                    ),
                    {"forma_id": forma_id},
                )
            else:
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO formas_pagamento (nome, ativo, criado_em, atualizado_em, tenant_id)
                        VALUES (:nome, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id)
                        """
                    ),
                    {"tenant_id": tenant_id, "nome": nome},
                )

        for nome, tipo in categorias_financeiras:
            categoria_id = _scalar(
                connection,
                """
                SELECT id FROM categorias_financeiras
                WHERE tenant_id = :tenant_id AND nome = :nome AND tipo_categoria = :tipo
                """,
                {"tenant_id": tenant_id, "nome": nome, "tipo": tipo},
            )
            if categoria_id:
                connection.execute(
                    sa.text(
                        """
                        UPDATE categorias_financeiras
                        SET ativo = TRUE, atualizado_em = CURRENT_TIMESTAMP
                        WHERE id = :categoria_id
                        """
                    ),
                    {"categoria_id": categoria_id},
                )
            else:
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO categorias_financeiras (nome, tipo_categoria, ativo, criado_em, atualizado_em, tenant_id)
                        VALUES (:nome, :tipo, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id)
                        """
                    ),
                    {"tenant_id": tenant_id, "nome": nome, "tipo": tipo},
                )

        for nome, codigo, tipo in tipos_operacao:
            operacao_id = _scalar(
                connection,
                "SELECT id FROM tipos_operacao WHERE tenant_id = :tenant_id AND codigo = :codigo",
                {"tenant_id": tenant_id, "codigo": codigo},
            )
            if operacao_id:
                connection.execute(
                    sa.text(
                        """
                        UPDATE tipos_operacao
                        SET nome = :nome, tipo_operacao = :tipo, ativo = TRUE, atualizado_em = CURRENT_TIMESTAMP
                        WHERE id = :operacao_id
                        """
                    ),
                    {"nome": nome, "tipo": tipo, "operacao_id": operacao_id},
                )
            else:
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO tipos_operacao (nome, codigo, tipo_operacao, ativo, criado_em, atualizado_em, tenant_id)
                        VALUES (:nome, :codigo, :tipo, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id)
                        """
                    ),
                    {"tenant_id": tenant_id, "nome": nome, "codigo": codigo, "tipo": tipo},
                )


def downgrade():
    connection = op.get_bind()

    for codigo, _ in permission_definitions:
        connection.execute(
            sa.text(
                """
                DELETE FROM role_permission
                WHERE permission_id IN (
                    SELECT id FROM permissions WHERE codigo = :codigo
                )
                """
            ),
            {"codigo": codigo},
        )
        connection.execute(
            sa.text("DELETE FROM permissions WHERE codigo = :codigo"),
            {"codigo": codigo},
        )

    for nome in formas_pagamento:
        connection.execute(
            sa.text("DELETE FROM formas_pagamento WHERE nome = :nome"),
            {"nome": nome},
        )

    for nome, tipo in categorias_financeiras:
        connection.execute(
            sa.text(
                "DELETE FROM categorias_financeiras WHERE nome = :nome AND tipo_categoria = :tipo"
            ),
            {"nome": nome, "tipo": tipo},
        )

    for _, codigo, _ in tipos_operacao:
        connection.execute(
            sa.text("DELETE FROM tipos_operacao WHERE codigo = :codigo"),
            {"codigo": codigo},
        )
