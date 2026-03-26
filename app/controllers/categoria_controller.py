from flask import Blueprint, render_template, url_for, redirect, request, flash
from app.services.categoria_service import CategoriaService
from flask_jwt_extended import jwt_required

categoria_bp = Blueprint("categoria", __name__)

categoria_bp.route("/cadastrar-categoria", methods=['GET', 'POST'])
@jwt_required()
def cadastrar_categoria():
    try:
        if request.method == 'POST':
            categoria = CategoriaService.cadastrar(request.form)
            flash(f'categoria {categoria.nome} cadastrado', 'success')
            return redirect(url_for('main.estoque_home'))
        else:
            return render_template('categoria/cadastrar.html')
    except Exception as e:
        flash('Error ao tentar cadastrar um categoria: ' + str(e))
        return render_template('main.estoque_home')
    
