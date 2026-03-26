from flask_jwt_extended import jwt_required
from flask import Blueprint, render_template, redirect, request, url_for, flash

main_bp = Blueprint('main', __name__)

# ROTA HOME SISTEMA
@main_bp.route('/home', methods=['GET'])
def home():
    try:
        return render_template('pages/home.html')
    
    except Exception as e:
        flash('Erro ao redirecionar para a home: ' + str(e), 'warning')
        return redirect(url_for('auth.login'))

# ROTA HOME PDV
@main_bp.route('/pdv/home', methods=['GET'])
def pdv_home():
    try:
        return render_template('pages/home_pdv.html')
    
    except Exception as e:
        flash('Erro ao redirecionar para o pdv: ' + str(e), 'warning')
        return redirect(url_for('main.home'))
    
# ROTA HOME ESTOQUE
@main_bp.route('/estoque/home', methods=['GET'])
def estoque_home():
    try:
        return render_template('pages/home_estoque.html')
    
    except Exception as e:
        flash('Erro ao redirecionar para o estoque: ' + str(e), 'warning')
        return redirect(url_for('main.home'))
    
# ROTA HOME FINANCEIRO
@main_bp.route('/financeiro/home', methods=['GET'])
def financeiro_home():
    try:
        return render_template('pages/home_financeiro.html')
    
    except Exception as e:
        flash('Erro ao redirecionar para o financeiro: ' + str(e), 'warning')
        return redirect(url_for('main.home'))