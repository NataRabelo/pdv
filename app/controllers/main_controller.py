from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, send_from_directory, url_for
from flask_jwt_extended import jwt_required

from app.security.decorators import ui_permission_required
from app.security.jwt import get_auth_scope

main_bp = Blueprint("main", __name__)


def _obter_diretorio_favicon():
    return Path(current_app.static_folder) / "favicon"


def _servir_arquivo_favicon(nome_arquivo, fallback=None):
    diretorio = _obter_diretorio_favicon()
    arquivo = diretorio / nome_arquivo
    if arquivo.exists():
        return send_from_directory(diretorio, nome_arquivo)

    if fallback:
        arquivo_fallback = diretorio / fallback
        if arquivo_fallback.exists():
            return send_from_directory(diretorio, fallback)

    return "", 204


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


@main_bp.route("/favicon.ico", methods=["GET"])
def favicon():
    return _servir_arquivo_favicon("favicon.ico", fallback="favicon.svg")


@main_bp.route("/site.webmanifest", methods=["GET"])
def site_webmanifest():
    return _servir_arquivo_favicon("site.webmanifest")


@main_bp.route("/browserconfig.xml", methods=["GET"])
def browserconfig():
    return _servir_arquivo_favicon("browserconfig.xml")


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
