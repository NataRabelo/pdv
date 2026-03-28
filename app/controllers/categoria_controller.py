from flask import Blueprint, render_template, url_for, redirect, request, flash
from app.services.categoria_service import CategoriaService
from flask_jwt_extended import jwt_required

categoria_bp = Blueprint("categoria", __name__)

# CADASTRAR 
@categoria_bp.route("/cadastrar-categoria", methods=['GET', 'POST'])
@jwt_required()
def cadastrar():
    try:
        if request.method == 'POST':
            categoria = CategoriaService.cadastrar(request.form)
            flash(f'categoria {categoria.nome} cadastrado', 'success')
            return redirect(url_for('estoque.categoria'))
        
    except Exception as e:
        flash('Error ao tentar cadastrar um categoria: ' + str(e))
        return redirect(url_for('estoque.categoria'))
    
# ATUALIZAR
@categoria_bp.route("/editar-categoria/<int:id>", methods=['GET', 'POST'])
def editar(id):
    try:
        if request.method == 'POST':
            categoria = CategoriaService.atualizar(request.form, id)
            flash(f'Categoria: {categoria.nome} atualizada', 'success')
            return redirect(url_for('estoque.categoria'))
    
    except Exception as e:
        flash(f'Erro ao editar a categoria: ' + str(e), 'warning')
        return redirect(url_for('estoque.categoria'))

# DELETAR 
@categoria_bp.route('/deletar-categoria/<int:id>', methods=['POST'])
def deletar(id):
    try: 
        if request.method == 'POST':
            CategoriaService.deletar(id)
            flash('Categoria deletada com sucesso', 'success')
            return redirect(url_for('estoque.categoria'))
        
    except Exception as e:
        flash('Erro ao deletar a categoria: ' + str(e), 'warning')
        return redirect(url_for('estoque.categoria'))