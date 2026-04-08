from datetime import date
import enum

from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import validates

from app.extensions import db
from app.services.time_service import TimeService


class TipoEmpresa(enum.Enum):
    MATRIZ = "MATRIZ"
    FILIAL = "FILIAL"


class TipoFinanceiro(enum.Enum):
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"


class TipoCategoriaFinanceira(enum.Enum):
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"


class TipoMovimentoEstoque(enum.Enum):
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"


class MotivoMovimentoEstoque(enum.Enum):
    COMPRA = "COMPRA"
    VENDA = "VENDA"
    AJUSTE = "AJUSTE"
    PERDA = "PERDA"
    DEVOLUCAO = "DEVOLUCAO"
    TRANSFERENCIA = "TRANSFERENCIA"


class TipoOperacaoEnum(enum.Enum):
    VENDA = "VENDA"
    ENTRADA_ESTOQUE = "ENTRADA_ESTOQUE"
    AJUSTE_ESTOQUE = "AJUSTE_ESTOQUE"
    TRANSFERENCIA = "TRANSFERENCIA"


class TipoDesconto(enum.Enum):
    PERCENTUAL = "PERCENTUAL"
    VALOR = "VALOR"


class StatusVenda(enum.Enum):
    ABERTA = "ABERTA"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"


class ModeloBase(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=TimeService.now_utc_naive)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=TimeService.now_utc_naive, onupdate=TimeService.now_utc_naive)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False, index=True)


class Tenant(db.Model):
    __tablename__ = "tenants"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=TimeService.now_utc_naive)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=TimeService.now_utc_naive, onupdate=TimeService.now_utc_naive)

    empresas = db.relationship("Empresa", backref="tenant", lazy=True, cascade="all, delete-orphan")
    funcionarios = db.relationship("Funcionario", backref="tenant", lazy=True, cascade="all, delete-orphan")
    produtos = db.relationship("Produto", backref="tenant", lazy=True, cascade="all, delete-orphan")
    roles = db.relationship("Role", backref="tenant", lazy=True, cascade="all, delete-orphan")
    permissions = db.relationship("Permission", backref="tenant", lazy=True, cascade="all, delete-orphan")


class PlatformOwner(db.Model):
    __tablename__ = "platform_owners"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    usuario = db.Column(db.String(80), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=TimeService.now_utc_naive)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=TimeService.now_utc_naive, onupdate=TimeService.now_utc_naive)


class Empresa(ModeloBase):
    __tablename__ = "empresas"

    cnpj = db.Column(db.String(18), nullable=False)
    razao_social = db.Column(db.String(180), nullable=False)
    nome_fantasia = db.Column(db.String(180), nullable=False)
    tipo_empresa = db.Column(db.Enum(TipoEmpresa), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "cnpj", name="uq_empresa_tenant_cnpj"),
        UniqueConstraint("tenant_id", "nome_fantasia", name="uq_empresa_tenant_nome_fantasia"),
    )


class Role(ModeloBase):
    __tablename__ = "role"

    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", name="uq_role_tenant_nome"),
        UniqueConstraint("tenant_id", "codigo", name="uq_role_tenant_codigo"),
    )


class Permission(ModeloBase):
    __tablename__ = "permissions"

    nome = db.Column(db.String(120), nullable=False)
    codigo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_permission_tenant_codigo"),
    )


class RolePermission(ModeloBase):
    __tablename__ = "role_permission"

    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey("permissions.id"), nullable=False)

    role = db.relationship(
        "Role",
        backref=db.backref("permissions_links", lazy=True, cascade="all, delete-orphan")
    )
    permission = db.relationship(
        "Permission",
        backref=db.backref("roles_links", lazy=True, cascade="all, delete-orphan")
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "role_id", "permission_id", name="uq_role_permission"),
    )


class Funcionario(ModeloBase):
    __tablename__ = "funcionarios"

    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    usuario = db.Column(db.String(80), nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    role = db.relationship("Role", backref=db.backref("funcionarios", lazy=True))

    __table_args__ = (
        UniqueConstraint("tenant_id", "cpf", name="uq_funcionario_tenant_cpf"),
        UniqueConstraint("tenant_id", "usuario", name="uq_funcionario_tenant_usuario"),
    )


class FuncionarioEmpresa(ModeloBase):
    __tablename__ = "funcionarios_empresa"

    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    funcionario = db.relationship(
        "Funcionario",
        backref=db.backref("empresas_vinculadas", lazy=True, cascade="all, delete-orphan")
    )
    empresa = db.relationship(
        "Empresa",
        backref=db.backref("funcionarios_vinculados", lazy=True, cascade="all, delete-orphan")
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "funcionario_id", "empresa_id", name="uq_funcionario_empresa"),
    )


class CategoriaProduto(ModeloBase):
    __tablename__ = "categorias_produto"

    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", name="uq_categoria_produto_tenant_nome"),
    )


