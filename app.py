import calendar
import datetime
from flask import Flask, flash, render_template, request, redirect, url_for, jsonify
import firebase_admin
import json
import os
from firebase_admin import credentials, firestore
from datetime import datetime
from flask import render_template

app = Flask(__name__)

app.secret_key = 'mapachespeludos_69'
MESES_COMPLETOS = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
]
# Leer la configuración desde variable de entorno
firebase_config = os.environ.get("FIREBASE_CONFIG")

if not firebase_config:
    raise Exception("FIREBASE_CONFIG no está definida en las variables de entorno de Render")

# Convertir string a diccionario
firebase_config_dict = json.loads(firebase_config)

# Inicializar Firebase con credenciales
cred = credentials.Certificate(firebase_config_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()



# Ruta de menu principal
@app.route('/')
def menu():
    return render_template('menu.html')

#Inicio PDF

@app.route("/usuario/<folio>/tarjeta")
def tarjeta_usuario(folio):
    # Buscar usuario por folio en Firestore
    usuarios_ref = db.collection("usuarios")
    query = usuarios_ref.where("Folio", "==", folio).limit(1).stream()

    usuario = None
    for doc in query:
        usuario = doc.to_dict()
        break

    if usuario:
        return render_template("tarjeta_usuario.html", usuario=usuario)
    else:
        return "Usuario no encontrado", 404

import qrcode
import io
from flask import send_file

@app.route("/qr/<folio>")
def codigo_qr(folio):
    url = request.host_url.rstrip("/") + url_for("vista_usuario_qr", folio=folio)
    qr_img = qrcode.make(url)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")

@app.route("/usuario/<folio>/vista_qr")
def vista_usuario_qr(folio):
    usuarios_ref = db.collection("usuarios")
    query = usuarios_ref.where("Folio", "==", folio).limit(1).stream()

    usuario = None
    for doc in query:
        usuario = doc.to_dict()
        break

    if usuario:
        return render_template("vista_qr_usuario.html", usuario=usuario)
    else:
        return "Usuario no encontrado", 404

from reportlab.pdfgen import canvas

@app.route("/usuario/<folio>/descargar_pdf")
def descargar_pdf(folio):
    usuarios_ref = db.collection("usuarios")
    query = usuarios_ref.where("Folio", "==", folio).limit(1).stream()

    usuario = None
    for doc in query:
        usuario = doc.to_dict()
        break

    if not usuario:
        return "Usuario no encontrado", 404

    # Generar código QR para la URL del usuario
    qr_url = request.host_url.rstrip("/") + url_for("vista_usuario_qr", folio=folio)
    qr_img = qrcode.make(qr_url)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # Crear el PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(250, 150))  # Tamaño tipo tarjeta

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20, 120, f"Folio: {usuario['Folio']}")
    c.drawString(20, 100, f"Nombre: {usuario['Nombre_completo']}")
    c.drawString(20, 80, f"Colonia: {usuario['Colonia']}")
    c.drawString(20, 60, f"Dirección: {usuario['Direccion']}")

    # Agregar el QR
    from reportlab.lib.utils import ImageReader
    qr_img_reader = ImageReader(qr_buffer)
    c.drawImage(qr_img_reader, 170, 40, width=60, height=60)

    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"tarjeta_{folio}.pdf", mimetype='application/pdf')



#Fin de PDF
# Ruta de pagina de usuarios
#Agregar restriciones de busqueda en numeros, CP...
@app.route('/usuarios')
def usuarios():
    busqueda = request.args.get('busqueda', '').strip().lower()
    usuarios_ref = db.collection('usuarios').stream()
    usuarios = []

    for doc in usuarios_ref:
        data = doc.to_dict()
        # Convertir campos a minúsculas
        nombre = data.get('Nombre_completo', '').lower()
        colonia = data.get('Colonia', '').lower()
        folio = data.get('Folio', '').lower()

        if not busqueda or (busqueda in nombre or busqueda in colonia or busqueda in folio):
            usuarios.append(data)
    return render_template('usuarios.html', usuarios=usuarios)


