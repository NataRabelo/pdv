from app.extensions import db
from app.models.db import (
    Empresa,
    Funcionario,
    FuncionarioEmpresa,
    Permission,
    Role,
    RolePermission,
    Tenant,
    TipoEmpresa,
)
from app.security.password import hash_password
from app.security.permissions import DEFAULT_PERMISSION_DEFINITIONS, DEFAULT_ROLE_DEFINITIONS


def _garantir_permissoes_e_roles(tenant_id):
    permissions_by_code = {}

    for definicao in DEFAULT_PERMISSION_DEFINITIONS:
        permission = Permission.query.filter_by(tenant_id=tenant_id, codigo=definicao["codigo"]).first()
        if not permission:
            permission = Permission(
                tenant_id=tenant_id,
                nome=definicao["nome"],
                codigo=definicao["codigo"],
                descricao=definicao.get("descricao"),
                ativo=True
            )
            db.session.add(permission)
            db.session.commit()

        permissions_by_code[permission.codigo] = permission

    roles_por_codigo = {}

    for definicao in DEFAULT_ROLE_DEFINITIONS:
        role = Role.query.filter_by(tenant_id=tenant_id, codigo=definicao["codigo"]).first()
        if not role:
            role = Role(
                tenant_id=tenant_id,
                nome=definicao["nome"],
                codigo=definicao["codigo"],
                descricao=definicao.get("descricao"),
                ativo=True
            )
            db.session.add(role)
            db.session.commit()

        roles_por_codigo[role.codigo] = role

        for permission_code in definicao["permissoes"]:
            permission = permissions_by_code[permission_code]
            vinculo = RolePermission.query.filter_by(
                tenant_id=tenant_id,
                role_id=role.id,
                permission_id=permission.id
            ).first()

            if not vinculo:
                db.session.add(RolePermission(
                    tenant_id=tenant_id,
                    role_id=role.id,
                    permission_id=permission.id
                ))
                db.session.commit()

    return roles_por_codigo


def run_seed():
    print("Iniciando seed...")

    tenant_nome = "BlueOcean"
    tenant = Tenant.query.filter_by(nome=tenant_nome).first()

    if not tenant:
        tenant = Tenant(nome=tenant_nome)
        db.session.add(tenant)
        db.session.commit()
        print("Tenant criado")
    else:
        print("Tenant ja existe")

    roles_por_codigo = _garantir_permissoes_e_roles(tenant.id)

    empresas_seed = [
        {
            "cnpj": "12.345.678/0001-99",
            "razao_social": "BlueOcean Matriz LTDA",
            "nome_fantasia": "BlueOcean Matriz",
            "tipo_empresa": TipoEmpresa.MATRIZ,
        },
        {
            "cnpj": "12.345.678/0002-70",
            "razao_social": "BlueOcean Filial Centro LTDA",
            "nome_fantasia": "BlueOcean Centro",
            "tipo_empresa": TipoEmpresa.FILIAL,
        },
        {
            "cnpj": "12.345.678/0003-50",
            "razao_social": "BlueOcean Filial Shopping LTDA",
            "nome_fantasia": "BlueOcean Shopping",
            "tipo_empresa": TipoEmpresa.FILIAL,
        },
    ]

    empresas_criadas = []

    for dados_empresa in empresas_seed:
        empresa = Empresa.query.filter_by(
            tenant_id=tenant.id,
            cnpj=dados_empresa["cnpj"]
        ).first()

        if not empresa:
            empresa = Empresa(
                tenant_id=tenant.id,
                cnpj=dados_empresa["cnpj"],
                razao_social=dados_empresa["razao_social"],
                nome_fantasia=dados_empresa["nome_fantasia"],
                tipo_empresa=dados_empresa["tipo_empresa"],
                ativo=True
            )
            db.session.add(empresa)
            db.session.commit()
            print(f"Empresa criada: {empresa.nome_fantasia}")
        else:
            print(f"Empresa ja existe: {empresa.nome_fantasia}")

        empresas_criadas.append(empresa)

    usuario_admin = "admin"
    role_admin = roles_por_codigo["administrador"]

    funcionario = Funcionario.query.filter_by(
        tenant_id=tenant.id,
        usuario=usuario_admin
    ).first()

    if not funcionario:
        funcionario = Funcionario(
            tenant_id=tenant.id,
            role_id=role_admin.id,
            nome="Administrador",
            cpf="123.456.789-00",
            usuario=usuario_admin,
            senha_hash=hash_password("123456"),
            ativo=True
        )
        db.session.add(funcionario)
        db.session.commit()

        print("Funcionario admin criado")
        print("Usuario: admin")
        print("Senha: 123456")
    else:
        if funcionario.role_id != role_admin.id:
            funcionario.role_id = role_admin.id
            db.session.commit()
        print("Funcionario admin ja existe")

    for empresa in empresas_criadas:
        vinculo = FuncionarioEmpresa.query.filter_by(
            tenant_id=tenant.id,
            funcionario_id=funcionario.id,
            empresa_id=empresa.id
        ).first()

        if not vinculo:
            vinculo = FuncionarioEmpresa(
                tenant_id=tenant.id,
                funcionario_id=funcionario.id,
                empresa_id=empresa.id,
                ativo=True
            )
            db.session.add(vinculo)
            db.session.commit()
            print(f"Vinculo criado: admin -> {empresa.nome_fantasia}")
        else:
            print(f"Vinculo ja existe: admin -> {empresa.nome_fantasia}")

    print("Seed finalizada com sucesso")
