import mysql.connector
import database as db



database = mysql.connector.connect(

    host='127.0.0.1',
    user='root',
    password='1234567890',
    database='registroclinico',
    port='3306'

)