#Ruta de registro de usuarios
@app.route('/registrar_usuario', methods=['GET', 'POST'])
def registrar_usuario():
    if request.method == 'POST':
        data = {
            'Nombre_completo': request.form['nombre_completo'],
            'Curp': request.form['curp'],
            'Folio': request.form['folio'],
            'Numero_contacto': int(request.form['numero_contacto']),
            'Email': request.form['email'],
            'Direccion': request.form['direccion'],
            'Colonia': request.form['colonia'],
            'Codigo_postal': int(request.form['codigo_postal']),
            'Genero': request.form['genero'],
            'Estatus': request.form['estatus']
        }
        db.collection('usuarios').add(data)
        return redirect('/usuarios')
    return render_template('registrar_usuario.html')


# Ruta de edicion de usuarios
@app.route('/editar_usuario/<folio>', methods=['GET', 'POST'])
def editar_usuario(folio):
    usuarios_ref = db.collection('usuarios')
    query = usuarios_ref.where('Folio', '==', folio).limit(1).stream()
    doc = next(query, None)
# Complememtar
    if not doc:
        return "Usuario no encontrado", 404
    doc_id = doc.id
    usuario_data = doc.to_dict()

    if request.method == 'POST':
        nuevo_data = {
            'Nombre_completo': request.form['nombre_completo'],
            'Curp': request.form['curp'],
            'Folio': request.form['folio'],
            'Numero_contacto': int(request.form['numero_contacto']),
            'Email': request.form['email'],
            'Direccion': request.form['direccion'],
            'Colonia': request.form['colonia'],
            'Codigo_postal': int(request.form['codigo_postal']),
            'Genero': request.form['genero'],
            'Estatus': request.form['estatus']
        }
        db.collection('usuarios').document(doc_id).set(nuevo_data)
        return redirect('/usuarios')
    return render_template('editar_usuario.html', usuario=usuario_data)


# Ruta de eliminar de usuarios
@app.route('/eliminar_usuario/<folio>')
def eliminar_usuario(folio):
    usuarios_ref = db.collection('usuarios')
    query = usuarios_ref.where('Folio', '==', folio).limit(1).stream()
    doc = next(query, None)
    if doc:
        db.collection('usuarios').document(doc.id).delete()
    return redirect('/usuarios')


@app.route('/pagos')
def pagos():
    busqueda = request.args.get('busqueda', '').strip().lower()
    usuarios_ref = db.collection('usuarios').stream()
    
    usuarios_con_estado = []
    todos_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    for doc in usuarios_ref:
        data = doc.to_dict()
        nombre = data.get('Nombre_completo', '').lower()
        colonia = data.get('Colonia', '').lower()
        folio = data.get('Folio', '').lower()

        if not busqueda or (busqueda in nombre or busqueda in colonia or busqueda in folio):
            # Verificar estado del usuario
            estado_usuario = data.get('Estado', 'Activo')
            
            # Solo verificar pagos si el usuario está activo
            if estado_usuario == 'Activo':
                # Obtener todos los pagos del usuario
                pagos_ref = db.collection('pagos').where('Folio_usuario', '==', data['Folio']).stream()
                
                meses_pagados = set()
                for pago in pagos_ref:
                    pago_data = pago.to_dict()
                    if 'Periodo' in pago_data:
                        meses_pago = pago_data['Periodo'].split(', ')
                        meses_pagados.update(meses_pago)
                
                # Determinar estado de pago
                estado_pago = 'Pagado' if len(meses_pagados) == len(todos_meses) else 'Debe'
            else:
                estado_pago = 'Inactivo'
            
            data['Estado'] = estado_usuario
            data['EstadoPago'] = estado_pago
            usuarios_con_estado.append(data)
    
    return render_template('pagos.html', usuarios=usuarios_con_estado)

