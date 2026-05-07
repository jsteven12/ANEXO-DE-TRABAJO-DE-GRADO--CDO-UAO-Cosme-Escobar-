from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import mysql.connector
from mysql.connector import Error
from openpyxl import Workbook
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "mi_clave_secreta"

# --- Configuración de MySQL ---
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '1234567',
    'database': 'amfe_db',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'ssl_disabled': True,   # 
}


# --- Función auxiliar para conectar a la BD ---
def conectar_bd():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        raise

# --- Crear base de datos y tablas ---
def init_db():
    # Primero conectar sin especificar base de datos para crearla si no existe
    config_sin_db = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
    conn = mysql.connector.connect(**config_sin_db)
    cursor = conn.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE `{DB_CONFIG['database']}`")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dispositivos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL,
        marca VARCHAR(255),
        modelo VARCHAR(255),
        serie VARCHAR(255),
        clasificacion VARCHAR(50),
        activo_fijo VARCHAR(255),
        registro_sanitario VARCHAR(255),
        ubicacion VARCHAR(255)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    cursor.execute("""
CREATE TABLE IF NOT EXISTS amfe (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dispositivo_id INT NOT NULL,
    subproceso TEXT,
    falla_potencial_del_subproceso TEXT,
    efecto_potencial TEXT,
    causa_potencial TEXT,
    sev INT,
    ocur INT,
    det INT,
    npr INT,
    acciones_recomendadas TEXT,
    responsable TEXT,
    FOREIGN KEY (dispositivo_id) REFERENCES dispositivos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
""")

    conn.commit()
    cursor.close()
    conn.close()

init_db()

