from app.health import health_bp
from app.controllers.auth_controller import auth_bp
from app.controllers.main_controller import main_bp
from app.controllers.produto_controller import produto_bp
from app.controllers.estoque_controller import estoque_bp
from app.controllers.categoria_controller import categoria_bp


def register_blueprints(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(estoque_bp)
    app.register_blueprint(categoria_bp)

