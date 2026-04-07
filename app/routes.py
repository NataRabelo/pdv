from app.health import health_bp
from app.controllers.auth_controller import auth_bp
from app.controllers.main_controller import main_bp
from app.controllers.produto_controller import produto_bp
from app.controllers.estoque_controller import estoque_bp
from app.controllers.categoria_controller import categoria_bp
from app.controllers.funcionario_controller import funcionario_bp
from app.controllers.role_controller import role_bp
from app.controllers.permission_controller import permission_bp


def register_blueprints(app):
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(produto_bp, url_prefix="/api/produtos")
    app.register_blueprint(estoque_bp, url_prefix="/api/estoque")
    app.register_blueprint(categoria_bp, url_prefix="/api/categorias")
    app.register_blueprint(funcionario_bp, url_prefix="/api/funcionarios")
    app.register_blueprint(role_bp, url_prefix="/api/roles")
    app.register_blueprint(permission_bp, url_prefix="/api/permissions")
