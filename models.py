import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Pizzas(db.Model):
    __tablename__ = 'pizzas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    ingredientes = db.Column(db.String(200))
    precio = db.Column(db.Float)


class Clientes(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    create_date = db.Column(db.DateTime, default=datetime.datetime.now)

    pedidos = db.relationship('Pedidos', back_populates='cliente')


class Pedidos(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.datetime.now)
    total = db.Column(db.Float)

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey('clientes.id'),
        nullable=False
    )

    cliente = db.relationship('Clientes', back_populates='pedidos')
    detalles = db.relationship('DetallePedido', back_populates='pedido')


class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedido'
    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer)
    subtotal = db.Column(db.Float)

    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey('pedidos.id'),
        nullable=False
    )

    pizza_id = db.Column(
        db.Integer,
        db.ForeignKey('pizzas.id'),
        nullable=False
    )

    pedido = db.relationship('Pedidos', back_populates='detalles')
    pizza = db.relationship('Pizzas')