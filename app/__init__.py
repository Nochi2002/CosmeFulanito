import os
from flask import Flask
from dotenv import load_dotenv
from .models import db

def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
    
    base_dir = os.path.abspath(os.path.dirname(__file__))
    root_dir = os.path.dirname(base_dir)

    db_path = os.path.join(root_dir, 'instance', 'users.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    db.init_app(app)

    from .principal.routes import principal_bp
    from .autenticacion.routes import autenticacion_bp
    from .productos.routes import productos_bp

    app.register_blueprint(principal_bp)
    app.register_blueprint(autenticacion_bp, url_prefix='/auth')
    app.register_blueprint(productos_bp)

    return app