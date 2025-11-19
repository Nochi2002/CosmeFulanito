from flask import Blueprint, redirect, url_for, session, render_template

# Creación del Blueprint
principal_bp = Blueprint('principal', __name__, template_folder='templates')

# Definición de la ruta raíz
@principal_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("autenticacion.profile"))
    
    return render_template("index.html")