from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from supabase import create_client, Client
import hashlib
import secrets
from datetime import datetime



app = Flask(__name__)

app.secret_key = "1234567890"

SUPABASE_URL = "https://puivxckjypuyuoxmfsoa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1aXZ4Y2tqeXB1eXVveG1mc29hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0NTA0NDMsImV4cCI6MjA3NjAyNjQ0M30.ndNCHjGnP8T-MbHLd4BlUsZk6W-b149DEOSwNyrUvZw"


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ===== FUNCIONES DE ENCRIPTACIÓN =====
def hash_password(password):
    """Encripta el password"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"


def verificar_password(password_ingresado, password_hash_almacenado):
    """Verifica si el password es correcto"""
    try:
        salt, stored_hash = password_hash_almacenado.split(':')
        pwd_hash = hashlib.sha256((password_ingresado + salt).encode()).hexdigest()
        return pwd_hash == stored_hash
    except:
        return False



@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("usuario")  # nombre del input
        contrasena = request.form.get("password")

        # ✅ Buscar si el correo existe en la tabla "usuarios"
        response = supabase.table("usuarios").select("*").eq("email", correo).execute()

        if len(response.data) == 0:
            flash("❌ El correo no está registrado. Por favor registrese.", "error")          
        else:
            flash("✅ Usuario encontrado correctamente.", "success")
        
        return redirect(url_for("login"))

    return render_template("MainPage.html")


def registro():

    if request.method == "POST":
        nombres = request.form.get("nombre")
        apellidos = request.form.get("apellido")
        password = request.form.get("password")
        password_confirmar = request.form.get("password_confirmar")

        




if __name__ == "__main__":
    app.run(debug=True,)