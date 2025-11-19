import os
from flask import Flask
from dotenv import load_dotenv
from .models import db

def create_app():
    # Cargar variables de entorno
    load_dotenv()

    # Crear la instancia de la app
    app = Flask(__name__)

    # Configuración de la App
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Inicializar la Base de Datos con la App
    db.init_app(app)

    # Importar y Registrar los Blueprints
    from .principal.routes import principal_bp
    from .autenticacion.routes import autenticacion_bp
    from .productos.routes import productos_bp

    app.register_blueprint(principal_bp)
    app.register_blueprint(autenticacion_bp, url_prefix='/auth')
    app.register_blueprint(productos_bp)

    return app