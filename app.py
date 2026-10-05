from flask import Flask, jsonify, request
import mysql.connector
from dotenv import load_dotenv
import os
import joblib
import pandas as pd
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Load the trained ML model once when the server starts
model = joblib.load("placement_model.pkl")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@app.route("/")
def home():
    return "Placement System API is running!"

# ---------- STUDENTS ----------
@app.route("/students")
def get_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(students)

# ---------- COMPANIES ----------
@app.route("/companies")
def get_companies():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM company")
    companies = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(companies)

# ---------- DRIVES ----------
@app.route("/drives")
def get_drives():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM drive")
    drives = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(drives)

@app.route("/drives/<int:drive_id>")
def get_drive(drive_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM drive WHERE drive_id = %s", (drive_id,))
    drive = cursor.fetchone()
    cursor.close()
    conn.close()
    if drive is None:
        return jsonify({"error": "Drive not found"}), 404
    return jsonify(drive)

# ---------- APPLICATIONS (with JOIN) ----------
@app.route("/applications")
def get_applications():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            a.application_id,
            s.name AS student_name,
            d.job_role,
            d.location,
            a.status,
            a.applied_date
        FROM application a
        JOIN student s ON a.student_id = s.student_id
        JOIN drive d ON a.drive_id = d.drive_id
    """)
    applications = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(applications)

# ---------- CREATE NEW APPLICATION (POST) ----------
@app.route("/applications", methods=["POST"])
def create_application():
    data = request.get_json()
    student_id = data.get("student_id")
    drive_id = data.get("drive_id")
    applied_date = data.get("applied_date")

    if not all([student_id, drive_id, applied_date]):
        return jsonify({"error": "student_id, drive_id, and applied_date are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO application (student_id, drive_id, status, applied_date) VALUES (%s, %s, %s, %s)",
        (student_id, drive_id, "Applied", applied_date)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Application created", "application_id": new_id}), 201

# ---------- GENERATE PREDICTION FOR ONE STUDENT ----------
@app.route("/predict/<int:student_id>", methods=["POST"])
def predict_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()

    if student is None:
        cursor.close()
        conn.close()
        return jsonify({"error": "Student not found"}), 404

    # Build the feature row the model expects
    skills_count = len([s.strip() for s in (student["skills"] or "").split(",") if s.strip()])

    features = pd.DataFrame([{
        "cgpa": float(student["cgpa"]),
        "backlogs": int(student["backlogs"]),
        "internships": 1 if student["internships"] and student["internships"].lower() != "none" else 0,
        "skills_count": skills_count,
        "branch": student["branch"]
    }])

    probability = model.predict_proba(features)[0][1]  # probability of class "1" (placed)
    probability = round(float(probability), 4)

    # Upsert into prediction table (update if exists, insert if not)
    cursor.execute("SELECT prediction_id FROM prediction WHERE student_id = %s", (student_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE prediction SET placement_probability = %s, generated_on = %s WHERE student_id = %s",
            (probability, datetime.now(), student_id)
        )
    else:
        cursor.execute(
            "INSERT INTO prediction (student_id, placement_probability, generated_on) VALUES (%s, %s, %s)",
            (student_id, probability, datetime.now())
        )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "student_id": student_id,
        "name": student["name"],
        "placement_probability": probability
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
