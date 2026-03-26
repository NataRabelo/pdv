from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.extensions import db, migrate, jwt
from app.routes import register_blueprints
from app.models.db import Funcionario
from app.config import get_config
from flask import Flask
from app.seeds.seed import run_seed


def register_context_processors(app):

    @app.context_processor
    def inject_user():
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()

            if user_id:
                funcionario = Funcionario.query.get(user_id)
                return dict(current_user=funcionario)

        except Exception:
            pass
        return dict(current_user=None)


def register_commands(app):

    @app.cli.command("seed")
    def seed_command():
        run_seed()


def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    register_context_processors(app)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    register_blueprints(app)
    register_commands(app)

    return app