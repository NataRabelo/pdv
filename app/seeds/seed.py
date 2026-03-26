from app.extensions import db
from app.models.db import (
    Tenant,
    Empresa,
    Funcionario,
    FuncionarioEmpresa,
    TipoEmpresa
)
from app.security.password import hash_password


def run_seed():
    print("Iniciando seed...")

    # =========================
    # TENANT / MARCA
    # =========================
    tenant_nome = "BlueOcean"

    tenant = Tenant.query.filter_by(nome=tenant_nome).first()

    if not tenant:
        tenant = Tenant(nome=tenant_nome)
        db.session.add(tenant)
        db.session.commit()
        print("Tenant criado")
    else:
        print("Tenant já existe")

    # =========================
    # EMPRESAS / LOJAS
    # =========================
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
            print(f"Empresa já existe: {empresa.nome_fantasia}")

        empresas_criadas.append(empresa)

    # =========================
    # FUNCIONÁRIO ADMIN
    # =========================
    usuario_admin = "admin"

    funcionario = Funcionario.query.filter_by(
        tenant_id=tenant.id,
        usuario=usuario_admin
    ).first()

    if not funcionario:
        funcionario = Funcionario(
            tenant_id=tenant.id,
            nome="Administrador",
            cpf="123.456.789-00",
            usuario=usuario_admin,
            senha_hash=hash_password("123456"),
            ativo=True
        )
        db.session.add(funcionario)
        db.session.commit()

        print("Funcionário admin criado")
        print("Usuário: admin")
        print("Senha: 123456")
    else:
        print("Funcionário admin já existe")

    # =========================
    # VÍNCULO FUNCIONÁRIO x EMPRESAS
    # =========================
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
            print(f"Vínculo criado: admin -> {empresa.nome_fantasia}")
        else:
            print(f"Vínculo já existe: admin -> {empresa.nome_fantasia}")

    print("Seed finalizada com sucesso")