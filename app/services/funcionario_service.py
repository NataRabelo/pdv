from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.models.db import Funcionario, FuncionarioEmpresa
from app.repositorys.funcionario_repository import FuncionarioRepository
from app.security.password import generate_password_hash

class FuncionarioService:

    @staticmethod
    def listar(tenant_id):
        return FuncionarioRepository.listar_por_tenant(tenant_id)
    
    @staticmethod
    def criar(data, tenant_id):

        senha_hash = generate_password_hash(data.get("senha"))

        nome = (data.get("nome") or "").strip
        cpf = (data.get("cpf") or "").strip
        usuario = (data.get("usuario") or "").strip
        senha = generate_password_hash((data.get("senha")) or "").strip
        empresa_id = (data.get("empresa") or "").strip
        ativo = FuncionarioService._to_bool(data.get("ativo", True))

        if not nome:
            raise ValueError("Nome do funcionário é obrigatório")
        
        if not usuario:
            raise ValueError("Usuário é obrigatório")
        
        if not cpf:
            raise ValueError("CPF é obrigatório")
        
        cpf_duplicado = FuncionarioRepository.buscar_cpf_duplicado(cpf, empresa_id, tenant_id)
        if cpf_duplicado:
            raise ValueError("CPF já cadastrado no sistema")

        usuario_duplicado = FuncionarioRepository.buscar_funcionario_duplicado(usuario, empresa_id, tenant_id)
        if usuario_duplicado:
            raise ValueError("Nome de usuário já cadastrado no sistema")
        
        empresa = FuncionarioRepository.buscar_empresa_por_id(empresa_id, tenant_id)
        if not empresa:
            raise ValueError("Empresa não encontrada")
        
        funcionario = Funcionario(
            tenant_id = tenant_id,
            nome = nome,
            cpf = cpf,
            usuario = usuario,
            senha_hash = senha,
            ativo = ativo
        )
        FuncionarioRepository.adicionar(funcionario)
        FuncionarioRepository.salvar()

        funcionario_empresa = FuncionarioEmpresa(
            tenant_id = tenant_id,
            funcionario_id = funcionario.id,
            empresa_id = empresa.id
        )
        FuncionarioRepository.adicionar(funcionario_empresa)
        FuncionarioRepository.salvar()

        return FuncionarioRepository.buscar_funcionario_empresa_por_id(funcionario_empresa.id, tenant_id)
    
    @staticmethod
    def atualizar(funcionario_empresa_id, data, tenant_id):
        funcionario_empresa = FuncionarioRepository.buscar_funcionario_empresa_por_id(funcionario_empresa_id, tenant_id)
        if not funcionario_empresa:
            raise ValueError("Funcionário não encontrado")
        
        funcionario = funcionario_empresa.funcionario

        nome = (data.get("nome") or "").strip()
        cpf = (data.get("cpf") or "").strip()
        usuario  = (data.get("usuario") or "").strip()
        senha_hash = generate_password_hash((data.get("senha") or "").strip())
        ativo = FuncionarioService._to_bool(data.get("ativo"), True)
        empresa_id = (data.get("empresa") or "").strip

        if not nome:
            raise ValueError("Nome do funcionário é obrigatório")
        
        if not usuario:
            raise ValueError("Usuário é obrigatório")
        
        if not cpf:
            raise ValueError("CPF é obrigatório")
        
        cpf_duplicado = FuncionarioRepository.buscar_cpf_duplicado(cpf, empresa_id, tenant_id)
        if cpf_duplicado:
            raise ValueError("CPF já cadastrado no sistema")

        usuario_duplicado = FuncionarioRepository.buscar_funcionario_duplicado(usuario, empresa_id, tenant_id)
        if usuario_duplicado:
            raise ValueError("Nome de usuário já cadastrado no sistema")
        
        empresa = FuncionarioRepository.buscar_empresa_por_id(empresa_id, tenant_id)
        if not empresa:
            raise ValueError("Empresa não encontrada")
        
        funcionario.nome = nome
        funcionario.cpf = cpf
        funcionario.usuario = usuario
        funcionario.senha_hash = senha_hash
        funcionario.ativo = ativo
        
        funcionario_empresa.empresa_id = empresa_id

        FuncionarioRepository.salvar()

        return FuncionarioRepository.buscar_funcionario_empresa_por_id(funcionario_empresa.id, tenant_id)
    
    @staticmethod
    def deletar(funcionario_empresa_id, tenant_id):
        funcionario_empresa = FuncionarioRepository.buscar_funcionario_empresa_por_id(funcionario_empresa_id, tenant_id)
        if not funcionario_empresa:
            raise ValueError("Funcionário não encontrado")
        
        funcionario_id = funcionario_empresa.funcionario_id
        funcionario = funcionario_empresa.funcionario

        FuncionarioRepository.deletar(funcionario_empresa)
        FuncionarioRepository.salvar()

        total_vinculos = FuncionarioRepository.contar_vinculos_funcionario(funcionario_id, tenant_id)
        if total_vinculos == 0:
            FuncionarioRepository.deletar(funcionario)
            FuncionarioRepository.salavar()

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