import os
import unittest

from app import create_app
from app.extensions import db
from app.models.db import (
    CategoriaProduto,
    Empresa,
    Funcionario,
    FuncionarioEmpresa,
    LancamentoFinanceiro,
    MovimentoEstoque,
    Produto,
    ProdutoEmpresa,
    StatusVenda,
    Tenant,
    TipoEmpresa,
    TipoFinanceiro,
)
from app.security.password import hash_password
from app.services.acesso_empresa_service import AcessoEmpresaService
from app.services.financeiro_service import FinanceiroService
from app.services.pdv_service import PdvService
from app.services.tenant_bootstrap_service import TenantBootstrapService


class FluxoPdvFinanceiroTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DATABASE_URL"] = "sqlite:///test_fluxo_pdv_financeiro.db"
        cls.app = create_app()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        db.drop_all()
        db.create_all()

        tenant = Tenant(nome="Tenant Teste")
        db.session.add(tenant)
        db.session.commit()

        roles = TenantBootstrapService.garantir_permissoes_e_roles(tenant.id)
        TenantBootstrapService.garantir_cadastros_operacionais(tenant.id)

        empresa = Empresa(
            tenant_id=tenant.id,
            cnpj="12.345.678/0001-00",
            razao_social="Empresa Teste LTDA",
            nome_fantasia="Empresa Teste",
            tipo_empresa=TipoEmpresa.MATRIZ,
            ativo=True,
        )
        db.session.add(empresa)
        db.session.flush()

        funcionario = Funcionario(
            tenant_id=tenant.id,
            role_id=roles["administrador"].id,
            nome="Admin Teste",
            cpf="123.456.789-99",
            usuario="admin_teste",
            senha_hash=hash_password("123456"),
            ativo=True,
        )
        db.session.add(funcionario)
        db.session.flush()

        db.session.add(
            FuncionarioEmpresa(
                tenant_id=tenant.id,
                funcionario_id=funcionario.id,
                empresa_id=empresa.id,
                ativo=True,
            )
        )

        categoria = CategoriaProduto(
            tenant_id=tenant.id,
            nome="Bebidas",
            descricao="Categoria de teste",
            ativo=True,
        )
        db.session.add(categoria)
        db.session.flush()

        produto = Produto(
            tenant_id=tenant.id,
            categoria_id=categoria.id,
            criado_por_funcionario_id=funcionario.id,
            nome="Refrigerante 2L",
            descricao="Produto para fluxo de teste",
            possui_ncm=False,
            codigo_barras="789000000001",
            ativo=True,
        )
        db.session.add(produto)
        db.session.flush()

        produto_empresa = ProdutoEmpresa(
            tenant_id=tenant.id,
            produto_id=produto.id,
            empresa_id=empresa.id,
            estoque_atual=10,
            estoque_minimo=2,
            valor_compra=4.50,
            valor_venda=7.50,
            ativo=True,
        )
        db.session.add(produto_empresa)
        db.session.commit()

        self.tenant = tenant
        self.empresa = empresa
        self.funcionario = funcionario
        self.produto = produto
        self.produto_empresa = produto_empresa
        self.escopo = AcessoEmpresaService.obter_escopo(funcionario.id, tenant.id)

    def test_venda_baixa_estoque_e_gera_financeiro(self):
        payload = {
            "empresa_id": self.empresa.id,
            "itens": [
                {
                    "produto_id": self.produto.id,
                    "quantidade": 2,
                    "valor_unitario": "7.50",
                }
            ],
            "pagamentos": [
                {
                    "forma_pagamento_id": FinanceiroService.listar_auxiliares(self.tenant.id, self.escopo)["formas_pagamento"][0]["id"],
                    "valor": "15.00",
                }
            ],
            "desconto_manual": "0.00",
        }

        venda = PdvService.criar_venda(payload, self.tenant.id, self.escopo, self.funcionario.id)
        produto_empresa = db.session.get(ProdutoEmpresa, self.produto_empresa.id)

        self.assertEqual(venda["status"], StatusVenda.FINALIZADA.value)
        self.assertEqual(produto_empresa.estoque_atual, 8)
        self.assertEqual(venda["total"], "15.00")
        self.assertEqual(LancamentoFinanceiro.query.count(), 1)
        self.assertEqual(MovimentoEstoque.query.count(), 1)

    def test_cancelamento_reverte_estoque_e_financeiro(self):
        venda = PdvService.criar_venda(
            {
                "empresa_id": self.empresa.id,
                "itens": [{"produto_id": self.produto.id, "quantidade": 1, "valor_unitario": "7.50"}],
                "pagamentos": [{
                    "forma_pagamento_id": FinanceiroService.listar_auxiliares(self.tenant.id, self.escopo)["formas_pagamento"][0]["id"],
                    "valor": "7.50",
                }],
                "desconto_manual": "0.00",
            },
            self.tenant.id,
            self.escopo,
            self.funcionario.id,
        )

        cancelada = PdvService.cancelar_venda(
            venda["id"],
            {"motivo": "Cliente desistiu"},
            self.tenant.id,
            self.escopo,
            self.funcionario.id,
        )

        produto_empresa = db.session.get(ProdutoEmpresa, self.produto_empresa.id)
        lancamentos = LancamentoFinanceiro.query.order_by(LancamentoFinanceiro.id.asc()).all()

        self.assertEqual(cancelada["status"], StatusVenda.CANCELADA.value)
        self.assertEqual(produto_empresa.estoque_atual, 10)
        self.assertEqual(MovimentoEstoque.query.count(), 2)
        self.assertEqual(len(lancamentos), 2)
        self.assertEqual(lancamentos[0].tipo, TipoFinanceiro.ENTRADA)
        self.assertEqual(lancamentos[1].tipo, TipoFinanceiro.SAIDA)

    def test_lancamento_manual_e_fechamento(self):
        auxiliares = FinanceiroService.listar_auxiliares(self.tenant.id, self.escopo)
        categoria_saida = auxiliares["categorias"]["SAIDA"][0]["id"]
        forma_pagamento = auxiliares["formas_pagamento"][0]["id"]

        lancamento = FinanceiroService.criar_lancamento_manual(
            {
                "empresa_id": self.empresa.id,
                "tipo": "SAIDA",
                "categoria_id": categoria_saida,
                "forma_pagamento_id": forma_pagamento,
                "descricao": "Compra emergencial",
                "valor": "20.00",
                "observacao": "Teste do financeiro",
            },
            self.tenant.id,
            self.escopo,
            self.funcionario.id,
        )

        fechamento = FinanceiroService.criar_fechamento(
            {
                "empresa_id": self.empresa.id,
                "valor_inicial": "100.00",
                "valor_final": "80.00",
                "observacao": "Fechamento de teste",
            },
            self.tenant.id,
            self.escopo,
            self.funcionario.id,
        )

        self.assertEqual(lancamento["tipo"], "SAIDA")
        self.assertEqual(fechamento["valor_inicial"], "100.00")
        self.assertEqual(fechamento["valor_final"], "80.00")

    def test_busca_produto_por_codigo_barras_no_pdv(self):
        produto = PdvService.buscar_produto_por_codigo_barras(
            tenant_id=self.tenant.id,
            escopo=self.escopo,
            empresa_id=self.empresa.id,
            codigo_barras="789000000001",
        )

        self.assertEqual(produto["id"], self.produto.id)
        self.assertEqual(produto["codigo_barras"], "789000000001")


if __name__ == "__main__":
    unittest.main()
