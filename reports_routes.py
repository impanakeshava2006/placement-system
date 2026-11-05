"""
SQL report routes for the Placement Management System.
Adds endpoints that run the JOIN queries, call the stored procedures and
demonstrate the eligibility trigger, so the Streamlit frontend can show them.

Hook it into app.py with two lines (see the steps given with this file):
    from reports_routes import register_reports
    register_reports(app, get_db_connection, clean)
"""
from flask import jsonify, request
import mysql.connector

JOIN_QUERIES = {
    1: """
        SELECT a.application_id, s.name AS student_name, s.branch,
               c.name AS company_name, d.job_role, d.drive_date, a.status
        FROM application a
        JOIN student s ON s.student_id = a.student_id
        JOIN drive   d ON d.drive_id   = a.drive_id
        JOIN company c ON c.company_id = d.company_id
        ORDER BY a.applied_date
    """,
    2: """
        SELECT c.name AS company_name,
               COUNT(DISTINCT d.drive_id)              AS total_drives,
               COUNT(a.application_id)                 AS total_applications,
               COALESCE(SUM(a.status = 'Selected'), 0) AS selected_count
        FROM company c
        LEFT JOIN drive d       ON d.company_id = c.company_id
        LEFT JOIN application a ON a.drive_id   = d.drive_id
        GROUP BY c.company_id, c.name
        ORDER BY selected_count DESC, c.name
    """,
    3: """
        SELECT s.student_id, s.name AS student_name, s.branch, s.cgpa,
               c.name AS company_name, p.package, p.date_of_offer
        FROM placement_record p
        JOIN student s ON s.student_id = p.student_id
        JOIN company c ON c.company_id = p.company_id
        ORDER BY p.package DESC
    """,
    4: """
        SELECT s.student_id, s.name, s.branch, s.cgpa
        FROM student s
        LEFT JOIN application a ON a.student_id = s.student_id
        WHERE a.application_id IS NULL
        ORDER BY s.branch, s.name
    """,
}


def register_reports(app, get_db_connection, clean):
    def run_query(sql, params=()):
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(sql, params)
            return [{k: clean(v) for k, v in row.items()} for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def run_procedure(name, args=()):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.callproc(name, args)
            rows = []
            for result in cur.stored_results():
                cols = [d[0] for d in result.description]
                rows = [{c: clean(v) for c, v in zip(cols, r)} for r in result.fetchall()]
            return rows
        finally:
            cur.close()
            conn.close()

    @app.route("/reports/join/<int:n>")
    def report_join(n):
        if n not in JOIN_QUERIES:
            return jsonify({"error": "Unknown join query"}), 404
        try:
            return jsonify(run_query(JOIN_QUERIES[n]))
        except mysql.connector.Error as e:
            return jsonify({"error": e.msg}), 500

    @app.route("/reports/branch_report")
    def report_branch():
        try:
            return jsonify(run_procedure("sp_branch_placement_report"))
        except mysql.connector.Error as e:
            return jsonify({"error": e.msg}), 500

    @app.route("/reports/student_applications/<int:student_id>")
    def report_student_applications(student_id):
        try:
            return jsonify(run_procedure("sp_student_applications", (student_id,)))
        except mysql.connector.Error as e:
            return jsonify({"error": e.msg}), 500

    @app.route("/reports/try_apply", methods=["POST"])
    def report_try_apply():
        """Inserts straight into the application table (no Python checks), so
        the BEFORE INSERT trigger trg_check_eligibility is the only thing that
        can stop an ineligible student."""
        data = request.get_json(silent=True) or {}
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO application (student_id, drive_id, status, applied_date) "
                "VALUES (%s, %s, 'Applied', CURDATE())",
                (data.get("student_id"), data.get("drive_id")),
            )
            conn.commit()
            return jsonify({"accepted": True,
                            "message": "Application inserted: the student is eligible."}), 201
        except mysql.connector.Error as e:
            conn.rollback()
            if e.errno == 1644:      # raised by SIGNAL in the trigger
                return jsonify({"accepted": False, "message": e.msg}), 200
            return jsonify({"accepted": False, "message": e.msg}), 200
        finally:
            cur.close()
            conn.close()
