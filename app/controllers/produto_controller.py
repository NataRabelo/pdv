from flask import Blueprint, render_template, url_for, redirect, request, flash
from app.services.produto_service import ProdutoService
from flask_jwt_extended import jwt_required

produto_bp = Blueprint("produto", __name__)

produto_bp.route("/cadastrar-produto", methods=['GET', 'POST'])
@jwt_required()
def cadastrar_produto():
    try:
        if request.method == 'POST':
            produto = ProdutoService.cadastrar(request.form)
            flash(f'Produto {produto.nome} cadastrado', 'success')
            return redirect(url_for('main.estoque_home'))
        else:
            return render_template('produto/cadastrar.html')
    except Exception as e:
        flash('Error ao tentar cadastrar um produto: ' + str(e))
        return render_template('main.estoque_home')
    
