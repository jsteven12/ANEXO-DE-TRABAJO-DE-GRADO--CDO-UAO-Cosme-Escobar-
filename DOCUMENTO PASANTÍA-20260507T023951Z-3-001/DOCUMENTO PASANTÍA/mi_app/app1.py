from flask import Flask, render_template, request, redirect, url_for, flash
import databaseuser as db


app = Flask(__name__)

app.secret_key = "1234567890"

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["usuario"]  # coincide con name="username"
        password = request.form["pasword"]  # coincide con name="password"

        conn = db.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM new_table WHERE usuario=%s AND pasword=%s", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            flash("✅ Inicio de sesión exitoso", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("⚠ Usuario no encontrado, por favor regístrese.", "danger")
            return redirect(url_for("login")) 
        
    return render_template("MainPage.html")


if __name__ == "__main__":
    app.run(debug=True)