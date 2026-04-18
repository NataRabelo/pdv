"""add client wallet messaging and reversal controls

Revision ID: f2b4c6d8e9f1
Revises: e6f7a8b9c0d1
Create Date: 2026-04-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f2b4c6d8e9f1"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


tipo_pessoa_enum = postgresql.ENUM("FISICA", "JURIDICA", name="tipopessoa", create_type=False)
canal_mensagem_enum = postgresql.ENUM("EMAIL", "SMS", "WHATSAPP", name="canalmensagemcliente", create_type=False)
status_mensagem_enum = postgresql.ENUM("PENDENTE", "ENVIADO", "ERRO", name="statusmensagemcliente", create_type=False)
movimento_carteira_enum = postgresql.ENUM(
    "CREDITO",
    "DEBITO",
    "ESTORNO",
    "EXPIRACAO",
    "AJUSTE",
    name="tipomovimentocarteiracliente",
    create_type=False,
)

permission_definitions = [
    ("cancelar_item_venda", "Cancelar itens de venda"),
    ("visualizar_cliente", "Visualizar clientes"),
    ("criar_cliente", "Criar clientes"),
    ("editar_cliente", "Editar clientes"),
    ("excluir_cliente", "Excluir clientes"),
    ("enviar_mensagem_cliente", "Enviar mensagens para clientes"),
    ("gerenciar_configuracao_cliente", "Gerenciar configuracoes de clientes"),
    ("cancelar_movimentacao_estoque", "Cancelar movimentacoes de estoque"),
]


def _scalar(connection, query, params):
    return connection.execute(sa.text(query), params).scalar()


def upgrade():
    connection = op.get_bind()
    for enum_obj in (tipo_pessoa_enum, canal_mensagem_enum, status_mensagem_enum, movimento_carteira_enum):
        enum_obj.create(connection, checkfirst=True)

    op.create_table(
        "clientes",
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("documento", sa.String(length=20), nullable=True),
        sa.Column("tipo_pessoa", tipo_pessoa_enum, nullable=False, server_default="FISICA"),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("whatsapp", sa.String(length=20), nullable=True),
        sa.Column("data_nascimento", sa.Date(), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("aceita_email", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("aceita_sms", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("aceita_whatsapp", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "documento", name="uq_cliente_tenant_documento"),
    )
    op.create_index("ix_cliente_tenant_nome", "clientes", ["tenant_id", "nome"], unique=False)
    op.create_index(op.f("ix_clientes_tenant_id"), "clientes", ["tenant_id"], unique=False)

    op.create_table(
        "carteiras_cliente",
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("saldo_disponivel", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("saldo_disponivel >= 0", name="ck_carteira_cliente_saldo_non_negative"),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "cliente_id", name="uq_carteira_cliente_tenant"),
    )
    op.create_index(op.f("ix_carteiras_cliente_tenant_id"), "carteiras_cliente", ["tenant_id"], unique=False)

    op.create_table(
        "configuracoes_cliente_empresa",
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("cashback_ativo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cashback_percentual", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("cashback_validade_dias", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("cashback_valor_minimo_resgate", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("cancelamento_venda_limite_horas", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("cancelamento_item_limite_horas", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("cancelamento_movimento_limite_horas", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("email_habilitado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("email_remetente", sa.String(length=150), nullable=True),
        sa.Column("email_remetente_nome", sa.String(length=120), nullable=True),
        sa.Column("smtp_host", sa.String(length=180), nullable=True),
        sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("smtp_usuario", sa.String(length=150), nullable=True),
        sa.Column("smtp_senha", sa.String(length=255), nullable=True),
        sa.Column("smtp_tls", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("smtp_ssl", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("whatsapp_habilitado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("whatsapp_api_url", sa.String(length=255), nullable=True),
        sa.Column("whatsapp_token", sa.String(length=255), nullable=True),
        sa.Column("whatsapp_remetente", sa.String(length=80), nullable=True),
        sa.Column("sms_habilitado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sms_api_url", sa.String(length=255), nullable=True),
        sa.Column("sms_token", sa.String(length=255), nullable=True),
        sa.Column("sms_remetente", sa.String(length=80), nullable=True),
        sa.Column("request_timeout_segundos", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("cashback_percentual >= 0 AND cashback_percentual <= 100", name="ck_config_cliente_cashback_percentual_range"),
        sa.CheckConstraint("cashback_validade_dias >= 1", name="ck_config_cliente_cashback_validade_positive"),
        sa.CheckConstraint("cashback_valor_minimo_resgate >= 0", name="ck_config_cliente_cashback_resgate_non_negative"),
        sa.CheckConstraint("cancelamento_venda_limite_horas >= 0", name="ck_config_cliente_cancelamento_venda_non_negative"),
        sa.CheckConstraint("cancelamento_item_limite_horas >= 0", name="ck_config_cliente_cancelamento_item_non_negative"),
        sa.CheckConstraint("cancelamento_movimento_limite_horas >= 0", name="ck_config_cliente_cancelamento_movimento_non_negative"),
        sa.CheckConstraint("smtp_port >= 1", name="ck_config_cliente_smtp_port_positive"),
        sa.CheckConstraint("request_timeout_segundos >= 1", name="ck_config_cliente_timeout_positive"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "empresa_id", name="uq_config_cliente_empresa_tenant"),
    )
    op.create_index(op.f("ix_configuracoes_cliente_empresa_tenant_id"), "configuracoes_cliente_empresa", ["tenant_id"], unique=False)

    op.create_table(
        "mensagens_cliente",
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("funcionario_id", sa.Integer(), nullable=True),
        sa.Column("canal", canal_mensagem_enum, nullable=False),
        sa.Column("destinatario", sa.String(length=160), nullable=False),
        sa.Column("assunto", sa.String(length=160), nullable=True),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("status", status_mensagem_enum, nullable=False, server_default="PENDENTE"),
        sa.Column("resposta_integracao", sa.Text(), nullable=True),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("enviado_em", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mensagem_cliente_tenant_cliente_criado", "mensagens_cliente", ["tenant_id", "cliente_id", "criado_em"], unique=False)
    op.create_index(op.f("ix_mensagens_cliente_tenant_id"), "mensagens_cliente", ["tenant_id"], unique=False)

    op.create_table(
        "creditos_cashback_cliente",
        sa.Column("carteira_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("venda_origem_id", sa.Integer(), nullable=False),
        sa.Column("valor_original", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("saldo_disponivel", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("data_expiracao", sa.Date(), nullable=False),
        sa.Column("cancelado_em", sa.DateTime(), nullable=True),
        sa.Column("expirado_em", sa.DateTime(), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("valor_original >= 0", name="ck_credito_cashback_valor_original_non_negative"),
        sa.CheckConstraint("saldo_disponivel >= 0", name="ck_credito_cashback_saldo_non_negative"),
        sa.CheckConstraint("saldo_disponivel <= valor_original", name="ck_credito_cashback_saldo_lte_original"),
        sa.ForeignKeyConstraint(["carteira_id"], ["carteiras_cliente.id"]),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["venda_origem_id"], ["vendas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "venda_origem_id", name="uq_credito_cashback_tenant_venda_origem"),
    )
    op.create_index("ix_credito_cashback_tenant_cliente_expiracao", "creditos_cashback_cliente", ["tenant_id", "cliente_id", "data_expiracao"], unique=False)
    op.create_index(op.f("ix_creditos_cashback_cliente_tenant_id"), "creditos_cashback_cliente", ["tenant_id"], unique=False)

    op.create_table(
        "movimentos_carteira_cliente",
        sa.Column("carteira_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("credito_id", sa.Integer(), nullable=True),
        sa.Column("venda_id", sa.Integer(), nullable=True),
        sa.Column("funcionario_id", sa.Integer(), nullable=True),
        sa.Column("tipo", movimento_carteira_enum, nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=False),
        sa.Column("data_movimento", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("valor > 0", name="ck_movimento_carteira_valor_positive"),
        sa.ForeignKeyConstraint(["carteira_id"], ["carteiras_cliente.id"]),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["credito_id"], ["creditos_cashback_cliente.id"]),
        sa.ForeignKeyConstraint(["funcionario_id"], ["funcionarios.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["venda_id"], ["vendas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_movimento_carteira_tenant_cliente_data", "movimentos_carteira_cliente", ["tenant_id", "cliente_id", "data_movimento"], unique=False)
    op.create_index(op.f("ix_movimentos_carteira_cliente_tenant_id"), "movimentos_carteira_cliente", ["tenant_id"], unique=False)

    with op.batch_alter_table("vendas") as batch_op:
        batch_op.add_column(sa.Column("cliente_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cancelado_por_funcionario_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cashback_utilizado", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("cashback_gerado", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("cashback_percentual_aplicado", sa.Numeric(5, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("valor_cancelado", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("cancelado_em", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key("fk_vendas_cliente_id", "clientes", ["cliente_id"], ["id"])
        batch_op.create_foreign_key("fk_vendas_cancelado_por_funcionario_id", "funcionarios", ["cancelado_por_funcionario_id"], ["id"])

    with op.batch_alter_table("itens_venda") as batch_op:
        batch_op.add_column(sa.Column("cancelado_por_funcionario_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("quantidade_cancelada", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("valor_cancelado", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("cancelado_em", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("motivo_cancelamento", sa.Text(), nullable=True))
        batch_op.create_foreign_key("fk_itens_venda_cancelado_por_funcionario_id", "funcionarios", ["cancelado_por_funcionario_id"], ["id"])

    with op.batch_alter_table("movimentos_estoque") as batch_op:
        batch_op.add_column(sa.Column("item_venda_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("movimento_origem_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("revertido", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("cancelado_por_funcionario_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cancelado_em", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("motivo_cancelamento", sa.Text(), nullable=True))
        batch_op.create_foreign_key("fk_movimentos_estoque_item_venda_id", "itens_venda", ["item_venda_id"], ["id"])
        batch_op.create_foreign_key("fk_movimentos_estoque_movimento_origem_id", "movimentos_estoque", ["movimento_origem_id"], ["id"])
        batch_op.create_foreign_key("fk_movimentos_estoque_cancelado_por_funcionario_id", "funcionarios", ["cancelado_por_funcionario_id"], ["id"])

    with op.batch_alter_table("lancamentos_financeiros") as batch_op:
        batch_op.add_column(sa.Column("item_venda_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("lancamento_origem_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("revertido", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_foreign_key("fk_lancamentos_financeiros_item_venda_id", "itens_venda", ["item_venda_id"], ["id"])
        batch_op.create_foreign_key("fk_lancamentos_financeiros_lancamento_origem_id", "lancamentos_financeiros", ["lancamento_origem_id"], ["id"])

    tenants = connection.execute(sa.text("SELECT id FROM tenants")).fetchall()
    for tenant in tenants:
        tenant_id = tenant[0]
        for codigo, nome in permission_definitions:
            permission_id = _scalar(connection, "SELECT id FROM permissions WHERE tenant_id = :tenant_id AND codigo = :codigo", {"tenant_id": tenant_id, "codigo": codigo})
            if permission_id:
                connection.execute(sa.text("UPDATE permissions SET nome = :nome, ativo = TRUE, atualizado_em = CURRENT_TIMESTAMP WHERE id = :permission_id"), {"nome": nome, "permission_id": permission_id})
            else:
                connection.execute(sa.text("INSERT INTO permissions (nome, codigo, descricao, ativo, criado_em, atualizado_em, tenant_id) VALUES (:nome, :codigo, NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id)"), {"tenant_id": tenant_id, "nome": nome, "codigo": codigo})

        role_id = _scalar(connection, "SELECT id FROM role WHERE tenant_id = :tenant_id AND codigo = 'administrador'", {"tenant_id": tenant_id})
        if role_id:
            for codigo, _ in permission_definitions:
                permission_id = _scalar(connection, "SELECT id FROM permissions WHERE tenant_id = :tenant_id AND codigo = :codigo", {"tenant_id": tenant_id, "codigo": codigo})
                vinculo_id = _scalar(connection, "SELECT id FROM role_permission WHERE tenant_id = :tenant_id AND role_id = :role_id AND permission_id = :permission_id", {"tenant_id": tenant_id, "role_id": role_id, "permission_id": permission_id})
                if not vinculo_id:
                    connection.execute(sa.text("INSERT INTO role_permission (role_id, permission_id, criado_em, atualizado_em, tenant_id) VALUES (:role_id, :permission_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id)"), {"tenant_id": tenant_id, "role_id": role_id, "permission_id": permission_id})

    empresas = connection.execute(sa.text("SELECT id, tenant_id FROM empresas")).fetchall()
    for empresa_id, tenant_id in empresas:
        configuracao_id = _scalar(connection, "SELECT id FROM configuracoes_cliente_empresa WHERE tenant_id = :tenant_id AND empresa_id = :empresa_id", {"tenant_id": tenant_id, "empresa_id": empresa_id})
        if not configuracao_id:
            connection.execute(sa.text("""
                INSERT INTO configuracoes_cliente_empresa (
                    empresa_id, cashback_ativo, cashback_percentual, cashback_validade_dias, cashback_valor_minimo_resgate,
                    cancelamento_venda_limite_horas, cancelamento_item_limite_horas, cancelamento_movimento_limite_horas,
                    email_habilitado, smtp_port, smtp_tls, smtp_ssl, whatsapp_habilitado, sms_habilitado, request_timeout_segundos,
                    criado_em, atualizado_em, tenant_id
                ) VALUES (
                    :empresa_id, FALSE, 0, 30, 0, 24, 24, 24, FALSE, 587, TRUE, FALSE, FALSE, FALSE, 15,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id
                )
            """), {"tenant_id": tenant_id, "empresa_id": empresa_id})


def downgrade():
    connection = op.get_bind()
    for codigo, _ in permission_definitions:
        connection.execute(sa.text("DELETE FROM role_permission WHERE permission_id IN (SELECT id FROM permissions WHERE codigo = :codigo)"), {"codigo": codigo})
        connection.execute(sa.text("DELETE FROM permissions WHERE codigo = :codigo"), {"codigo": codigo})

    with op.batch_alter_table("lancamentos_financeiros") as batch_op:
        batch_op.drop_constraint("fk_lancamentos_financeiros_item_venda_id", type_="foreignkey")
        batch_op.drop_constraint("fk_lancamentos_financeiros_lancamento_origem_id", type_="foreignkey")
        batch_op.drop_column("revertido")
        batch_op.drop_column("lancamento_origem_id")
        batch_op.drop_column("item_venda_id")

    with op.batch_alter_table("movimentos_estoque") as batch_op:
        batch_op.drop_constraint("fk_movimentos_estoque_item_venda_id", type_="foreignkey")
        batch_op.drop_constraint("fk_movimentos_estoque_movimento_origem_id", type_="foreignkey")
        batch_op.drop_constraint("fk_movimentos_estoque_cancelado_por_funcionario_id", type_="foreignkey")
        batch_op.drop_column("motivo_cancelamento")
        batch_op.drop_column("cancelado_em")
        batch_op.drop_column("cancelado_por_funcionario_id")
        batch_op.drop_column("revertido")
        batch_op.drop_column("movimento_origem_id")
        batch_op.drop_column("item_venda_id")

    with op.batch_alter_table("itens_venda") as batch_op:
        batch_op.drop_constraint("fk_itens_venda_cancelado_por_funcionario_id", type_="foreignkey")
        batch_op.drop_column("motivo_cancelamento")
        batch_op.drop_column("cancelado_em")
        batch_op.drop_column("valor_cancelado")
        batch_op.drop_column("quantidade_cancelada")
        batch_op.drop_column("cancelado_por_funcionario_id")

    with op.batch_alter_table("vendas") as batch_op:
        batch_op.drop_constraint("fk_vendas_cliente_id", type_="foreignkey")
        batch_op.drop_constraint("fk_vendas_cancelado_por_funcionario_id", type_="foreignkey")
        batch_op.drop_column("cancelado_em")
        batch_op.drop_column("valor_cancelado")
        batch_op.drop_column("cashback_percentual_aplicado")
        batch_op.drop_column("cashback_gerado")
        batch_op.drop_column("cashback_utilizado")
        batch_op.drop_column("cancelado_por_funcionario_id")
        batch_op.drop_column("cliente_id")

    op.drop_index(op.f("ix_movimentos_carteira_cliente_tenant_id"), table_name="movimentos_carteira_cliente")
    op.drop_index("ix_movimento_carteira_tenant_cliente_data", table_name="movimentos_carteira_cliente")
    op.drop_table("movimentos_carteira_cliente")
    op.drop_index(op.f("ix_creditos_cashback_cliente_tenant_id"), table_name="creditos_cashback_cliente")
    op.drop_index("ix_credito_cashback_tenant_cliente_expiracao", table_name="creditos_cashback_cliente")
    op.drop_table("creditos_cashback_cliente")
    op.drop_index(op.f("ix_mensagens_cliente_tenant_id"), table_name="mensagens_cliente")
    op.drop_index("ix_mensagem_cliente_tenant_cliente_criado", table_name="mensagens_cliente")
    op.drop_table("mensagens_cliente")
    op.drop_index(op.f("ix_configuracoes_cliente_empresa_tenant_id"), table_name="configuracoes_cliente_empresa")
    op.drop_table("configuracoes_cliente_empresa")
    op.drop_index(op.f("ix_carteiras_cliente_tenant_id"), table_name="carteiras_cliente")
    op.drop_table("carteiras_cliente")
    op.drop_index(op.f("ix_clientes_tenant_id"), table_name="clientes")
    op.drop_index("ix_cliente_tenant_nome", table_name="clientes")
    op.drop_table("clientes")

    for enum_obj in (movimento_carteira_enum, status_mensagem_enum, canal_mensagem_enum, tipo_pessoa_enum):
        enum_obj.drop(connection, checkfirst=True)
