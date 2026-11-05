from flask import Flask, jsonify, request
import mysql.connector
from dotenv import load_dotenv
import os
import joblib
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
from werkzeug.security import check_password_hash

load_dotenv()

app = Flask(__name__)

# Load the trained ML model once when the server starts
model = joblib.load("placement_model.pkl")

# Columns we are happy to expose (never expose password_hash)
STUDENT_COLS = "student_id, name, branch, cgpa, backlogs, skills, internships, email, phone"
VALID_STATUSES = ["Applied", "In Progress", "Rejected", "Selected"]


# ------------------------------------------------------------
# Database helpers
# ------------------------------------------------------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def clean(value):
    """Make MySQL values JSON-friendly (dates -> text, Decimal -> float)."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def fetch_all(sql, params=()):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{k: clean(v) for k, v in row.items()} for row in rows]


def fetch_one(sql, params=()):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    """Run an INSERT/UPDATE and return the new row id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return new_id


def db_error(e):
    """Turn a MySQL error into a clear JSON response."""
    if e.errno == 1062:
        return jsonify({"error": "That record already exists"}), 409
    if e.errno == 1452:
        return jsonify({"error": "Invalid reference: a related id does not exist"}), 400
    return jsonify({"error": f"Database error: {e.msg}"}), 500


@app.route("/")
def home():
    return "Placement System API is running!"


# ------------------------------------------------------------
# STUDENTS
# ------------------------------------------------------------
@app.route("/students")
def get_students():
    return jsonify(fetch_all(f"SELECT {STUDENT_COLS} FROM student ORDER BY student_id"))


@app.route("/students/<int:student_id>")
def get_student(student_id):
    student = fetch_one(f"SELECT {STUDENT_COLS} FROM student WHERE student_id = %s", (student_id,))
    if student is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student)


# ------------------------------------------------------------
# COMPANIES
# ------------------------------------------------------------
@app.route("/companies")
def get_companies():
    return jsonify(fetch_all("SELECT * FROM company ORDER BY company_id"))


@app.route("/companies", methods=["POST"])
def create_company():
    d = request.get_json() or {}
    if not d.get("name"):
        return jsonify({"error": "Company name is required"}), 400
    try:
        new_id = execute(
            "INSERT INTO company (name, sector, package_offered, min_cgpa_required, eligible_branches) "
            "VALUES (%s, %s, %s, %s, %s)",
            (d.get("name"), d.get("sector"), d.get("package_offered"),
             d.get("min_cgpa_required"), d.get("eligible_branches")),
        )
    except mysql.connector.Error as e:
        return db_error(e)
    return jsonify({"message": "Company created", "company_id": new_id}), 201


# ------------------------------------------------------------
# DRIVES
# ------------------------------------------------------------
DRIVE_SELECT = """
    SELECT d.drive_id, d.company_id, c.name AS company_name, d.admin_id,
           d.drive_date, d.job_role, d.location, d.rounds,
           c.package_offered, c.min_cgpa_required, c.eligible_branches
    FROM drive d
    JOIN company c ON d.company_id = c.company_id
"""


@app.route("/drives")
def get_drives():
    return jsonify(fetch_all(DRIVE_SELECT + " ORDER BY d.drive_date"))


@app.route("/drives/<int:drive_id>")
def get_drive(drive_id):
    drive = fetch_one(DRIVE_SELECT + " WHERE d.drive_id = %s", (drive_id,))
    if drive is None:
        return jsonify({"error": "Drive not found"}), 404
    return jsonify(drive)


@app.route("/drives", methods=["POST"])
def create_drive():
    d = request.get_json() or {}
    required = ["company_id", "admin_id", "drive_date", "job_role"]
    if not all(d.get(k) for k in required):
        return jsonify({"error": "company_id, admin_id, drive_date and job_role are required"}), 400
    try:
        new_id = execute(
            "INSERT INTO drive (company_id, admin_id, drive_date, job_role, location, rounds) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (d["company_id"], d["admin_id"], d["drive_date"], d["job_role"],
             d.get("location"), d.get("rounds", 1)),
        )
    except mysql.connector.Error as e:
        return db_error(e)
    return jsonify({"message": "Drive created", "drive_id": new_id}), 201


