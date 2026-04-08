from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies

from app.security.jwt import gerar_token
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("pages/login.html")

    try:
        auth_data = AuthService.logar(request.form)
        token = gerar_token(auth_data["user"], auth_data["scope"])
        destino = "platform.home" if auth_data["scope"] == "platform" else "main.home"

        response = redirect(url_for(destino))
        set_access_cookies(response, token)
        return response

    except ValueError as e:
        flash(str(e), "warning")
        return render_template("pages/login.html"), 401

    except Exception as e:
        flash("Erro interno ao tentar realizar o login: " + str(e), "danger")
        return render_template("pages/login.html"), 500


@auth_bp.route("/logout", methods=["GET"])
def logout():
    try:
        response = redirect(url_for("auth.login"))
        unset_jwt_cookies(response)
        return response

    except Exception as e:
        flash("Erro ao tentar realizar o logout: " + str(e), "warning")
        return redirect(url_for("main.home"))