# --- Función auxiliar para crear estilos del PDF ---
def crear_estilos(prefijo=""):
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle(
        f'{prefijo}Titulo', parent=styles['Heading1'], fontSize=18,
        textColor=colors.HexColor('#1e3a8a'), alignment=1, spaceAfter=4
    )
    fecha = ParagraphStyle(
        f'{prefijo}Fecha', parent=styles['Normal'], fontSize=10,
        textColor=colors.HexColor('#64748b'), alignment=1, spaceAfter=30
    )
    seccion = ParagraphStyle(
        f'{prefijo}Seccion', parent=styles['Heading2'], fontSize=13,
        textColor=colors.HexColor('#2563eb'), spaceBefore=20, spaceAfter=10
    )
    campo = ParagraphStyle(
        f'{prefijo}Campo', parent=styles['Normal'], fontSize=11,
        spaceAfter=12, leading=16
    )
    pie = ParagraphStyle(
        f'{prefijo}Pie', parent=styles['Normal'], fontSize=8,
        textColor=colors.grey, alignment=1, spaceBefore=40
    )
    titulo_bajo = ParagraphStyle(
        f'{prefijo}TituloBajo', parent=styles['Heading3'], fontSize=12,
        textColor=colors.HexColor('#16a34a'), spaceBefore=12, spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    titulo_medio = ParagraphStyle(
        f'{prefijo}TituloMedio', parent=styles['Heading3'], fontSize=12,
        textColor=colors.HexColor('#ca8a04'), spaceBefore=12, spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    titulo_alto = ParagraphStyle(
        f'{prefijo}TituloAlto', parent=styles['Heading3'], fontSize=12,
        textColor=colors.HexColor('#dc2626'), spaceBefore=12, spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    return titulo, fecha, seccion, campo, pie, titulo_bajo, titulo_medio, titulo_alto

# ===================== RUTAS =====================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["username"]
        contraseña = request.form["password"]

        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE username=%s AND password=%s", (usuario, contraseña))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['usuario'] = usuario
            return redirect(url_for("dashboard"))
        else:
            flash("Usuario o contraseña incorrectos", "error")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM dispositivos WHERE clasificacion = 'IIB'")
    total_IIB = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dispositivos WHERE clasificacion = 'III'")
    total_III = cursor.fetchone()[0]

    total_dispositivos = total_IIB + total_III
    cursor.close()
    conn.close()

    return render_template("dashboard.html",
                           total_dispositivos=total_dispositivos,
                           total_IIB=total_IIB,
                           total_III=total_III)

# --------- REGISTRO DE NUEVO USUARIO ---------
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['username'].strip()
        contraseña = request.form['password']
        confirmar = request.form.get('confirm_password', '')

        if not usuario.endswith('@clinicadeoccidente.com') or len(usuario) <= len('@clinicadeoccidente.com'):
            flash("Debe usar un correo válido de @clinicadeoccidente.com", "error")
            return redirect(url_for('registro'))

        if len(contraseña) < 6:
            flash("La contraseña debe tener al menos 6 caracteres", "error")
            return redirect(url_for('registro'))

        if not any(c.isupper() for c in contraseña):
            flash("La contraseña debe contener al menos una letra mayúscula", "error")
            return redirect(url_for('registro'))

        if not any(c.isdigit() for c in contraseña):
            flash("La contraseña debe contener al menos un número", "error")
            return redirect(url_for('registro'))

        if contraseña != confirmar:
            flash("Las contraseñas no coinciden", "error")
            return redirect(url_for('registro'))

        conn = conectar_bd()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (usuario, contraseña))
            conn.commit()
            flash("Usuario registrado correctamente. Ya puedes iniciar sesión.", "success")
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash("El nombre de usuario ya existe. Elige otro.", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('registro.html')

# --------- INVENTARIO ---------
@app.route("/inventario", methods=["GET", "POST"])
def inventario():
    conn = conectar_bd()
    cursor = conn.cursor()

    editar_id = request.args.get("editar_id")
    editar_dispositivo = None

    if editar_id:
        cursor.execute("SELECT * FROM dispositivos WHERE id = %s", (editar_id,))
        editar_dispositivo = cursor.fetchone()

    if request.method == "POST":
        nombre = request.form["nombre"]
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        serie = request.form["serie"]
        clasificacion = request.form["clasificacion"]
        activo_fijo = request.form["activo_fijo"]
        registro_sanitario = request.form["registro_sanitario"]
        ubicacion = request.form["ubicacion"]

        editar_id = request.form.get("editar_id")

        if editar_id:
            cursor.execute("""
                UPDATE dispositivos SET
                nombre=%s, marca=%s, modelo=%s, serie=%s, clasificacion=%s,
                activo_fijo=%s, registro_sanitario=%s, ubicacion=%s
                WHERE id=%s
            """, (nombre, marca, modelo, serie, clasificacion, activo_fijo, registro_sanitario, ubicacion, editar_id))
        else:
            cursor.execute("""
                INSERT INTO dispositivos (nombre, marca, modelo, serie, clasificacion, activo_fijo, registro_sanitario, ubicacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (nombre, marca, modelo, serie, clasificacion, activo_fijo, registro_sanitario, ubicacion))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/inventario")

    cursor.execute("SELECT * FROM dispositivos")
    dispositivos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("inventario.html", dispositivos=dispositivos, editar_dispositivo=editar_dispositivo)

@app.route("/eliminar/<int:id>")
def eliminar(id):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dispositivos WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Dispositivo eliminado", "info")
    return redirect(url_for("inventario"))

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = conectar_bd()
    cursor = conn.cursor()

    if request.method == "POST":
        nombre = request.form["nombre"]
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        serie = request.form["serie"]
        clasificacion = request.form["clasificacion"]
        activo_fijo = request.form["activo_fijo"]
        registro_sanitario = request.form["registro_sanitario"]
        ubicacion = request.form["ubicacion"]

        cursor.execute("""
        UPDATE dispositivos
        SET nombre=%s, marca=%s, modelo=%s, serie=%s, clasificacion=%s,
            activo_fijo=%s, registro_sanitario=%s, ubicacion=%s
        WHERE id=%s
        """, (nombre, marca, modelo, serie, clasificacion, activo_fijo, registro_sanitario, ubicacion, id))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Dispositivo actualizado correctamente", "success")
        return redirect(url_for("inventario"))

    cursor.execute("SELECT * FROM dispositivos WHERE id=%s", (id,))
    dispositivo = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template("inventario.html", dispositivo=dispositivo)

# --------- DESCARGA EXCEL ---------
@app.route('/descargar_excel')
def descargar_excel():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dispositivos")
    dispositivos = cursor.fetchall()
    cursor.close()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario de Dispositivos"

    ws.append(["ID", "Nombre", "Marca", "Modelo", "Serie", "Clasificación",
               "Activo fijo", "Registro sanitario", "Ubicación"])

    for d in dispositivos:
        ws.append(d)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="inventario_dispositivos.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ----------- DESCARGAR EN PDF ------------
@app.route('/descargar_inventario_pdf')
def descargar_inventario_pdf():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dispositivos")
    dispositivos = cursor.fetchall()
    cursor.close()
    conn.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=30, leftMargin=30,
                           topMargin=30, bottomMargin=30)

    elements = []
    titulo_style, fecha_style, seccion_style, campo_style, pie_style, titulo_bajo, titulo_medio, titulo_alto = crear_estilos("inv_")

    elements.append(Paragraph("INVENTARIO DE DISPOSITIVOS MÉDICOS", titulo_style))
    elements.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fecha_style))
    elements.append(Spacer(1, 20))

    total_dispositivos = len(dispositivos)
    total_IIB = len([d for d in dispositivos if d[5] == 'IIB'])
    total_III = len([d for d in dispositivos if d[5] == 'III'])

    elements.append(Paragraph("RESUMEN DEL INVENTARIO", seccion_style))

    stats_data = [
        ['Total de Dispositivos:', str(total_dispositivos)],
        ['Dispositivos Clase IIB:', str(total_IIB)],
        ['Dispositivos Clase III:', str(total_III)]
    ]

    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 25))

    if dispositivos:
        elements.append(Paragraph("LISTADO COMPLETO DE DISPOSITIVOS", seccion_style))
        elements.append(Spacer(1, 12))

        table_data = [['ID', 'Nombre', 'Marca', 'Modelo', 'Serie', 'Clase', 'Activo Fijo', 'Ubicación']]

        for d in dispositivos:
            table_data.append([
                str(d[0]),
                d[1][:20] if d[1] else 'N/A',
                d[2][:15] if d[2] else 'N/A',
                d[3][:15] if d[3] else 'N/A',
                d[4][:15] if d[4] else 'N/A',
                d[5] or 'N/A',
                d[6][:15] if d[6] else 'N/A',
                d[8][:20] if d[8] else 'N/A'
            ])

        inventario_table = Table(table_data, colWidths=[0.4*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.5*inch, 0.8*inch, 1*inch])
        inventario_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
        ]))
        elements.append(inventario_table)
    else:
        elements.append(Paragraph("No hay dispositivos registrados en el inventario.", campo_style))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Este inventario fue generado automáticamente por el Sistema de Gestión AMFE", pie_style))

    doc.build(elements)
    buffer.seek(0)

    nombre_archivo = f"Inventario_Dispositivos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=nombre_archivo, mimetype='application/pdf')

# --------- LOGOUT ---------
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('login'))

# --------- INICIO (redirige al dashboard) ---------
@app.route("/inicio")
def inicio():
    return redirect(url_for("dashboard"))

# --------- MATRIZ AMFE ---------
@app.route("/matriz_amfe", methods=["GET", "POST"])
def matriz_amfe():
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre FROM dispositivos")
    dispositivos = cursor.fetchall()

    registros = []
    dispositivo_id = None

    if request.method == "POST":
        accion = request.form.get("accion")
        dispositivo_id = request.form.get("dispositivo_id")

        if accion == "guardar":
            subproceso = request.form.get("subproceso", "").strip()
            falla = request.form.get("falla_potencial_del_subproceso", "").strip()
            efecto = request.form.get("efecto_potencial", "").strip()
            causa = request.form.get("causa_potencial", "").strip()
            sev = int(request.form.get("sev", 0))
            ocur = int(request.form.get("ocur", 0))
            det = int(request.form.get("det", 0))
            npr = sev * ocur * det
            acciones = request.form.get("acciones_recomendadas", "").strip()
            responsable = request.form.get("responsable", "").strip()

            cursor.execute("""
                INSERT INTO amfe (dispositivo_id, subproceso, falla_potencial_del_subproceso,
                                  efecto_potencial, causa_potencial, sev, ocur,
                                  det, npr, acciones_recomendadas, responsable)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (dispositivo_id, subproceso, falla, efecto, causa, sev, ocur, det, npr, acciones, responsable))
            conn.commit()
            flash("Registro AMFE guardado correctamente.", "success")

        if dispositivo_id:
            cursor.execute("""
                SELECT a.id, d.nombre, a.subproceso, a.falla_potencial_del_subproceso,
                       a.efecto_potencial, a.causa_potencial, a.sev,
                       a.ocur, a.det, a.npr,
                       a.acciones_recomendadas, a.responsable
                FROM amfe a
                JOIN dispositivos d ON a.dispositivo_id = d.id
                WHERE a.dispositivo_id = %s
            """, (dispositivo_id,))
            registros = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("matriz_amfe.html", dispositivos=dispositivos, registros=registros)


# --------- EDITAR REGISTRO AMFE ---------
@app.route("/editar_amfe/<int:registro_id>", methods=["GET", "POST"])
def editar_amfe(registro_id):
    conn = conectar_bd()
    cursor = conn.cursor()

    if request.method == "POST":
        sev = int(request.form.get("sev", 1))
        ocur = int(request.form.get("ocur", 1))
        det = int(request.form.get("det", 1))
        npr = sev * ocur * det

        cursor.execute("""
            UPDATE amfe SET sev=%s, ocur=%s, det=%s, npr=%s
            WHERE id=%s
        """, (sev, ocur, det, npr, registro_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Registro AMFE actualizado correctamente.", "success")
        return redirect(url_for("matriz_amfe"))

    cursor.execute("SELECT id, sev, ocur, det, dispositivo_id FROM amfe WHERE id=%s", (registro_id,))
    reg = cursor.fetchone()
    cursor.close()
    conn.close()

    if not reg:
        flash("Registro no encontrado.", "error")
        return redirect(url_for("matriz_amfe"))

    from flask import jsonify
    return jsonify({"id": reg[0], "sev": reg[1], "ocur": reg[2], "det": reg[3], "dispositivo_id": reg[4]})


# --------- ELIMINAR REGISTRO AMFE ---------
@app.route("/eliminar_amfe/<int:registro_id>", methods=["POST"])
def eliminar_amfe(registro_id):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("SELECT dispositivo_id FROM amfe WHERE id=%s", (registro_id,))
    row = cursor.fetchone()

    cursor.execute("DELETE FROM amfe WHERE id=%s", (registro_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Modo de falla eliminado correctamente.", "info")
    return redirect(url_for("matriz_amfe"))

# --------- REPORTES ---------
@app.route("/reportes", methods=["GET"])
def reportes():
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT d.id, d.nombre, d.marca, d.modelo, d.clasificacion
        FROM dispositivos d
        INNER JOIN amfe a ON d.id = a.dispositivo_id
        ORDER BY d.nombre
    """)
    dispositivos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("reportes.html", dispositivos=dispositivos)

# --------- GENERAR PDF REPORTE COMPLETO DEL DISPOSITIVO ---------
@app.route("/generar_reporte_pdf/<int:dispositivo_id>")
def generar_reporte_pdf(dispositivo_id):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre, marca, modelo, serie, clasificacion, activo_fijo, ubicacion
        FROM dispositivos WHERE id = %s
    """, (dispositivo_id,))
    dispositivo = cursor.fetchone()

    if not dispositivo:
        flash("Dispositivo no encontrado", "error")
        cursor.close()
        conn.close()
        return redirect(url_for("reportes"))

    cursor.execute("""
        SELECT subproceso, falla_potencial_del_subproceso, efecto_potencial,
               causa_potencial, sev, ocur, det, npr,
               acciones_recomendadas, responsable
        FROM amfe WHERE dispositivo_id = %s
        ORDER BY npr DESC
    """, (dispositivo_id,))
    registros_amfe = cursor.fetchall()
    cursor.close()
    conn.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=40, leftMargin=40,
                           topMargin=40, bottomMargin=40)

    elements = []
    titulo_style, fecha_style, seccion_style, campo_style, pie_style, titulo_bajo, titulo_medio, titulo_alto = crear_estilos("rpt_")

    elements.append(Paragraph("REPORTE DE ANÁLISIS AMFE", titulo_style))
    elements.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fecha_style))

    elements.append(Paragraph("INFORMACIÓN DEL DISPOSITIVO MÉDICO", seccion_style))
    elements.append(Paragraph(f"<b>Nombre:</b> {dispositivo[0] or 'N/A'}", campo_style))
    elements.append(Paragraph(f"<b>Marca:</b> {dispositivo[1] or 'N/A'}", campo_style))
    elements.append(Paragraph(f"<b>Modelo:</b> {dispositivo[2] or 'N/A'}", campo_style))
    elements.append(Paragraph(f"<b>Serie:</b> {dispositivo[3] or 'N/A'}", campo_style))
    elements.append(Paragraph(f"<b>Clasificación:</b> {dispositivo[4] or 'N/A'}", campo_style))
    elements.append(Paragraph(f"<b>Activo Fijo:</b> {dispositivo[5] or 'N/A'}", campo_style))
    elements.append(Paragraph(f"<b>Ubicación:</b> {dispositivo[6] or 'N/A'}", campo_style))
    elements.append(Spacer(1, 20))

    if registros_amfe:
        elements.append(Paragraph("ANÁLISIS DE MODOS DE FALLA Y EFECTOS (AMFE)", seccion_style))

        for idx, reg in enumerate(registros_amfe, 1):
            npr = reg[7]
            if npr <= 10:
                titulo_falla_style = titulo_bajo
                nivel_riesgo = "RIESGO BAJO"
            elif npr <= 20:
                titulo_falla_style = titulo_medio
                nivel_riesgo = "RIESGO MEDIO"
            else:
                titulo_falla_style = titulo_alto
                nivel_riesgo = "RIESGO CRÍTICO"

            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"── Registro AMFE #{idx} - {nivel_riesgo} (NPR: {npr}) ──", titulo_falla_style))
            elements.append(Paragraph(f"<b>Subproceso:</b> {reg[0] or 'N/A'}", campo_style))
            elements.append(Paragraph(f"<b>Falla Potencial:</b> {reg[1] or 'N/A'}", campo_style))
            elements.append(Paragraph(f"<b>Efecto Potencial:</b> {reg[2] or 'N/A'}", campo_style))
            elements.append(Paragraph(f"<b>Causa Potencial:</b> {reg[3] or 'N/A'}", campo_style))
            elements.append(Paragraph(f"<b>Severidad:</b> {reg[4]} | <b>Ocurrencia:</b> {reg[5]} | <b>Detección:</b> {reg[6]} | <b>NPR:</b> {reg[7]}", campo_style))
            elements.append(Paragraph(f"<b>Acciones Recomendadas:</b> {reg[8] or 'N/A'}", campo_style))
            elements.append(Paragraph(f"<b>Responsable:</b> {reg[9] or 'N/A'}", campo_style))
    else:
        elements.append(Paragraph("No se encontraron registros AMFE para este dispositivo.", campo_style))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Este reporte fue generado automáticamente por el Sistema de Gestión AMFE", pie_style))

    doc.build(elements)
    buffer.seek(0)

    nombre_archivo = f"Reporte_AMFE_{dispositivo[0].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=nombre_archivo, mimetype='application/pdf')

# --------- GENERAR PDF DE UNA SOLA FALLA ---------
@app.route("/generar_reporte_falla/<int:registro_id>")
def generar_reporte_falla(registro_id):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.nombre,
               a.subproceso, a.falla_potencial_del_subproceso, a.efecto_potencial,
               a.causa_potencial, a.acciones_recomendadas, a.responsable
        FROM amfe a
        JOIN dispositivos d ON a.dispositivo_id = d.id
        WHERE a.id = %s
    """, (registro_id,))
    registro = cursor.fetchone()
    cursor.close()
    conn.close()

    if not registro:
        flash("Registro no encontrado", "error")
        return redirect(url_for("matriz_amfe"))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=50, leftMargin=50,
                           topMargin=50, bottomMargin=50)

    elements = []
    titulo_style, fecha_style, seccion_style, campo_style, pie_style, titulo_bajo, titulo_medio, titulo_alto = crear_estilos("falla_")

    elements.append(Paragraph("REPORTE DE FALLA POTENCIAL", titulo_style))
    elements.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fecha_style))

    elements.append(Paragraph("Dispositivo", seccion_style))
    elements.append(Paragraph(f"{registro[0] or 'N/A'}", campo_style))
    elements.append(Paragraph("Subproceso", seccion_style))
    elements.append(Paragraph(f"{registro[1] or 'N/A'}", campo_style))
    elements.append(Paragraph("Falla Potencial", seccion_style))
    elements.append(Paragraph(f"{registro[2] or 'N/A'}", campo_style))
    elements.append(Paragraph("Efecto Potencial", seccion_style))
    elements.append(Paragraph(f"{registro[3] or 'N/A'}", campo_style))
    elements.append(Paragraph("Causa Potencial", seccion_style))
    elements.append(Paragraph(f"{registro[4] or 'N/A'}", campo_style))
    elements.append(Paragraph("Acciones Recomendadas", seccion_style))
    elements.append(Paragraph(f"{registro[5] or 'N/A'}", campo_style))
    elements.append(Paragraph("Responsable", seccion_style))
    elements.append(Paragraph(f"{registro[6] or 'N/A'}", campo_style))

    elements.append(Paragraph("Este reporte fue generado automáticamente por el Sistema de Gestión AMFE", pie_style))

    doc.build(elements)
    buffer.seek(0)

    nombre_archivo = f"Reporte_Falla_{registro[2].replace(' ', '_') if registro[2] else 'Sin_nombre'}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=nombre_archivo, mimetype='application/pdf')

# =============================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)