# ------------------------------------------------------------
# APPLICATIONS
# ------------------------------------------------------------
APPLICATION_SELECT = """
    SELECT a.application_id, a.student_id, s.name AS student_name,
           c.name AS company_name, d.job_role, d.location,
           a.status, a.applied_date
    FROM application a
    JOIN student s ON a.student_id = s.student_id
    JOIN drive d ON a.drive_id = d.drive_id
    JOIN company c ON d.company_id = c.company_id
"""


@app.route("/applications")
def get_applications():
    student_id = request.args.get("student_id")
    if student_id:
        rows = fetch_all(APPLICATION_SELECT + " WHERE a.student_id = %s ORDER BY a.application_id", (student_id,))
    else:
        rows = fetch_all(APPLICATION_SELECT + " ORDER BY a.application_id")
    return jsonify(rows)


@app.route("/applications", methods=["POST"])
def create_application():
    d = request.get_json() or {}
    student_id = d.get("student_id")
    drive_id = d.get("drive_id")
    applied_date = d.get("applied_date")

    if not all([student_id, drive_id, applied_date]):
        return jsonify({"error": "student_id, drive_id, and applied_date are required"}), 400

    student = fetch_one("SELECT cgpa, branch FROM student WHERE student_id = %s", (student_id,))
    drive = fetch_one(DRIVE_SELECT + " WHERE d.drive_id = %s", (drive_id,))
    if student is None:
        return jsonify({"error": "Student not found"}), 404
    if drive is None:
        return jsonify({"error": "Drive not found"}), 404

    # Eligibility checks (cgpa + branch)
    min_cgpa = drive.get("min_cgpa_required")
    if min_cgpa is not None and student["cgpa"] < min_cgpa:
        return jsonify({"error": f"Not eligible: minimum CGPA required is {min_cgpa}"}), 403

    branches = [b.strip().lower() for b in (drive.get("eligible_branches") or "").split(",") if b.strip()]
    if branches and student["branch"].lower() not in branches:
        return jsonify({"error": f"Not eligible: open only to {drive['eligible_branches']}"}), 403

    try:
        new_id = execute(
            "INSERT INTO application (student_id, drive_id, status, applied_date) VALUES (%s, %s, %s, %s)",
            (student_id, drive_id, "Applied", applied_date),
        )
    except mysql.connector.Error as e:
        if e.errno == 1062:
            return jsonify({"error": "You have already applied to this drive"}), 409
        return db_error(e)
    return jsonify({"message": "Application created", "application_id": new_id}), 201


@app.route("/applications/<int:application_id>/status", methods=["PUT"])
def update_application_status(application_id):
    d = request.get_json() or {}
    status = d.get("status")
    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {VALID_STATUSES}"}), 400

    app_row = fetch_one("SELECT student_id, drive_id FROM application WHERE application_id = %s", (application_id,))
    if app_row is None:
        return jsonify({"error": "Application not found"}), 404

    execute("UPDATE application SET status = %s WHERE application_id = %s", (status, application_id))

    # If selected, automatically create a placement record (one per student)
    if status == "Selected":
        info = fetch_one(
            "SELECT d.company_id, c.package_offered FROM drive d "
            "JOIN company c ON d.company_id = c.company_id WHERE d.drive_id = %s",
            (app_row["drive_id"],),
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT IGNORE INTO placement_record (student_id, company_id, package, date_of_offer) "
            "VALUES (%s, %s, %s, %s)",
            (app_row["student_id"], info["company_id"], info["package_offered"], date.today()),
        )
        conn.commit()
        cursor.close()
        conn.close()

    return jsonify({"message": f"Application {application_id} marked as {status}"})


# ------------------------------------------------------------
# ROUND RESULTS
# ------------------------------------------------------------
@app.route("/round_results")
def get_round_results():
    application_id = request.args.get("application_id")
    sql = """
        SELECT r.application_id, s.name AS student_name, d.job_role,
               r.round_name, r.status, r.remarks
        FROM round_result r
        JOIN application a ON r.application_id = a.application_id
        JOIN student s ON a.student_id = s.student_id
        JOIN drive d ON a.drive_id = d.drive_id
    """
    if application_id:
        rows = fetch_all(sql + " WHERE r.application_id = %s", (application_id,))
    else:
        rows = fetch_all(sql + " ORDER BY r.application_id, r.round_name")
    return jsonify(rows)


