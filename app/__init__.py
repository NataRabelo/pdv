import os

from flask import Flask
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.config import get_config
from app.extensions import db, jwt, migrate
from app.models.db import Funcionario, PlatformOwner
from app.routes import register_blueprints
from app.security.jwt import get_auth_scope
from app.seeds.seed import run_seed


def register_extensions(app: Flask) -> None:
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)


def register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_user():
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()

            if user_id:
                auth_scope = get_auth_scope()

                if auth_scope == "platform":
                    owner = db.session.get(PlatformOwner, int(user_id))
                    return {
                        "current_user": None,
                        "current_platform_owner": owner,
                        "current_auth_scope": auth_scope,
                    }

                funcionario = db.session.get(Funcionario, int(user_id))
                return {
                    "current_user": funcionario,
                    "current_platform_owner": None,
                    "current_auth_scope": auth_scope,
                }

        except Exception:
            pass

        return {
            "current_user": None,
            "current_platform_owner": None,
            "current_auth_scope": None,
        }


def register_commands(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command():
        """Executa a carga inicial de dados do sistema."""
        run_seed()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config())
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

    register_extensions(app)
    register_blueprints(app)
    register_context_processors(app)
    register_commands(app)

    return app
