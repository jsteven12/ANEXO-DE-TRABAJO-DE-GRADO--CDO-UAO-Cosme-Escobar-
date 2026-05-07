import mysql.connector

def get_db_connection():

    conexion = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="1234567890",
        database="registro",
        port="3306"
    )
    return conexion