class Produto(ModeloBase):
    __tablename__ = "produtos"

    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias_produto.id"), nullable=True)
    criado_por_funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    possui_ncm = db.Column(db.Boolean, nullable=False, default=False)
    ncm = db.Column(db.String(20), nullable=True)
    codigo_barras = db.Column(db.String(60), nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    categoria = db.relationship("CategoriaProduto", backref=db.backref("produtos", lazy=True))
    criado_por = db.relationship("Funcionario", backref=db.backref("produtos_criados", lazy=True))

    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", name="uq_produto_tenant_nome"),
        UniqueConstraint("tenant_id", "codigo_barras", name="uq_produto_tenant_codigo_barras"),
        CheckConstraint("possui_ncm = FALSE OR ncm IS NOT NULL", name="ck_produto_ncm_flag"),
    )

    @validates("ncm")
    def validar_ncm(self, key, value):
        if self.possui_ncm and not value:
            raise ValueError("Produto com possui_ncm=True deve ter NCM.")
        return value


class ProdutoEmpresa(ModeloBase):
    __tablename__ = "produtos_empresa"

    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    estoque_atual = db.Column(db.Integer, nullable=False, default=0)
    estoque_minimo = db.Column(db.Integer, nullable=False, default=0)
    valor_compra = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    valor_venda = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    produto = db.relationship("Produto", backref=db.backref("dados_por_empresa", lazy=True, cascade="all, delete-orphan"))
    empresa = db.relationship("Empresa", backref=db.backref("produtos_empresa", lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "produto_id", "empresa_id", name="uq_produto_empresa"),
        CheckConstraint("estoque_atual >= 0", name="ck_produto_empresa_estoque_atual_non_negative"),
        CheckConstraint("estoque_minimo >= 0", name="ck_produto_empresa_estoque_minimo_non_negative"),
        CheckConstraint("valor_compra >= 0", name="ck_produto_empresa_valor_compra_non_negative"),
        CheckConstraint("valor_venda >= 0", name="ck_produto_empresa_valor_venda_non_negative"),
    )


class FormaPagamento(ModeloBase):
    __tablename__ = "formas_pagamento"

    nome = db.Column(db.String(80), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", name="uq_forma_pagamento_tenant_nome"),
    )


class CategoriaFinanceira(ModeloBase):
    __tablename__ = "categorias_financeiras"

    nome = db.Column(db.String(100), nullable=False)
    tipo_categoria = db.Column(db.Enum(TipoCategoriaFinanceira), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", "tipo_categoria", name="uq_categoria_financeira_tenant_nome_tipo"),
    )


class TipoOperacao(ModeloBase):
    __tablename__ = "tipos_operacao"

    nome = db.Column(db.String(80), nullable=False)
    codigo = db.Column(db.String(30), nullable=False)
    tipo_operacao = db.Column(db.Enum(TipoOperacaoEnum), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_tipo_operacao_tenant_codigo"),
        UniqueConstraint("tenant_id", "nome", name="uq_tipo_operacao_tenant_nome"),
    )


class Cupom(ModeloBase):
    __tablename__ = "cupons"

    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(60), nullable=False)
    data_validade = db.Column(db.Date, nullable=False)
    tipo_desconto = db.Column(db.Enum(TipoDesconto), nullable=False)
    valor_desconto = db.Column(db.Numeric(12, 2), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_cupom_tenant_codigo"),
    )


class MovimentoEstoque(ModeloBase):
    __tablename__ = "movimentos_estoque"

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=True)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=True)
    tipo_movimento = db.Column(db.Enum(TipoMovimentoEstoque), nullable=False)
    motivo = db.Column(db.Enum(MotivoMovimentoEstoque), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Numeric(12, 2), nullable=True)
    valor_total = db.Column(db.Numeric(12, 2), nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    data_movimento = db.Column(db.DateTime, nullable=False, default=TimeService.now_utc_naive)

    empresa = db.relationship("Empresa", backref=db.backref("movimentos_estoque", lazy=True))
    produto = db.relationship("Produto", backref=db.backref("movimentos_estoque", lazy=True))
    funcionario = db.relationship("Funcionario", backref=db.backref("movimentos_estoque", lazy=True))
    venda = db.relationship("Venda", backref=db.backref("movimentos_estoque", lazy=True))

    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_movimento_estoque_quantidade_positive"),
        CheckConstraint("valor_unitario IS NULL OR valor_unitario >= 0", name="ck_movimento_estoque_valor_unitario_non_negative"),
        CheckConstraint("valor_total IS NULL OR valor_total >= 0", name="ck_movimento_estoque_valor_total_non_negative"),
        Index("ix_mov_estoque_tenant_empresa_produto", "tenant_id", "empresa_id", "produto_id"),
    )


