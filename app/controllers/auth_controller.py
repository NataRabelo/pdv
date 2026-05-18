from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies

from app.security.jwt import gerar_token
from app.security.rate_limit import LoginRateLimiter
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


def _login_rate_limit_key():
    usuario = (request.form.get("usuario") or "").strip().lower()
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    if "," in ip_address:
        ip_address = ip_address.split(",", 1)[0].strip()
    return f"{ip_address}:{usuario}"


def _registrar_auditoria_login(action, status, auth_data=None, details=None):
    try:
        user = (auth_data or {}).get("user")
        AuditService.registrar(
            action,
            tenant_id=getattr(user, "tenant_id", None),
            actor_scope=(auth_data or {}).get("scope"),
            actor_id=getattr(user, "id", None),
            entity_type="auth",
            status=status,
            details=details,
            commit=True,
        )
    except Exception as exc:
        current_app.logger.warning("Falha ao registrar auditoria de login: %s", exc)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("pages/login.html")

    rate_key = _login_rate_limit_key()
    allowed, retry_after = LoginRateLimiter.hit(
        rate_key,
        current_app.config["LOGIN_RATE_LIMIT_ATTEMPTS"],
        current_app.config["LOGIN_RATE_LIMIT_WINDOW_SECONDS"],
    )
    if not allowed:
        _registrar_auditoria_login(
            "auth.login_rate_limited",
            "BLOCKED",
            details=f"Tentativas excedidas. Tente novamente em {retry_after} segundos.",
        )
        flash("Muitas tentativas de login. Aguarde alguns minutos e tente novamente.", "warning")
        return render_template("pages/login.html"), 429

    try:
        auth_data = AuthService.logar(request.form)
        LoginRateLimiter.clear(rate_key)
        token = gerar_token(auth_data["user"], auth_data["scope"])
        destino = "platform.home" if auth_data["scope"] == "platform" else "main.home"

        response = redirect(url_for(destino))
        set_access_cookies(response, token)
        _registrar_auditoria_login("auth.login", "SUCCESS", auth_data=auth_data)
        return response

    except ValueError as e:
        _registrar_auditoria_login("auth.login", "FAILURE", details=str(e))
        flash(str(e), "warning")
        return render_template("pages/login.html"), 401

    except Exception as e:
        _registrar_auditoria_login("auth.login", "ERROR", details=str(e))
        flash("Erro interno ao tentar realizar o login: " + str(e), "danger")
        return render_template("pages/login.html"), 500


@auth_bp.route("/logout", methods=["GET"])
def logout():
    try:
        response = redirect(url_for("auth.login"))
        unset_jwt_cookies(response)
        _registrar_auditoria_login("auth.logout", "SUCCESS")
        return response

    except Exception as e:
        flash("Erro ao tentar realizar o logout: " + str(e), "warning")
        return redirect(url_for("main.home"))
