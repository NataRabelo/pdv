"""add wholesale pricing and fiscal foundation

Revision ID: a4f1c8d2e7b9
Revises: f2b4c6d8e9f1
Create Date: 2026-04-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a4f1c8d2e7b9"
down_revision = "f2b4c6d8e9f1"
branch_labels = None
depends_on = None


modalidade_preco_enum = postgresql.ENUM(
    "VAREJO",
    "ATACADO",
    "AUTOMATICO",
    name="modalidadeprecovenda",
    create_type=False,
)
ambiente_fiscal_enum = postgresql.ENUM(
    "HOMOLOGACAO",
    "PRODUCAO",
    name="ambientefiscal",
    create_type=False,
)
regime_tributario_enum = postgresql.ENUM(
    "SIMPLES_NACIONAL",
    "LUCRO_PRESUMIDO",
    "LUCRO_REAL",
    name="regimetributariofiscal",
    create_type=False,
)
status_nota_fiscal_enum = postgresql.ENUM(
    "PENDENTE",
    "VALIDACAO_ERRO",
    "PRONTA_PARA_EMISSAO",
    "EMITIDA",
    "REJEITADA",
    "CANCELADA",
    name="statusnotafiscal",
    create_type=False,
)

permission_definitions = [
    ("visualizar_fiscal", "Visualizar fiscal"),
    ("gerenciar_fiscal", "Gerenciar fiscal"),
]


def _scalar(connection, query, params):
    return connection.execute(sa.text(query), params).scalar()


def upgrade():
    connection = op.get_bind()
    for enum_obj in (
        modalidade_preco_enum,
        ambiente_fiscal_enum,
        regime_tributario_enum,
        status_nota_fiscal_enum,
    ):
        enum_obj.create(connection, checkfirst=True)

    with op.batch_alter_table("produtos_empresa") as batch_op:
        batch_op.add_column(sa.Column("valor_varejo", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("valor_atacado", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("quantidade_minima_atacado", sa.Integer(), nullable=False, server_default="1"))

    connection.execute(sa.text("""
        UPDATE produtos_empresa
        SET valor_varejo = valor_venda,
            valor_atacado = valor_venda,
            quantidade_minima_atacado = 1
    """))

    with op.batch_alter_table("produtos_empresa") as batch_op:
        batch_op.create_check_constraint(
            "ck_produto_empresa_valor_varejo_non_negative",
            "valor_varejo >= 0",
        )
        batch_op.create_check_constraint(
            "ck_produto_empresa_valor_atacado_non_negative",
            "valor_atacado >= 0",
        )
        batch_op.create_check_constraint(
            "ck_produto_empresa_qtd_min_atacado_positive",
            "quantidade_minima_atacado >= 1",
        )

    with op.batch_alter_table("vendas") as batch_op:
        batch_op.add_column(
            sa.Column(
                "modalidade_preco",
                modalidade_preco_enum,
                nullable=False,
                server_default="VAREJO",
            )
        )

    with op.batch_alter_table("itens_venda") as batch_op:
        batch_op.add_column(
            sa.Column(
                "modalidade_preco_aplicada",
                modalidade_preco_enum,
                nullable=False,
                server_default="VAREJO",
            )
        )

    op.create_table(
        "configuracoes_fiscais_empresa",
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("ambiente", ambiente_fiscal_enum, nullable=False, server_default="HOMOLOGACAO"),
        sa.Column("regime_tributario", regime_tributario_enum, nullable=False, server_default="SIMPLES_NACIONAL"),
        sa.Column("serie_nfce", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("proximo_numero_nfce", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("inscricao_estadual", sa.String(length=30), nullable=True),
        sa.Column("inscricao_municipal", sa.String(length=30), nullable=True),
        sa.Column("cnae", sa.String(length=20), nullable=True),
        sa.Column("uf", sa.String(length=2), nullable=True),
        sa.Column("municipio_nome", sa.String(length=120), nullable=True),
        sa.Column("municipio_codigo_ibge", sa.String(length=7), nullable=True),
        sa.Column("cep", sa.String(length=10), nullable=True),
        sa.Column("logradouro", sa.String(length=180), nullable=True),
        sa.Column("numero", sa.String(length=20), nullable=True),
        sa.Column("complemento", sa.String(length=120), nullable=True),
        sa.Column("bairro", sa.String(length=120), nullable=True),
        sa.Column("certificado_caminho", sa.String(length=255), nullable=True),
        sa.Column("certificado_senha_env", sa.String(length=120), nullable=True),
        sa.Column("csc_id", sa.String(length=20), nullable=True),
        sa.Column("csc_token", sa.String(length=255), nullable=True),
        sa.Column("contingencia_ativa", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ultimo_teste_certificado_em", sa.DateTime(), nullable=True),
        sa.Column("ultimo_teste_certificado_status", sa.String(length=30), nullable=True),
        sa.Column("ultimo_teste_certificado_detalhe", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("serie_nfce >= 1", name="ck_config_fiscal_serie_positive"),
        sa.CheckConstraint("proximo_numero_nfce >= 1", name="ck_config_fiscal_proximo_numero_positive"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "empresa_id", name="uq_config_fiscal_empresa_tenant"),
    )
    op.create_index(op.f("ix_configuracoes_fiscais_empresa_tenant_id"), "configuracoes_fiscais_empresa", ["tenant_id"], unique=False)

    op.create_table(
        "notas_fiscais_venda",
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("venda_id", sa.Integer(), nullable=False),
        sa.Column("configuracao_fiscal_id", sa.Integer(), nullable=True),
        sa.Column("ambiente", ambiente_fiscal_enum, nullable=False, server_default="HOMOLOGACAO"),
        sa.Column("status", status_nota_fiscal_enum, nullable=False, server_default="PENDENTE"),
        sa.Column("serie", sa.Integer(), nullable=True),
        sa.Column("numero", sa.Integer(), nullable=True),
        sa.Column("chave_acesso", sa.String(length=60), nullable=True),
        sa.Column("recibo", sa.String(length=60), nullable=True),
        sa.Column("protocolo", sa.String(length=60), nullable=True),
        sa.Column("xml_path", sa.String(length=255), nullable=True),
        sa.Column("mensagem_retorno", sa.Text(), nullable=True),
        sa.Column("enviado_em", sa.DateTime(), nullable=True),
        sa.Column("emitida_em", sa.DateTime(), nullable=True),
        sa.Column("cancelada_em", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["configuracao_fiscal_id"], ["configuracoes_fiscais_empresa.id"]),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["venda_id"], ["vendas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "venda_id", name="uq_nota_fiscal_venda_tenant"),
        sa.UniqueConstraint("tenant_id", "empresa_id", "serie", "numero", name="uq_nota_fiscal_tenant_empresa_serie_numero"),
    )
    op.create_index("ix_nota_fiscal_tenant_empresa_status", "notas_fiscais_venda", ["tenant_id", "empresa_id", "status"], unique=False)
    op.create_index(op.f("ix_notas_fiscais_venda_tenant_id"), "notas_fiscais_venda", ["tenant_id"], unique=False)

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
                        "UPDATE permissions SET nome = :nome, ativo = TRUE, atualizado_em = CURRENT_TIMESTAMP WHERE id = :permission_id"
                    ),
                    {"nome": nome, "permission_id": permission_id},
                )
            else:
                connection.execute(
                    sa.text(
                        "INSERT INTO permissions (nome, codigo, descricao, ativo, criado_em, atualizado_em, tenant_id) "
                        "VALUES (:nome, :codigo, NULL, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id)"
                    ),
                    {"tenant_id": tenant_id, "nome": nome, "codigo": codigo},
                )

        role_id = _scalar(
            connection,
            "SELECT id FROM role WHERE tenant_id = :tenant_id AND codigo = 'administrador'",
            {"tenant_id": tenant_id},
        )
        if role_id:
            for codigo, _ in permission_definitions:
                permission_id = _scalar(
                    connection,
                    "SELECT id FROM permissions WHERE tenant_id = :tenant_id AND codigo = :codigo",
                    {"tenant_id": tenant_id, "codigo": codigo},
                )
                vinculo_id = _scalar(
                    connection,
                    "SELECT id FROM role_permission WHERE tenant_id = :tenant_id AND role_id = :role_id AND permission_id = :permission_id",
                    {"tenant_id": tenant_id, "role_id": role_id, "permission_id": permission_id},
                )
                if not vinculo_id:
                    connection.execute(
                        sa.text(
                            "INSERT INTO role_permission (role_id, permission_id, criado_em, atualizado_em, tenant_id) "
                            "VALUES (:role_id, :permission_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :tenant_id)"
                        ),
                        {"tenant_id": tenant_id, "role_id": role_id, "permission_id": permission_id},
                    )


def downgrade():
    connection = op.get_bind()
    for codigo, _ in permission_definitions:
        connection.execute(
            sa.text("DELETE FROM role_permission WHERE permission_id IN (SELECT id FROM permissions WHERE codigo = :codigo)"),
            {"codigo": codigo},
        )
        connection.execute(sa.text("DELETE FROM permissions WHERE codigo = :codigo"), {"codigo": codigo})

    op.drop_index(op.f("ix_notas_fiscais_venda_tenant_id"), table_name="notas_fiscais_venda")
    op.drop_index("ix_nota_fiscal_tenant_empresa_status", table_name="notas_fiscais_venda")
    op.drop_table("notas_fiscais_venda")

    op.drop_index(op.f("ix_configuracoes_fiscais_empresa_tenant_id"), table_name="configuracoes_fiscais_empresa")
    op.drop_table("configuracoes_fiscais_empresa")

    with op.batch_alter_table("itens_venda") as batch_op:
        batch_op.drop_column("modalidade_preco_aplicada")

    with op.batch_alter_table("vendas") as batch_op:
        batch_op.drop_column("modalidade_preco")

    with op.batch_alter_table("produtos_empresa") as batch_op:
        batch_op.drop_constraint("ck_produto_empresa_qtd_min_atacado_positive", type_="check")
        batch_op.drop_constraint("ck_produto_empresa_valor_atacado_non_negative", type_="check")
        batch_op.drop_constraint("ck_produto_empresa_valor_varejo_non_negative", type_="check")
        batch_op.drop_column("quantidade_minima_atacado")
        batch_op.drop_column("valor_atacado")
        batch_op.drop_column("valor_varejo")

    for enum_obj in (
        status_nota_fiscal_enum,
        regime_tributario_enum,
        ambiente_fiscal_enum,
        modalidade_preco_enum,
    ):
        enum_obj.drop(connection, checkfirst=True)
