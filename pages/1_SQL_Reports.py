"""
SQL Reports page: shows the JOIN queries, stored procedures and triggers
running on the live database. Streamlit lists every file in the pages/
folder in the sidebar automatically.
"""
import pandas as pd
import requests
import streamlit as st

API = "http://127.0.0.1:5000"

st.title("SQL Reports: Joins, Procedures and Triggers")

user = st.session_state.get("user")
if not user:
    st.warning("Please log in as Admin from the main page first.")
    st.stop()
if isinstance(user, dict) and str(user.get("role", "admin")).strip().lower() != "admin":
    st.warning("This page is for the Admin role.")
    st.stop()


def get(path):
    try:
        r = requests.get(API + path, timeout=10)
        data = r.json()
        if r.status_code != 200:
            st.error(data.get("error", "Request failed"))
            return None
        return data
    except Exception as e:
        st.error(f"Could not reach the backend at {API}: {e}")
        return None


def post(path, payload):
    try:
        return requests.post(API + path, json=payload, timeout=10).json()
    except Exception as e:
        st.error(f"Could not reach the backend at {API}: {e}")
        return None


def show(rows, empty="No rows returned."):
    if rows is None:
        return
    if not rows:
        st.info(empty)
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


JOINS = {
    1: ("INNER JOIN of four tables",
        "Joins application, student, drive and company, so each application "
        "shows the student, company and role. Only rows that match in all four tables appear.",
        """SELECT a.application_id, s.name AS student_name, s.branch,
       c.name AS company_name, d.job_role, d.drive_date, a.status
FROM application a
JOIN student s ON s.student_id = a.student_id
JOIN drive   d ON d.drive_id   = a.drive_id
JOIN company c ON c.company_id = d.company_id
ORDER BY a.applied_date;"""),
    2: ("LEFT JOIN with GROUP BY and aggregate functions",
        "Starts from company, so companies with no applications are still listed "
        "(with 0). COUNT and SUM are aggregate functions; GROUP BY makes one row per company.",
        """SELECT c.name AS company_name,
       COUNT(DISTINCT d.drive_id)              AS total_drives,
       COUNT(a.application_id)                 AS total_applications,
       COALESCE(SUM(a.status = 'Selected'), 0) AS selected_count
FROM company c
LEFT JOIN drive d       ON d.company_id = c.company_id
LEFT JOIN application a ON a.drive_id   = d.drive_id
GROUP BY c.company_id, c.name
ORDER BY selected_count DESC, c.name;"""),
    3: ("Placed students with company and package",
        "Joins placement_record with student and company to show who was placed where, "
        "highest package first.",
        """SELECT s.student_id, s.name AS student_name, s.branch, s.cgpa,
       c.name AS company_name, p.package, p.date_of_offer
FROM placement_record p
JOIN student s ON s.student_id = p.student_id
JOIN company c ON c.company_id = p.company_id
ORDER BY p.package DESC;"""),
    4: ("LEFT JOIN with IS NULL",
        "Keeps every student and matches their applications; IS NULL leaves only the "
        "students who have not applied to any drive. An empty result means everyone has applied.",
        """SELECT s.student_id, s.name, s.branch, s.cgpa
FROM student s
LEFT JOIN application a ON a.student_id = s.student_id
WHERE a.application_id IS NULL
ORDER BY s.branch, s.name;"""),
}

tab_join, tab_proc, tab_trig = st.tabs(["JOIN queries", "Stored procedures", "Triggers"])

# ------------------------------------------------------------ JOIN queries
with tab_join:
    for n, (title, why, sql) in JOINS.items():
        st.subheader(f"Query {n}: {title}")
        st.caption(why)
        with st.expander("Show SQL"):
            st.code(sql, language="sql")
        if st.button(f"Run query {n}", key=f"join{n}"):
            show(get(f"/reports/join/{n}"))

# -------------------------------------------------------------- Procedures
with tab_proc:
    st.subheader("sp_branch_placement_report()  (no parameter)")
    st.caption("Branch-wise report using LEFT JOIN, GROUP BY, COUNT(DISTINCT) and AVG.")
    with st.expander("Show call"):
        st.code("CALL sp_branch_placement_report();", language="sql")
    if st.button("Run branch report"):
        rows = get("/reports/branch_report")
        show(rows)
        if rows:
            st.bar_chart(pd.DataFrame(rows).set_index("branch")["placement_percent"])

    st.divider()
    st.subheader("sp_student_applications(student_id)  (IN parameter)")
    st.caption("All applications of one student with company and drive details.")
    students = get("/students") or []
    options = {f"{s['student_id']} - {s['name']}": s["student_id"] for s in students}
    if options:
        choice = st.selectbox("Choose a student", list(options.keys()))
        sid = options[choice]
        with st.expander("Show call"):
            st.code(f"CALL sp_student_applications({sid});", language="sql")
        if st.button("Run student applications"):
            show(get(f"/reports/student_applications/{sid}"),
                 "This student has no applications.")

# ---------------------------------------------------------------- Triggers
with tab_trig:
    st.subheader("Trigger 1: trg_check_eligibility (BEFORE INSERT on application)")
    st.caption("This form inserts directly into the application table, so only the "
               "trigger can reject an ineligible student.")
    students = get("/students") or []
    drives = get("/drives") or []
    s_opts = {f"{s['student_id']} - {s['name']} ({s['branch']}, CGPA {s['cgpa']})": s["student_id"]
              for s in students}
    d_opts = {f"{d['drive_id']} - {d.get('company_name', d.get('name', 'Company'))} - {d.get('job_role', '')}":
              d["drive_id"] for d in drives}
    if s_opts and d_opts:
        s_pick = st.selectbox("Student", list(s_opts.keys()), key="trig_s")
        d_pick = st.selectbox("Drive", list(d_opts.keys()), key="trig_d")
        if st.button("Try to apply"):
            res = post("/reports/try_apply",
                       {"student_id": s_opts[s_pick], "drive_id": d_opts[d_pick]})
            if res:
                if res.get("accepted"):
                    st.success(res["message"])
                else:
                    st.error(f"Blocked by trigger: {res['message']}")
    with st.expander("Show trigger code"):
        st.code("""CREATE TRIGGER trg_check_eligibility
BEFORE INSERT ON application
FOR EACH ROW
BEGIN
  -- reads student CGPA/branch and the company's rules, then
  -- SIGNAL SQLSTATE '45000' if CGPA is too low or branch is not allowed
END;""", language="sql")

    st.divider()
    st.subheader("Trigger 2: trg_application_selected (AFTER UPDATE on application)")
    st.write("To show it: open the **Applications** page, change an application that is "
             "not yet Selected to **Selected**, then come back here and run Query 3 "
             "(or open the **Placements** page). A placement record for that student "
             "appears without any extra step, because the trigger created it.")
    with st.expander("Show trigger code"):
        st.code("""CREATE TRIGGER trg_application_selected
AFTER UPDATE ON application
FOR EACH ROW
BEGIN
  IF NEW.status = 'Selected' AND OLD.status <> 'Selected' THEN
    INSERT IGNORE INTO placement_record (student_id, company_id, package, date_of_offer)
    SELECT NEW.student_id, d.company_id, c.package_offered, CURDATE()
    FROM drive d JOIN company c ON c.company_id = d.company_id
    WHERE d.drive_id = NEW.drive_id;
  END IF;
END;""", language="sql")
    if st.button("Show current placement records (Query 3)"):
        show(get("/reports/join/3"))