@app.route('/registrar_pago/<folio>', methods=['GET', 'POST'])
def registrar_pago(folio):
    # Obtener usuario
    usuarios_ref = db.collection('usuarios').where('Folio', '==', folio).limit(1).stream()
    usuario = next(usuarios_ref, None)
    
    if not usuario:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('pagos'))
    
    usuario = usuario.to_dict()
    
    # Obtener año actual y disponibles (actual + 3 atrás)
    año_actual = datetime.now().year
    años_disponibles = list(range(año_actual - 3, año_actual + 1))
    
    # Para GET requests, usar año actual por defecto
    año_seleccionado = año_actual
    
    if request.method == 'POST':
        try:
            año_seleccionado = int(request.form['anio'])
            monto = float(request.form['monto'])
            meses_seleccionados = request.form.getlist('meses')
            
            # Validaciones
            if not meses_seleccionados:
                flash('Debe seleccionar al menos un mes', 'danger')
                return redirect(url_for('registrar_pago', folio=folio))
                
            # Verificar meses no pagados previamente en el año seleccionado
            pagos_ref = db.collection('pagos')\
                         .where('Folio_usuario', '==', folio)\
                         .where('anio', '==', año_seleccionado)\
                         .stream()
            
            meses_pagados = set()
            for pago in pagos_ref:
                pago_data = pago.to_dict()
                if 'Periodo' in pago_data:
                    meses_pago = pago_data['Periodo'].split(', ')
                    meses_pagados.update(meses_pago)
            
            for mes in meses_seleccionados:
                if mes in meses_pagados:
                    flash(f'El mes {mes} del año {año_seleccionado} ya fue pagado anteriormente', 'danger')
                    return redirect(url_for('registrar_pago', folio=folio))
            
            # Registrar el pago
            pago_data = {
                'Folio_usuario': folio,
                'Monto': monto,
                'anio': año_seleccionado,
                'Estado_pago': 'Completo' if len(meses_seleccionados) == len(MESES_COMPLETOS) else 'Parcial',
                'Fecha_pago': datetime.now().strftime("%d/%m/%Y, %H:%M"),
                'Periodo': ', '.join(meses_seleccionados),
                'Timestamp': datetime.now().isoformat()
            }
            
            db.collection('pagos').add(pago_data)
            flash(f'Pago registrado para {len(meses_seleccionados)} mes(es) del año {año_seleccionado}', 'success')
            return redirect(url_for('pagos'))
            
        except ValueError:
            flash('Datos inválidos', 'danger')
        except Exception as e:
            flash(f'Error al registrar pago: {str(e)}', 'danger')
    
    # Para GET requests, obtener meses pendientes del año actual
    pagos_ref = db.collection('pagos')\
                 .where('Folio_usuario', '==', folio)\
                 .where('anio', '==', año_seleccionado)\
                 .stream()
    
    meses_pagados = set()
    for pago in pagos_ref:
        pago_data = pago.to_dict()
        if 'Periodo' in pago_data:
            meses_pago = pago_data['Periodo'].split(', ')
            meses_pagados.update(meses_pago)
    
    meses_pendientes = [mes for mes in MESES_COMPLETOS if mes not in meses_pagados]
    
    return render_template('registrar_pago.html',
                         usuario=usuario,
                         meses_pendientes=meses_pendientes,
                         años_disponibles=años_disponibles,
                         año_actual=año_seleccionado,
                         fecha_actual=datetime.now().strftime("%d/%m/%Y, %H:%M"),
                         fecha_actual_iso=datetime.now().isoformat())

@app.route('/get_meses_pendientes')
def get_meses_pendientes():
    folio = request.args.get('folio')
    año = int(request.args.get('anio'))
    
    # Obtener meses ya pagados para este año
    pagos_ref = db.collection('pagos')\
                 .where('Folio_usuario', '==', folio)\
                 .where('anio', '==', año)\
                 .stream()
    
    meses_pagados = set()
    for pago in pagos_ref:
        pago_data = pago.to_dict()
        if 'Periodo' in pago_data:
            meses_pago = pago_data['Periodo'].split(', ')
            meses_pagados.update(meses_pago)
    
    meses_pendientes = [mes for mes in MESES_COMPLETOS if mes not in meses_pagados]
    
    return jsonify({
        'meses_pendientes': meses_pendientes
    })

