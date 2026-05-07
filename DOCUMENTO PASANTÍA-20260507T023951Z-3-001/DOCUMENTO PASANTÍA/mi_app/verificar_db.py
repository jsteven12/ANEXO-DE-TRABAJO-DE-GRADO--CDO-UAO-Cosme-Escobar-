import sqlite3
import os

DB_FILE = "database.db"

def verificar_db():
    if not os.path.exists(DB_FILE):
        print(f"❌ El archivo '{DB_FILE}' no existe.")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"✅ Conexión a '{DB_FILE}' exitosa.")

        # Verificar tabla 'usuarios'
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios';")
        if cursor.fetchone():
            print("✅ Tabla 'usuarios' encontrada.")
        else:
            print("❌ Tabla 'usuarios' NO encontrada.")

        # Verificar tabla 'dispositivos'
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dispositivos';")
        if cursor.fetchone():
            print("✅ Tabla 'dispositivos' encontrada.")
        else:
            print("❌ Tabla 'dispositivos' NO encontrada.")

        # Opcional: mostrar algunos registros
        cursor.execute("SELECT * FROM usuarios LIMIT 5;")
        usuarios = cursor.fetchall()
        print(f"Usuarios (hasta 5 registros): {usuarios}")

        cursor.execute("SELECT * FROM dispositivos LIMIT 5;")
        dispositivos = cursor.fetchall()
        print(f"Dispositivos (hasta 5 registros): {dispositivos}")

        conn.close()

    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")

if __name__ == "__main__":
    verificar_db()
