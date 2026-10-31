from werkzeug.security import generate_password_hash
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)
cursor = conn.cursor()

cursor.execute("UPDATE student SET password_hash = %s", (generate_password_hash("test123"),))
cursor.execute("UPDATE admin SET password_hash = %s", (generate_password_hash("admin123"),))

conn.commit()
cursor.close()
conn.close()

print("Done. All students -> 'test123'   |   All admins -> 'admin123'")
