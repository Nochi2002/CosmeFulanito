import os
from flask import Blueprint, redirect, url_for, session, request, render_template
from werkzeug.utils import secure_filename
import boto3

# Importación relativa de modelos
from ..models import db, User, Producto, Pedido

# Creación del Blueprint
productos_bp = Blueprint('productos', __name__, template_folder='templates')

# Configuración de AWS S3
AWS_ACCESS_KEY_ID = os.environ.get("ACCESS_KEY_S3")
AWS_SECRET_ACCESS_KEY = os.environ.get("SECRET_KEY_ACCESS_S3")
AWS_S3_BUCKET_NAME = os.environ.get("AWS_S3_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# RUTAS (alta-baja-modificar)


@productos_bp.route("/upload", methods=["GET", "POST"])
def upload_file():
    if "user_id" not in session:
        return redirect(url_for("autenticacion.login"))

    user = db.get_or_404(User, session["user_id"])

    if request.method == "POST":
        file = request.files.get("file")
        nombre_producto = request.form.get('nombre')
        descripcion_producto = request.form.get('descripcion')
        precio_producto = request.form.get('precio')
        stock_producto = request.form.get('stock')
        
        if not file:
            return render_template("upload.html", user=user, error="No seleccionaste ningún archivo")

        filename = secure_filename(file.filename)
        if not filename:
            return render_template("upload.html", user=user, error="Nombre de archivo inválido")

        try:
            s3.upload_fileobj(file, AWS_S3_BUCKET_NAME, filename)
            file_url = f"https://{AWS_S3_BUCKET_NAME}.s3.amazonaws.com/{filename}"

            new_product = Producto(
                nombre=nombre_producto,
                descripcion=descripcion_producto,
                precio=float(precio_producto),
                stock=int(stock_producto),
                imagen_url=file_url,
                vendedor_id=user.id
            )
            
            db.session.add(new_product)
            db.session.commit()

            return render_template("upload.html", user=user, success=True, file_url=file_url)

        except Exception as e:
            return render_template("upload.html", user=user, error=str(e))

    return render_template("upload.html", user=user)


@productos_bp.route("/producto/eliminar/<int:producto_id>", methods=["POST"])
def eliminar_producto(producto_id):
    # Verificar que el usuario esté logueado
    if "user_id" not in session:
        return redirect(url_for("autenticacion.login"))

    # Encontrar el producto en la base de datos
    producto_a_eliminar = Producto.query.get(producto_id)

    # Verificar que el producto exista
    if not producto_a_eliminar:
        # (Idealmente, aquí podríamos mostrar un error 404)
        return redirect(url_for("productos.gallery"))

    # Verificar que el usuario logueado sea el dueño (vendedor) del producto
    if producto_a_eliminar.vendedor_id != session["user_id"]:
        return redirect(url_for("productos.gallery"))

    # Si todo está bien, eliminar el producto
    try:
        db.session.delete(producto_a_eliminar)
        db.session.commit()
        
    except Exception as e:
        print(f"Error al eliminar: {e}")
        db.session.rollback()

    # Redirigir de vuelta a la galería
    return redirect(url_for("productos.gallery"))


@productos_bp.route("/producto/modificar/<int:producto_id>", methods=["GET", "POST"])
def modificar_producto(producto_id):
    # Verificar que el usuario esté logueado
    if "user_id" not in session:
        return redirect(url_for("autenticacion.login"))

    # Encontrar el producto que se quiere modificar
    producto_a_modificar = Producto.query.get(producto_id)

    # Verificar que exista
    if not producto_a_modificar:
        return "Producto no encontrado", 404

    # Verificar que el usuario sea el dueño
    if producto_a_modificar.vendedor_id != session["user_id"]:
        return "No tienes permiso para modificar este producto", 403

    # Si el usuario envía el formulario (POST)
    if request.method == "POST":
        try:
            producto_a_modificar.nombre = request.form.get('nombre')
            producto_a_modificar.descripcion = request.form.get('descripcion')
            producto_a_modificar.precio = float(request.form.get('precio'))
            producto_a_modificar.stock = int(request.form.get('stock'))

            db.session.commit()

            return redirect(url_for("productos.gallery"))
            
        except Exception as e:
            print(f"Error al modificar: {e}")
            db.session.rollback()
            user = db.get_or_404(User, session["user_id"])
            return render_template("modificar_producto.html", user=user, producto=producto_a_modificar, error=str(e))

    # Si el usuario solo está cargando la página (GET)
    user = db.get_or_404(User, session["user_id"])
    return render_template("modificar_producto.html", user=user, producto=producto_a_modificar)

@productos_bp.route("/gallery")
def gallery():
    user = None
    if "user_id" in session:
        user = db.get_or_404(User, session["user_id"])

    # Obtenemos el término de búsqueda de la URL
    termino_busqueda = request.args.get('q', None)

    if termino_busqueda:
        # Si hay término, filtramos la base de datos
        productos = Producto.query.filter(
            Producto.nombre.ilike(f"%{termino_busqueda}%")
        ).all()
    else:
        # Si no hay término de búsqueda, mostramos todo
        productos = Producto.query.all()

    return render_template("gallery.html", user=user, productos=productos, termino_busqueda=termino_busqueda)

# -----------------------------------------------------
# Detalle de Producto
# -----------------------------------------------------
@productos_bp.route("/producto/<int:producto_id>")
def detalle_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    
    user = None
    if "user_id" in session:
        user = db.get_or_404(User, session["user_id"])
        
    return render_template("detalle_producto.html", producto=producto, user=user)

# -----------------------------------------------------
# Confirmar Compra
# -----------------------------------------------------
@productos_bp.route("/comprar/<int:producto_id>", methods=["POST"])
def confirmar_compra(producto_id):
    # Asegurarse que el usuario esté logueado
    if "user_id" not in session:
        return redirect(url_for("autenticacion.login"))
    
    # Obtener el producto
    producto = Producto.query.get_or_404(producto_id)
    
    # Validaciones de seguridad
    if producto.vendedor_id == session["user_id"]:
        return "No puedes comprar tu propio producto", 403
    
    if producto.stock <= 0:
        return "Este producto ya no tiene stock", 400

    try:
        # Descontar el stock
        producto.stock = producto.stock - 1
        
        # Crear el Pedido
        nuevo_pedido = Pedido(
            comprador_id=session["user_id"],
            producto_id=producto_id,
            cantidad=1,
            estado="pendiente"
        )
        
        db.session.add(nuevo_pedido)
        db.session.commit()
    
    except Exception as e:
        print(f"Error al comprar: {e}")
        db.session.rollback()
        return "Hubo un error al procesar tu compra", 500

    # Redirigir al usuario a su página de "Mis Compras"
    return redirect(url_for("autenticacion.mis_compras"))