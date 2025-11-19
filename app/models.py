from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# MODELO DE USUARIO
class User(db.Model):
    """ Tabla para guardar la información de los usuarios (Compradores y Vendedores). """
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100))
    picture = db.Column(db.String(200))
    
    productos = db.relationship("Producto", backref="vendedor", lazy=True)
    pedidos = db.relationship("Pedido", backref="comprador", lazy=True)


# MODELO DE PRODUCTO
class Producto(db.Model):
    """ Tabla para guardar los productos publicados por los vendedores. """
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    
    imagen_url = db.Column(db.String(300), nullable=False)
    fecha_publicacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Clave foránea: Vincula el producto con el usuario que lo creó.
    vendedor_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    
    # Relación con los pedidos que incluyen este producto.
    pedidos_rel = db.relationship('Pedido', backref='producto_vendido')


# MODELO DE PEDIDO
class Pedido(db.Model):
    """ Tabla para registrar las compras realizadas. """
    __tablename__ = 'pedidos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Quién compró
    comprador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    # Qué compró
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')
    fecha_pedido = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    producto = db.relationship('Producto', backref='ordenes_de_compra')