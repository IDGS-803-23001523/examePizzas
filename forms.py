from flask_wtf import FlaskForm
from wtforms import Form
from wtforms import StringField, IntegerField, RadioField, SelectMultipleField
from wtforms import validators

class ClienteForm(FlaskForm):
    nombre = StringField('Nombre completo', [
        validators.DataRequired(message='El nombre es requerido'),
        validators.length(min=3, max=100)
    ])
    direccion = StringField('Dirección', [
        validators.DataRequired(message='La dirección es requerida'),
        validators.length(min=5, max=200)
    ])
    telefono = StringField('Teléfono', [
        validators.DataRequired(message='El teléfono es requerido'),
        validators.length(min=10, max=10, message='10 dígitos')
    ])

class PizzaTemporalForm(Form):
    tamaño = RadioField('Tamaño', [
        validators.DataRequired(message='Selecciona un tamaño')
    ], choices=[
        ('pequena', 'Pequeña'),
        ('mediana', 'Mediana'),
        ('grande', 'Grande')
    ])
    
    ingredientes = SelectMultipleField('Ingredientes', [
        validators.DataRequired(message='Selecciona al menos un ingrediente')
    ], choices=[
        ('jamon', 'Jamón'), ('pepperoni', 'Pepperoni'),
        ('champiñones', 'Champiñones'), ('cebolla', 'Cebolla'),
        ('pimiento', 'Pimiento'), ('aceitunas', 'Aceitunas'),
        ('piña', 'Piña'), ('extra_queso', 'Extra Queso')
    ])
    
    numero_pizzas = IntegerField('Número de pizzas', [
        validators.DataRequired(message='La cantidad es requerida'),
        validators.NumberRange(min=1, max=100)
    ])