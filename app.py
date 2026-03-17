from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from models import db
from models import Clientes, Pedidos, DetallePedido, Pizzas
from sqlalchemy import func
from sqlalchemy import extract
from datetime import datetime, timedelta


import forms

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()
migrate = Migrate(app, db)
db.init_app(app)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.route("/")
def index():
    return render_template("bienvenida.html")

@app.route("/pedidos", methods=['GET', 'POST'])
def pedidos():
    create_form = forms.ClienteForm(request.form)
    
    # Inicializar sesión para pedido temporal
    if 'pedido_temporal' not in session:
        session['pedido_temporal'] = []
    
    if request.method == 'POST' and request.form.get('accion') == 'agregar':
        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        tamaño = request.form.get('tamaño')
        ingredientes = request.form.getlist('ingredientes')
        numero_pizzas = int(request.form.get('numero_pizzas', 1))
        
        # Guardar datos del cliente en sesión para que persistan
        session['cliente_temp'] = {
            'nombre': nombre,
            'direccion': direccion,
            'telefono': telefono
        }
        
        # Calcular subtotal
        precios = {'pequena': 80, 'mediana': 120, 'grande': 160}
        precio_base = precios.get(tamaño, 80)
        precio_ingredientes = len(ingredientes) * 10
        subtotal = (precio_base + precio_ingredientes) * numero_pizzas
        
        # Crear item temporal
        item = {
            'id': len(session['pedido_temporal']) + 1,
            'tamaño': tamaño,
            'ingredientes': ', '.join(ingredientes),
            'cantidad': numero_pizzas,
            'subtotal': subtotal
        }
        
        # Agregar a la sesión
        session['pedido_temporal'].append(item)
        session.modified = True
        
        flash('Pizza agregada al pedido', 'success')
        return redirect(url_for('pedidos'))
    
    # Si hay datos de cliente en sesión, llenar el formulario
    if 'cliente_temp' in session:
        create_form.nombre.data = session['cliente_temp'].get('nombre', '')
        create_form.direccion.data = session['cliente_temp'].get('direccion', '')
        create_form.telefono.data = session['cliente_temp'].get('telefono', '')
    
    # Obtener datos para la plantilla
    pedido_temporal = session.get('pedido_temporal', [])
    total = sum(item['subtotal'] for item in pedido_temporal)
    
    return render_template("pedidos.html", 
                         form=create_form, 
                         pedido_temporal=pedido_temporal,
                         total=total)

@app.route("/quitar_pizza", methods=['POST'])
def quitar_pizza():
    if request.method == 'POST':
        item_id = int(request.form.get('item_id'))
        
        # Eliminar de la sesión
        pedido_temporal = session.get('pedido_temporal', [])
        session['pedido_temporal'] = [item for item in pedido_temporal if item['id'] != item_id]
        session.modified = True
        
        flash('Pizza eliminada del pedido', 'success')
    return redirect(url_for('pedidos'))

@app.route("/terminar_pedido", methods=['POST'])
def terminar_pedido():
    pedido_temporal = session.get('pedido_temporal', [])
    cliente_temp = session.get('cliente_temp', {})
    
    if not pedido_temporal:
        flash('No hay pizzas en el pedido', 'error')
        return redirect(url_for('pedidos'))
    
    if not cliente_temp:
        flash('Debes ingresar datos del cliente', 'error')
        return redirect(url_for('pedidos'))
    
    try:
        # Calcular total
        total = sum(item['subtotal'] for item in pedido_temporal)
        
        # Guardar o buscar cliente
        cliente = Clientes.query.filter_by(telefono=cliente_temp['telefono']).first()
        
        if not cliente:
            cliente = Clientes(
                nombre=cliente_temp['nombre'],
                direccion=cliente_temp['direccion'],
                telefono=cliente_temp['telefono']
            )
            db.session.add(cliente)
            db.session.flush()
        
        # Crear pedido
        pedido = Pedidos(
            total=total,
            cliente_id=cliente.id
        )
        db.session.add(pedido)
        db.session.flush()
        
        # Crear detalles del pedido (UNA PIZZA NUEVA POR CADA ITEM)
        for item in pedido_temporal:
            # Crear una nueva pizza en la tabla pizzas
            nueva_pizza = Pizzas(
                nombre=f"Pizza {item['tamaño']}",
                ingredientes=item['ingredientes'],
                precio=item['subtotal'] // item['cantidad']  # Precio unitario
            )
            db.session.add(nueva_pizza)
            db.session.flush()  # Para obtener el ID
            
            # Crear detalle del pedido con la nueva pizza
            detalle = DetallePedido(
                cantidad=item['cantidad'],
                subtotal=item['subtotal'],
                pedido_id=pedido.id,
                pizza_id=nueva_pizza.id
            )
            db.session.add(detalle)
        
        db.session.commit()
        
        flash(f'Pedido confirmado. Total a pagar: ${total}', 'success')
        
        # Limpiar sesión
        session.pop('pedido_temporal', None)
        session.pop('cliente_temp', None)
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar el pedido: {str(e)}', 'error')
    
    return redirect(url_for('pedidos'))


@app.route("/ventas_dia", methods=['GET', 'POST'])
def ventas_dia():
    ventas = []
    total = 0
    dia_seleccionado = None
    
    if request.method == 'POST':
        dia_seleccionado = request.form.get('dia')
        
        if dia_seleccionado:
            # Mapeo de días para MySQL (1=domingo, 2=lunes...)
            dias_map = {
                'domingo': 1,
                'lunes': 2,
                'martes': 3,
                'miércoles': 4,
                'jueves': 5,
                'viernes': 6,
                'sábado': 7
            }
            
            numero_dia = dias_map.get(dia_seleccionado.lower(), 0)
            
            if numero_dia > 0:
                # Calcular fecha de hace 7 días
                fecha_limite = datetime.now() - timedelta(days=7)
                
                # Buscar ventas del día seleccionado en la última semana
                ventas = db.session.query(Pedidos).filter(
                    func.dayofweek(Pedidos.fecha) == numero_dia,
                    Pedidos.fecha >= fecha_limite
                ).all()
                
                total = sum(v.total for v in ventas)
    
    return render_template("busquedaDia.html", 
                         ventas=ventas, 
                         total=total,
                         dia_seleccionado=dia_seleccionado)


@app.route("/ventas_mes", methods=['GET', 'POST'])
def ventas_mes():
    if request.method == 'POST':
        mes = request.form.get('mes')
        
        # Mapeo de meses en español a números
        meses_map = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        numero_mes = meses_map.get(mes.lower(), 1)
        
        # Consultar ventas por mes usando extract
        ventas = db.session.query(Pedidos).filter(
            extract('month', Pedidos.fecha) == numero_mes
        ).all()
        
        total_acumulado = sum(v.total for v in ventas)
        
        return render_template("busquedaMes.html", 
                             ventas=ventas, 
                             total=total_acumulado,
                             mes_seleccionado=mes)
    
    return render_template("busquedaMes.html", ventas=[], total=0, mes_seleccionado=None)

if __name__ == '__main__':
	csrf.init_app(app)
	with app.app_context():
		db.create_all()
	app.run()