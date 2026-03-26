from flask import Blueprint, render_template, url_for, redirect, request, flash
from app.services.categoria_service import CategoriaService
from flask_jwt_extended import jwt_required

estoque_bp = Blueprint("estoque", __name__, url_prefix='/estoque')

@estoque_bp.route("/categorias", methods=['GET'])
@jwt_required()
def categoria():
    try:
        categorias = CategoriaService.listar()
        return render_template(
            "categoria/listar.html", 
            categorias=categorias
            )

    except Exception as e:
        flash('Erro ao acessar as categorias: ' + str(e), 'warning')
        return redirect(url_for('main.home'))