DEFAULT_PERMISSION_DEFINITIONS = [
    {"codigo": "visualizar_funcionario", "nome": "Visualizar funcionarios"},
    {"codigo": "criar_funcionario", "nome": "Criar funcionarios"},
    {"codigo": "editar_funcionario", "nome": "Editar funcionarios"},
    {"codigo": "excluir_funcionario", "nome": "Excluir funcionarios"},
    {"codigo": "visualizar_categoria", "nome": "Visualizar categorias"},
    {"codigo": "criar_categoria", "nome": "Criar categorias"},
    {"codigo": "editar_categoria", "nome": "Editar categorias"},
    {"codigo": "excluir_categoria", "nome": "Excluir categorias"},
    {"codigo": "visualizar_produto", "nome": "Visualizar produtos"},
    {"codigo": "criar_produto", "nome": "Criar produtos"},
    {"codigo": "editar_produto", "nome": "Editar produtos"},
    {"codigo": "excluir_produto", "nome": "Excluir produtos"},
    {"codigo": "visualizar_role", "nome": "Visualizar roles"},
    {"codigo": "criar_role", "nome": "Criar roles"},
    {"codigo": "editar_role", "nome": "Editar roles"},
    {"codigo": "excluir_role", "nome": "Excluir roles"},
    {"codigo": "visualizar_permission", "nome": "Visualizar permissions"},
    {"codigo": "criar_permission", "nome": "Criar permissions"},
    {"codigo": "editar_permission", "nome": "Editar permissions"},
    {"codigo": "excluir_permission", "nome": "Excluir permissions"},
    {"codigo": "visualizar_pdv", "nome": "Visualizar PDV"},
    {"codigo": "registrar_venda", "nome": "Registrar vendas"},
    {"codigo": "cancelar_venda", "nome": "Cancelar vendas"},
    {"codigo": "visualizar_financeiro", "nome": "Visualizar financeiro"},
    {"codigo": "criar_lancamento_financeiro", "nome": "Criar lancamentos financeiros"},
    {"codigo": "fechar_caixa", "nome": "Fechar caixa"},
    {"codigo": "visualizar_todas_empresas", "nome": "Visualizar dados de todas as empresas"},
]


DEFAULT_ROLE_DEFINITIONS = [
    {
        "codigo": "administrador",
        "nome": "Administrador",
        "descricao": "Acesso completo ao sistema.",
        "permissoes": [item["codigo"] for item in DEFAULT_PERMISSION_DEFINITIONS],
    },
    {
        "codigo": "operador",
        "nome": "Operador",
        "descricao": "Opera estoque e catalogo sem gerenciar usuarios.",
        "permissoes": [
            "visualizar_categoria",
            "criar_categoria",
            "editar_categoria",
            "excluir_categoria",
            "visualizar_produto",
            "criar_produto",
            "editar_produto",
            "excluir_produto",
            "visualizar_pdv",
            "registrar_venda",
            "visualizar_financeiro",
            "criar_lancamento_financeiro",
            "fechar_caixa",
        ],
    },
]


ADMIN_ROLE_CODE = "administrador"
VISUALIZAR_TODAS_EMPRESAS = "visualizar_todas_empresas"
