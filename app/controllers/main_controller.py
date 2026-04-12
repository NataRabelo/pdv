from flask import Blueprint, flash, redirect, render_template, url_for
from flask_jwt_extended import jwt_required

from app.security.decorators import ui_permission_required
from app.security.jwt import get_auth_scope

main_bp = Blueprint("main", __name__)


def _redirecionar_platform_owner():
    if get_auth_scope() == "platform":
        flash("Esse ambiente pertence ao tenant. Use o painel da plataforma.", "warning")
        return redirect(url_for("platform.home"))
    return None


@main_bp.route("/", methods=["GET"])
def index():
    try:
        return redirect(url_for("auth.login"))
    except Exception as e:
        flash("Erro ao redirecionar para a tela de login: " + str(e), "warning")
        return 404


@main_bp.route("/home", methods=["GET"])
@jwt_required()
def home():
    try:
        if get_auth_scope() == "platform":
            return redirect(url_for("platform.home"))

        return render_template("pages/home.html")

    except Exception as e:
        flash("Erro ao redirecionar para a home: " + str(e), "warning")
        return redirect(url_for("auth.login"))


@main_bp.route("/pdv/home", methods=["GET"])
@jwt_required()
@ui_permission_required("visualizar_pdv")
def pdv_home():
    try:
        redirect_response = _redirecionar_platform_owner()
        if redirect_response:
            return redirect_response

        return render_template("pages/home_pdv.html")

    except Exception as e:
        flash("Erro ao redirecionar para o pdv: " + str(e), "warning")
        return redirect(url_for("main.home"))


@main_bp.route("/estoque/home", methods=["GET"])
@jwt_required()
@ui_permission_required("visualizar_produto")
def estoque_home():
    try:
        redirect_response = _redirecionar_platform_owner()
        if redirect_response:
            return redirect_response

        return render_template("pages/home_estoque.html")

    except Exception as e:
        flash("Erro ao redirecionar para o estoque: " + str(e), "warning")
        return redirect(url_for("main.home"))


@main_bp.route("/financeiro/home", methods=["GET"])
@jwt_required()
@ui_permission_required("visualizar_financeiro")
def financeiro_home():
    try:
        redirect_response = _redirecionar_platform_owner()
        if redirect_response:
            return redirect_response

        return render_template("pages/home_financeiro.html")

    except Exception as e:
        flash("Erro ao redirecionar para o financeiro: " + str(e), "warning")
        return redirect(url_for("main.home"))
