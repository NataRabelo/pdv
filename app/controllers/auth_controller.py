from flask_jwt_extended import jwt_required, unset_jwt_cookies, set_access_cookies
from flask import Blueprint, render_template, redirect, request, url_for, flash

from app.services.auth_service import AuthService
from app.security.jwt import gerar_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login/login.html")

    try:
        funcionario = AuthService.logar(request.form)
        token = gerar_token(funcionario)

        response = redirect(url_for("main.home"))
        set_access_cookies(response, token)
        return response

    except ValueError as e:
        flash(str(e), "warning")
        return render_template("login/login.html"), 401

    except Exception as e:
        flash("Erro interno ao tentar realizar o login: " + str(e), "danger")
        return render_template("login/login.html"), 500


@auth_bp.route("/logout", methods=["GET"])
@jwt_required()
def logout():
    try:
        response = redirect(url_for("auth.login"))
        unset_jwt_cookies(response)
        return response

    except Exception as e:
        flash("Erro ao tentar realizar o logout: " + str(e), "warning")
        return redirect(url_for("main.home"))