@app.route("/round_results", methods=["POST"])
def create_round_result():
    d = request.get_json() or {}
    if not d.get("application_id") or not d.get("round_name"):
        return jsonify({"error": "application_id and round_name are required"}), 400
    try:
        execute(
            "INSERT INTO round_result (application_id, round_name, status, remarks) VALUES (%s, %s, %s, %s)",
            (d["application_id"], d["round_name"], d.get("status", "Pending"), d.get("remarks", "")),
        )
    except mysql.connector.Error as e:
        return db_error(e)
    return jsonify({"message": "Round result added"}), 201


# ------------------------------------------------------------
# PLACEMENTS + PREDICTIONS (read)
# ------------------------------------------------------------
@app.route("/placements")
def get_placements():
    return jsonify(fetch_all("""
        SELECT p.record_id, s.name AS student_name, s.branch,
               c.name AS company_name, p.package, p.date_of_offer
        FROM placement_record p
        JOIN student s ON p.student_id = s.student_id
        JOIN company c ON p.company_id = c.company_id
        ORDER BY p.record_id
    """))


@app.route("/predictions")
def get_predictions():
    return jsonify(fetch_all("""
        SELECT pr.prediction_id, s.name AS student_name, s.branch, s.cgpa,
               pr.placement_probability, pr.generated_on
        FROM prediction pr
        JOIN student s ON pr.student_id = s.student_id
        ORDER BY pr.placement_probability DESC
    """))


# ------------------------------------------------------------
# ML PREDICTION
# ------------------------------------------------------------
def predict_for_student(student_id):
    student = fetch_one(f"SELECT {STUDENT_COLS} FROM student WHERE student_id = %s", (student_id,))
    if student is None:
        return None

    skills_count = len([s.strip() for s in (student["skills"] or "").split(",") if s.strip()])
    has_internship = 1 if student["internships"] and student["internships"].strip().lower() != "none" else 0

    features = pd.DataFrame([{
        "cgpa": float(student["cgpa"]),
        "backlogs": int(student["backlogs"] or 0),
        "internships": has_internship,
        "skills_count": skills_count,
        "branch": student["branch"],
    }])

    probability = round(float(model.predict_proba(features)[0][1]), 4)

    existing = fetch_one("SELECT prediction_id FROM prediction WHERE student_id = %s", (student_id,))
    if existing:
        execute(
            "UPDATE prediction SET placement_probability = %s, generated_on = %s WHERE student_id = %s",
            (probability, datetime.now(), student_id),
        )
    else:
        execute(
            "INSERT INTO prediction (student_id, placement_probability, generated_on) VALUES (%s, %s, %s)",
            (student_id, probability, datetime.now()),
        )

    return {"student_id": student_id, "name": student["name"], "placement_probability": probability}


@app.route("/predict/<int:student_id>", methods=["POST"])
def predict_student(student_id):
    result = predict_for_student(student_id)
    if result is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(result)


@app.route("/predict_all", methods=["POST"])
def predict_all():
    ids = [row["student_id"] for row in fetch_all("SELECT student_id FROM student")]
    results = [predict_for_student(i) for i in ids]
    return jsonify({"message": f"Generated {len(results)} predictions", "results": results})


# ------------------------------------------------------------
# DASHBOARD STATS
# ------------------------------------------------------------
@app.route("/stats")
def get_stats():
    counts = fetch_one("""
        SELECT
            (SELECT COUNT(*) FROM student) AS students,
            (SELECT COUNT(*) FROM company) AS companies,
            (SELECT COUNT(*) FROM drive) AS drives,
            (SELECT COUNT(*) FROM application) AS applications,
            (SELECT COUNT(*) FROM placement_record) AS placed,
            (SELECT COALESCE(AVG(package), 0) FROM placement_record) AS avg_package
    """)
    by_status = fetch_all("SELECT status, COUNT(*) AS count FROM application GROUP BY status")
    counts["applications_by_status"] = by_status
    return jsonify(counts)


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------
def do_login(table, id_col):
    d = request.get_json() or {}
    email = d.get("email")
    password = d.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = fetch_one(f"SELECT * FROM {table} WHERE email = %s", (email,))
    if user and check_password_hash(user["password_hash"], password):
        return jsonify({"message": "Login successful", id_col: user[id_col], "name": user["name"]}), 200
    return jsonify({"error": "Invalid email or password"}), 401


@app.route("/login/student", methods=["POST"])
def login_student():
    return do_login("student", "student_id")


@app.route("/login/admin", methods=["POST"])
def login_admin():
    return do_login("admin", "admin_id")


from reports_routes import register_reports
register_reports(app, get_db_connection, clean)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
