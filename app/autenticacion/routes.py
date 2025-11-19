import os
from flask import Blueprint, redirect, url_for, session, request, render_template
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Importación relativa de modelos
from ..models import db, User, Pedido, Producto

# Creación del Blueprint
autenticacion_bp = Blueprint('autenticacion', __name__, template_folder='templates')

# Configuración de Google OAUTH
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://127.0.0.1:5000/auth/callback")

flow = Flow.from_client_config(
    client_config={
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    },
    scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_uri=REDIRECT_URI,
)

# -----------------------------------------------------
# Rutas
# -----------------------------------------------------
@autenticacion_bp.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@autenticacion_bp.route("/callback")
def callback():
    if request.args.get("state") != session.get("state"):
        return render_template("error.html", message="Error de seguridad (state mismatch)")

    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    
    try:
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        return render_template("error.html", message="Token inválido")

    google_id = id_info.get("sub")
    email = id_info.get("email")

    # 1. Buscamos por Google ID
    user = User.query.filter_by(google_id=google_id).first()

    # 2. Si no existe, buscamos por EMAIL para evitar duplicados
    # (segun gemini esto deberia dejarte logear, intenta con otro correo x si aca)
    if not user:
        user = User.query.filter_by(email=email).first()
        
        if user:
            # ¡Lo encontramos por email! Actualizamos su ID y Foto para arreglar el registro
            user.google_id = google_id
            user.picture = id_info.get("picture")
            user.name = id_info.get("name")
            db.session.commit()
        else:
            # 3. No existe por ID ni por Email -> Lo creamos desde cero
            user = User(
                google_id=google_id,
                email=email,
                name=id_info.get("name"),
                picture=id_info.get("picture"),
            )
            db.session.add(user)
            db.session.commit()

    session["user_id"] = user.id
    return redirect(url_for("autenticacion.profile"))

@autenticacion_bp.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("autenticacion.login"))
    user = db.get_or_404(User, session["user_id"])
    return render_template("profile.html", user=user)

@autenticacion_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("principal.index"))

# -----------------------------------------------------
# Mis Compras
# -----------------------------------------------------
@autenticacion_bp.route("/mis_compras")
def mis_compras():
    if "user_id" not in session:
        return redirect(url_for("autenticacion.login"))

    user = db.get_or_404(User, session["user_id"])
    
    pedidos = Pedido.query.filter_by(comprador_id=user.id)\
                          .order_by(Pedido.fecha_pedido.desc())\
                          .all()
    
    return render_template("mis_compras.html", user=user, pedidos=pedidos)

# -----------------------------------------------------
# Ventas
# -----------------------------------------------------
@autenticacion_bp.route("/mis_ventas")
def mis_ventas():
    if "user_id" not in session:
        return redirect(url_for("autenticacion.login"))

    user = db.get_or_404(User, session["user_id"])
    ventas = Pedido.query.join(Producto).filter(
        Producto.vendedor_id == user.id
    ).order_by(Pedido.fecha_pedido.desc()).all()
    
    return render_template("mis_ventas.html", user=user, ventas=ventas)

# -----------------------------------------------------
# Despacho de producto simulado
# -----------------------------------------------------
@autenticacion_bp.route("/pedido/despachar/<int:pedido_id>", methods=["POST"])
def despachar_pedido(pedido_id):
    if "user_id" not in session:
         return redirect(url_for("autenticacion.login"))

    pedido = Pedido.query.get_or_404(pedido_id)

    if pedido.producto.vendedor_id != session["user_id"]:
        return "No tienes permiso para gestionar este pedido", 403

    pedido.estado = "enviado"
    db.session.commit()

    return redirect(url_for("autenticacion.mis_ventas"))