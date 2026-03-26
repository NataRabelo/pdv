from app.repositorys.produto_repository import ProdutoRepository
from app.utils.helpers import parse_float, _to_int_or_none
from flask_jwt_extended import get_jwt_identity
from app.models.db import Produto

class ProdutoService():

    @staticmethod
    def cadastrar(data: dict):

        nome            = data.get('nome')
        descricao       = data.get('descricao')
        quantidade      = data.get('quantidade')
        possui_ncm      = data.get('possui_ncm')
        ncm             = data.get('ncm')
        codigo_barras   = data.get('codigo_barras')
        data_validade   = data.get('data_validade')

        valor_compra    = parse_float(data.get('valor_compra'))
        valor_venda     = parse_float(data.get('valor_venda'))

        funcionario     = get_jwt_identity()
        categoria       = _to_int_or_none(data.get('categoria'))

        v_nome = ProdutoRepository.get_by_nome(nome)
        if v_nome:
            raise ValueError('produto já cadastrado com o mesmo nome')
        if ncm:
            v_ncm = ProdutoRepository.get_by_ncm(ncm)
            if v_ncm:
                raise ValueError('Produto já cadastrado com o mesmo NCM')

        if not nome:
            raise ValueError("Produto sem nome")
        if not descricao:
            raise ValueError('Produto sem descrição')
        if not quantidade or quantidade <= 0:
            raise ValueError('Produto com quantidade zerada')
        if not valor_venda:
            raise ValueError('Produto sem valor de venda')
        
        produto = Produto(
            nome            = nome,
            descricao       = descricao,
            quantidade      = quantidade,
            possui_ncm      = possui_ncm,
            ncm             = ncm,
            codigo_barras   = codigo_barras,
            data_validade   =  data_validade,
            valor_compra    = valor_compra,
            valor_venda     = valor_venda,
            funcionario     = funcionario,
            categoria       = categoria 
        )

        produto = ProdutoRepository.create(produto)

        return produto 