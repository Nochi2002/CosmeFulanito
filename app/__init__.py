import os
from flask import Flask
from dotenv import load_dotenv
from .models import db
from .principal.routes import principal_bp
from .autenticacion.routes import autenticacion_bp
from .productos.routes import productos_bp

def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
    
    # Gemini dice con esto obtenemos la carpeta donde estamos parados la raíz del proyecto
    basedir = os.path.abspath(os.getcwd())
    
    # Forzamos a que la base de datos esté siempre en 'users.db' en la raíz
    db_path = os.path.join(basedir, 'users.db')
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    db.init_app(app)

    # Importar y Registrar los Blueprints
    

    app.register_blueprint(principal_bp)
    app.register_blueprint(autenticacion_bp, url_prefix='/auth')
    app.register_blueprint(productos_bp)

    return app