class Venda(ModeloBase):
    __tablename__ = "vendas"

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=True)
    tipo_operacao_id = db.Column(db.Integer, db.ForeignKey("tipos_operacao.id"), nullable=False)
    cupom_id = db.Column(db.Integer, db.ForeignKey("cupons.id"), nullable=True)
    numero_unico = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Enum(StatusVenda), nullable=False, default=StatusVenda.ABERTA)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    desconto = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    data_venda = db.Column(db.DateTime, nullable=False, default=TimeService.now_utc_naive)
    observacao = db.Column(db.Text, nullable=True)

    empresa = db.relationship("Empresa", backref=db.backref("vendas", lazy=True))
    funcionario = db.relationship("Funcionario", backref=db.backref("vendas", lazy=True))
    tipo_operacao = db.relationship("TipoOperacao", backref=db.backref("vendas", lazy=True))
    cupom = db.relationship("Cupom", backref=db.backref("vendas", lazy=True))

    __table_args__ = (
        UniqueConstraint("tenant_id", "empresa_id", "numero_unico", name="uq_venda_tenant_empresa_numero_unico"),
        CheckConstraint("subtotal >= 0", name="ck_venda_subtotal_non_negative"),
        CheckConstraint("desconto >= 0", name="ck_venda_desconto_non_negative"),
        CheckConstraint("total >= 0", name="ck_venda_total_non_negative"),
        Index("ix_venda_tenant_empresa_data", "tenant_id", "empresa_id", "data_venda"),
    )


class ItemVenda(ModeloBase):
    __tablename__ = "itens_venda"

    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    valor_total = db.Column(db.Numeric(12, 2), nullable=False)

    venda = db.relationship("Venda", backref=db.backref("itens", lazy=True, cascade="all, delete-orphan"))
    produto = db.relationship("Produto", backref=db.backref("itens_venda", lazy=True))

    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_item_venda_quantidade_positive"),
        CheckConstraint("valor_unitario >= 0", name="ck_item_venda_valor_unitario_non_negative"),
        CheckConstraint("valor_total >= 0", name="ck_item_venda_valor_total_non_negative"),
    )


class PagamentoVenda(ModeloBase):
    __tablename__ = "pagamentos_venda"

    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=False)
    forma_pagamento_id = db.Column(db.Integer, db.ForeignKey("formas_pagamento.id"), nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    comprovante = db.Column(db.String(120), nullable=True)

    venda = db.relationship("Venda", backref=db.backref("pagamentos", lazy=True, cascade="all, delete-orphan"))
    forma_pagamento = db.relationship("FormaPagamento", backref=db.backref("pagamentos_venda", lazy=True))

    __table_args__ = (
        CheckConstraint("valor >= 0", name="ck_pagamento_venda_valor_non_negative"),
    )


class LancamentoFinanceiro(ModeloBase):
    __tablename__ = "lancamentos_financeiros"

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias_financeiras.id"), nullable=False)
    forma_pagamento_id = db.Column(db.Integer, db.ForeignKey("formas_pagamento.id"), nullable=False)
    venda_id = db.Column(db.Integer, db.ForeignKey("vendas.id"), nullable=True)
    tipo = db.Column(db.Enum(TipoFinanceiro), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    data_lancamento = db.Column(db.DateTime, nullable=False, default=TimeService.now_utc_naive)
    data_competencia = db.Column(db.Date, nullable=True)
    observacao = db.Column(db.Text, nullable=True)

    empresa = db.relationship("Empresa", backref=db.backref("lancamentos_financeiros", lazy=True))
    funcionario = db.relationship("Funcionario", backref=db.backref("lancamentos_financeiros", lazy=True))
    categoria = db.relationship("CategoriaFinanceira", backref=db.backref("lancamentos_financeiros", lazy=True))
    forma_pagamento = db.relationship("FormaPagamento", backref=db.backref("lancamentos_financeiros", lazy=True))
    venda = db.relationship("Venda", backref=db.backref("lancamentos_financeiros", lazy=True))

    __table_args__ = (
        CheckConstraint("valor >= 0", name="ck_lancamento_financeiro_valor_non_negative"),
        Index("ix_financeiro_tenant_empresa_data", "tenant_id", "empresa_id", "data_lancamento"),
    )


class FechamentoCaixa(ModeloBase):
    __tablename__ = "fechamentos_caixa"

    empresa_id = db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey("funcionarios.id"), nullable=False)
    data_fechamento = db.Column(db.Date, nullable=False)
    valor_inicial = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    valor_final = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    observacao = db.Column(db.Text, nullable=True)

    empresa = db.relationship("Empresa", backref=db.backref("fechamentos_caixa", lazy=True))
    funcionario = db.relationship("Funcionario", backref=db.backref("fechamentos_caixa", lazy=True))

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "empresa_id",
            "funcionario_id",
            "data_fechamento",
            name="uq_fechamento_caixa_tenant_empresa_funcionario_data"
        ),
    )