@app.route('/dar_baja_usuario/<folio>', methods=['POST'])
def dar_baja_usuario(folio):
    try:
        # Obtener información del usuario
        usuarios_ref = db.collection('usuarios').where('Folio', '==', folio).limit(1).stream()
        usuario = next(usuarios_ref, None)
        
        if not usuario:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('pagos'))
        
        # Crear registro de baja simple
        baja_data = {
            'folio_usuario': folio,
            'nombre_usuario': usuario.to_dict().get('Nombre_completo', ''),
            'fecha_baja': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'timestamp': datetime.now().isoformat()
        }
        
        # Guardar en Firestore (en una colección de bajas)
        db.collection('bajas').add(baja_data)
        
        # Marcar al usuario como inactivo
        usuario_ref = db.collection('usuarios').document(usuario.id)
        usuario_ref.update({'Estado': 'Inactivo'})
        
        flash(f'Usuario {folio} dado de baja correctamente', 'success')
        return redirect(url_for('pagos'))
        
    except Exception as e:
        flash(f'Error al dar de baja al usuario: {str(e)}', 'danger')
        return redirect(url_for('registrar_pago', folio=folio))

@app.route('/historial_pagos/<folio>')
def historial_pagos(folio):
    # Obtener información del usuario
    usuarios_ref = db.collection('usuarios').where('Folio', '==', folio).limit(1).stream()
    usuario = next(usuarios_ref, None)
    
    if not usuario:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('pagos'))
    
    usuario = usuario.to_dict()
    
    # Obtener año actual 
    año_actual = datetime.now().year
    años_disponibles = list(range(año_actual - 3, año_actual + 1))
    
    # Obtener todos los pagos del usuario 
    pagos_ref = db.collection('pagos')\
                 .where('Folio_usuario', '==', folio)\
                 .where('anio', '==', año_actual)\
                 .stream()
    
    # Procesar pagos por mes
    pagos_por_mes = {}
    for pago in pagos_ref:
        pago_data = pago.to_dict()
        if 'Periodo' in pago_data:
            for mes in pago_data['Periodo'].split(', '):
                pagos_por_mes[mes] = True
    
    
    meses_pendientes = [mes for mes in MESES_COMPLETOS if mes not in pagos_por_mes]
    
    # Generar datos de calendario para cada mes
    calendarios = {}
    for mes_num in range(1, 13):
        mes_nombre = MESES_COMPLETOS[mes_num-1]
        cal = calendar.monthcalendar(año_actual, mes_num)
        calendarios[mes_nombre] = {
            'semanas': cal,
            'dias_en_mes': calendar.monthrange(año_actual, mes_num)[1],
            'primer_dia': calendar.monthrange(año_actual, mes_num)[0]
        }
    
    return render_template('historial_pagos.html',
                         usuario=usuario,
                         pagos_por_mes=pagos_por_mes,
                         meses_pendientes=meses_pendientes,
                         meses_completos=MESES_COMPLETOS,
                         calendarios=calendarios,
                         año_actual=año_actual,
                         años_disponibles=años_disponibles)

@app.route('/get_historial_pagos')
def get_historial_pagos():
    try:
        folio = request.args.get('folio')
        año = int(request.args.get('anio'))
        
        # Obtener pagos del usuario 
        pagos_ref = db.collection('pagos')\
                     .where('Folio_usuario', '==', folio)\
                     .where('anio', '==', año)\
                     .stream()
        
        # Procesar pagos por mes
        pagos_por_mes = {}
        for pago in pagos_ref:
            pago_data = pago.to_dict()
            if 'Periodo' in pago_data:
                for mes in pago_data['Periodo'].split(', '):
                    pagos_por_mes[mes] = True
        
        
        meses_pendientes = [mes for mes in MESES_COMPLETOS if mes not in pagos_por_mes]
        
        # Generar datos de calendario para cada mes
        calendarios = {}
        for mes_num in range(1, 13):
            mes_nombre = MESES_COMPLETOS[mes_num-1]
            cal = calendar.monthcalendar(año, mes_num)
            calendarios[mes_nombre] = {
                'semanas': cal,
                'dias_en_mes': calendar.monthrange(año, mes_num)[1],
                'primer_dia': calendar.monthrange(año, mes_num)[0]
            }
        
        return jsonify({
            'success': True,
            'meses_pendientes': meses_pendientes,
            'meses_completos': MESES_COMPLETOS,
            'calendarios': calendarios,
            'año_actual': año
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
