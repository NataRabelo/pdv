from decimal import Decimal, InvalidOperation

from app.models.db import Produto, ProdutoEmpresa
from app.repositorys.produto_repository import ProdutoRepository


class ProdutoService:

    @staticmethod
    def listar(tenant_id):
        return ProdutoRepository.listar(tenant_id)

    @staticmethod
    def listar_categorias(tenant_id):
        return ProdutoRepository.listar_categorias(tenant_id)

    @staticmethod
    def listar_empresas(tenant_id):
        return ProdutoRepository.listar_empresas(tenant_id)

    @staticmethod
    def criar(data, tenant_id, funcionario_id=None):
        nome = (data.get("nome") or "").strip()
        descricao = (data.get("descricao") or "").strip() or None
        categoria_id = data.get("categoria_id")
        empresa_id = data.get("empresa_id")
        codigo_barras = (data.get("codigo_barras") or "").strip() or None
        possui_ncm = bool(data.get("possui_ncm"))
        ncm = (data.get("ncm") or "").strip() or None
        estoque_minimo = ProdutoService._to_decimal(data.get("estoque_minimo", 0), "estoque mínimo", 3)
        valor_compra = ProdutoService._to_decimal(data.get("valor_compra", 0), "valor de compra", 2)
        valor_venda = ProdutoService._to_decimal(data.get("valor_venda", 0), "valor de venda", 2)
        ativo = ProdutoService._to_bool(data.get("ativo", True))

        if not nome:
            raise ValueError("Nome do produto é obrigatório.")

        if not empresa_id:
            raise ValueError("Empresa é obrigatória.")

        empresa = ProdutoRepository.buscar_empresa_por_id(empresa_id, tenant_id)
        if not empresa:
            raise ValueError("Empresa não encontrada.")

        categoria = None
        if categoria_id:
            categoria = ProdutoRepository.buscar_categoria_por_id(categoria_id, tenant_id)
            if not categoria:
                raise ValueError("Categoria não encontrada.")

        if ProdutoRepository.buscar_produto_por_nome(nome, tenant_id):
            raise ValueError("Já existe um produto com esse nome.")

        if codigo_barras and ProdutoRepository.buscar_produto_por_codigo_barras(codigo_barras, tenant_id):
            raise ValueError("Já existe um produto com esse código de barras.")

        if possui_ncm and not ncm:
            raise ValueError("Informe o NCM quando 'possui NCM' estiver marcado.")

        produto = Produto(
            tenant_id=tenant_id,
            categoria_id=categoria.id if categoria else None,
            criado_por_funcionario_id=funcionario_id,
            nome=nome,
            descricao=descricao,
            possui_ncm=possui_ncm,
            ncm=ncm,
            codigo_barras=codigo_barras,
            ativo=ativo
        )
        ProdutoRepository.adicionar(produto)
        ProdutoRepository.salvar()

        produto_empresa = ProdutoEmpresa(
            tenant_id=tenant_id,
            produto_id=produto.id,
            empresa_id=empresa.id,
            estoque_atual=Decimal("0"),
            estoque_minimo=estoque_minimo,
            valor_compra=valor_compra,
            valor_venda=valor_venda,
            ativo=ativo
        )
        ProdutoRepository.adicionar(produto_empresa)
        ProdutoRepository.salvar()

        return ProdutoRepository.buscar_produto_empresa_por_id(produto_empresa.id, tenant_id)

    @staticmethod
    def atualizar(produto_empresa_id, data, tenant_id):
        produto_empresa = ProdutoRepository.buscar_produto_empresa_por_id(produto_empresa_id, tenant_id)
        if not produto_empresa:
            raise ValueError("Produto não encontrado.")

        produto = produto_empresa.produto

        nome = (data.get("nome") or "").strip()
        descricao = (data.get("descricao") or "").strip() or None
        categoria_id = data.get("categoria_id")
        empresa_id = data.get("empresa_id")
        codigo_barras = (data.get("codigo_barras") or "").strip() or None
        possui_ncm = ProdutoService._to_bool(data.get("possui_ncm", False))
        ncm = (data.get("ncm") or "").strip() or None
        estoque_minimo = ProdutoService._to_decimal(data.get("estoque_minimo", 0), "estoque mínimo", 3)
        valor_compra = ProdutoService._to_decimal(data.get("valor_compra", 0), "valor de compra", 2)
        valor_venda = ProdutoService._to_decimal(data.get("valor_venda", 0), "valor de venda", 2)
        ativo = ProdutoService._to_bool(data.get("ativo", True))

        if not nome:
            raise ValueError("Nome do produto é obrigatório.")

        if not empresa_id:
            raise ValueError("Empresa é obrigatória.")

        empresa = ProdutoRepository.buscar_empresa_por_id(empresa_id, tenant_id)
        if not empresa:
            raise ValueError("Empresa não encontrada.")

        categoria = None
        if categoria_id:
            categoria = ProdutoRepository.buscar_categoria_por_id(categoria_id, tenant_id)
            if not categoria:
                raise ValueError("Categoria não encontrada.")

        produto_existente = ProdutoRepository.buscar_produto_por_nome(
            nome,
            tenant_id,
            ignorar_produto_id=produto.id
        )
        if produto_existente:
            raise ValueError("Já existe um produto com esse nome.")

        codigo_existente = ProdutoRepository.buscar_produto_por_codigo_barras(
            codigo_barras,
            tenant_id,
            ignorar_produto_id=produto.id
        )
        if codigo_existente:
            raise ValueError("Já existe um produto com esse código de barras.")

        if possui_ncm and not ncm:
            raise ValueError("Informe o NCM quando 'possui NCM' estiver marcado.")

        if ProdutoRepository.existe_produto_empresa(
            produto.id,
            empresa.id,
            tenant_id,
            ignorar_produto_empresa_id=produto_empresa.id
        ):
            raise ValueError("Esse produto já está vinculado a essa empresa.")

        produto.nome = nome
        produto.descricao = descricao
        produto.categoria_id = categoria.id if categoria else None
        produto.codigo_barras = codigo_barras
        produto.possui_ncm = possui_ncm
        produto.ncm = ncm
        produto.ativo = ativo

        produto_empresa.empresa_id = empresa.id
        produto_empresa.estoque_minimo = estoque_minimo
        produto_empresa.valor_compra = valor_compra
        produto_empresa.valor_venda = valor_venda
        produto_empresa.ativo = ativo

        ProdutoRepository.salvar()

        return ProdutoRepository.buscar_produto_empresa_por_id(produto_empresa.id, tenant_id)

    @staticmethod
    def deletar(produto_empresa_id, tenant_id):
        produto_empresa = ProdutoRepository.buscar_produto_empresa_por_id(produto_empresa_id, tenant_id)
        if not produto_empresa:
            raise ValueError("Produto não encontrado.")

        produto_id = produto_empresa.produto_id
        produto = produto_empresa.produto

        ProdutoRepository.deletar(produto_empresa)
        ProdutoRepository.salvar()

        total_vinculos = ProdutoRepository.contar_vinculos_produto(produto_id, tenant_id)
        if total_vinculos == 0:
            ProdutoRepository.deletar(produto)
            ProdutoRepository.salvar()

    @staticmethod
    def _to_decimal(value, field_name, casas=2):
        if value in (None, ""):
            value = 0

        try:
            valor = Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            raise ValueError(f"Valor inválido para {field_name}.")

        if valor < 0:
            raise ValueError(f"{field_name.capitalize()} não pode ser negativo.")

        quant = "0." + ("0" * (casas - 1)) + "1" if casas > 0 else "1"
        return valor.quantize(Decimal(quant))

    @staticmethod
    def _to_bool(value):
        if isinstance(value, bool):
            return value

        if value in [1, "1", "true", "True", "on", "ON", "sim", "SIM"]:
            return True

        return False