import streamlit as st
import requests
import pandas as pd
from datetime import date

API_URL = "http://127.0.0.1:5000"

st.set_page_config(page_title="Placement System", page_icon="🎓", layout="wide")


def api_get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=10)
        return r.json() if r.ok else None
    except requests.exceptions.RequestException:
        return None


def api_send(method, path, payload=None):
    try:
        r = requests.request(method, f"{API_URL}{path}", json=payload or {}, timeout=20)
        try:
            body = r.json()
        except ValueError:
            body = {}
        return r.status_code, body
    except requests.exceptions.RequestException:
        return None, {"error": "Could not reach the Flask server. Is it running?"}


def show_table(rows, empty_msg="No records found."):
    if rows is None:
        st.error("Could not load data. Is your Flask server running?")
    elif len(rows) == 0:
        st.info(empty_msg)
    else:
        st.dataframe(pd.DataFrame(rows), hide_index=True)


if "user" not in st.session_state:
    st.session_state.user = None


def login_page():
    st.title("🎓 Placement Management System")
    st.subheader("Please log in")

    role = st.radio("Login as", ["Student", "Admin"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        endpoint = "/login/student" if role == "Student" else "/login/admin"
        code, body = api_send("POST", endpoint, {"email": email, "password": password})
        if code == 200:
            user_id = body.get("student_id") if role == "Student" else body.get("admin_id")
            st.session_state.user = {"role": role, "id": user_id, "name": body["name"]}
            st.rerun()
        else:
            st.error(body.get("error", "Login failed"))

    st.caption("Demo: student ananya.rao@college.edu / test123  |  admin priya.sharma@college.edu / admin123")


def student_app(user):
    menu = st.sidebar.radio(
        "Navigate",
        ["My Profile", "Browse Drives", "Apply to a Drive", "My Applications", "My Prediction"],
    )

    if menu == "My Profile":
        st.header("My Profile")
        profile = api_get(f"/students/{user['id']}")
        if profile:
            c1, c2, c3 = st.columns(3)
            c1.metric("CGPA", profile["cgpa"])
            c2.metric("Backlogs", profile["backlogs"])
            c3.metric("Branch", profile["branch"])
            st.write(f"**Name:** {profile['name']}")
            st.write(f"**Email:** {profile['email']}  |  **Phone:** {profile['phone']}")
            st.write(f"**Skills:** {profile['skills']}")
            st.write(f"**Internships:** {profile['internships']}")
        else:
            st.error("Could not load profile.")

    elif menu == "Browse Drives":
        st.header("Upcoming Placement Drives")
        show_table(api_get("/drives"))

    elif menu == "Apply to a Drive":
        st.header("Apply to a Drive")
        drives = api_get("/drives")
        if not drives:
            st.error("Could not load drives.")
            return
        options = {
            d["drive_id"]: f"{d['company_name']} - {d['job_role']} ({d['location']}, {d['drive_date']})"
            for d in drives
        }
        drive_id = st.selectbox("Select a drive", list(options.keys()), format_func=lambda k: options[k])
        if st.button("Submit Application"):
            code, body = api_send("POST", "/applications", {
                "student_id": user["id"],
                "drive_id": drive_id,
                "applied_date": str(date.today()),
            })
            if code == 201:
                st.success(f"Application submitted! (ID {body['application_id']})")
            else:
                st.error(body.get("error", "Something went wrong"))

    elif menu == "My Applications":
        st.header("My Applications")
        show_table(api_get("/applications", {"student_id": user["id"]}), "You have not applied to any drive yet.")

    elif menu == "My Prediction":
        st.header("🔮 My Placement Prediction")
        if st.button("Generate / Refresh Prediction"):
            code, body = api_send("POST", f"/predict/{user['id']}")
            if code == 200:
                prob = body["placement_probability"]
                st.metric("Placement Probability", f"{prob * 100:.1f}%")
                st.progress(prob)
                if prob >= 0.75:
                    st.success("Strong profile. Keep applying!")
                elif prob >= 0.5:
                    st.warning("Decent chances. More internships and skills will help.")
                else:
                    st.error("Work on CGPA, backlogs, skills and internships to improve.")
            else:
                st.error(body.get("error", "Could not generate prediction"))


def admin_app(user):
    menu = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Students", "Companies", "Drives", "Applications",
         "Round Results", "Placements", "Predictions"],
    )

    if menu == "Dashboard":
        st.header("Dashboard")
        stats = api_get("/stats")
        if stats:
            c1, c2, c3 = st.columns(3)
            c1.metric("Students", stats["students"])
            c2.metric("Companies", stats["companies"])
            c3.metric("Drives", stats["drives"])
            c4, c5, c6 = st.columns(3)
            c4.metric("Applications", stats["applications"])
            c5.metric("Students Placed", stats["placed"])
            c6.metric("Average Package", f"₹{stats['avg_package']:,.0f}")
            if stats["applications_by_status"]:
                st.subheader("Applications by status")
                df = pd.DataFrame(stats["applications_by_status"]).set_index("status")
                st.bar_chart(df)
        else:
            st.error("Could not load stats. Is your Flask server running?")

    elif menu == "Students":
        st.header("Students")
        show_table(api_get("/students"))

    elif menu == "Companies":
        st.header("Companies")
        show_table(api_get("/companies"))
        st.subheader("Add a new company")
        with st.form("add_company"):
            name = st.text_input("Company name")
            sector = st.text_input("Sector")
            package = st.number_input("Package offered (₹)", min_value=0.0, step=50000.0)
            min_cgpa = st.number_input("Minimum CGPA", min_value=0.0, max_value=10.0, step=0.1, value=6.0)
            branches = st.text_input("Eligible branches (comma separated)", "CSE,IT")
            if st.form_submit_button("Add company"):
                code, body = api_send("POST", "/companies", {
                    "name": name, "sector": sector, "package_offered": package,
                    "min_cgpa_required": min_cgpa, "eligible_branches": branches,
                })
                if code == 201:
                    st.success("Company added. Refresh the page to see it in the table.")
                else:
                    st.error(body.get("error", "Failed"))

    elif menu == "Drives":
        st.header("Drives")
        show_table(api_get("/drives"))
        st.subheader("Create a new drive")
        companies = api_get("/companies") or []
        if companies:
            copts = {c["company_id"]: c["name"] for c in companies}
            with st.form("add_drive"):
                company_id = st.selectbox("Company", list(copts.keys()), format_func=lambda k: copts[k])
                drive_date = st.date_input("Drive date")
                job_role = st.text_input("Job role")
                location = st.text_input("Location")
                rounds = st.number_input("Number of rounds", min_value=1, max_value=10, value=2)
                if st.form_submit_button("Create drive"):
                    code, body = api_send("POST", "/drives", {
                        "company_id": company_id, "admin_id": user["id"],
                        "drive_date": str(drive_date), "job_role": job_role,
                        "location": location, "rounds": int(rounds),
                    })
                    if code == 201:
                        st.success("Drive created. Refresh the page to see it in the table.")
                    else:
                        st.error(body.get("error", "Failed"))

    elif menu == "Applications":
        st.header("Applications")
        apps = api_get("/applications")
        show_table(apps)
        if apps:
            st.subheader("Update application status")
            aopts = {a["application_id"]: f"#{a['application_id']} - {a['student_name']} → {a['company_name']} ({a['status']})" for a in apps}
            with st.form("update_status"):
                app_id = st.selectbox("Application", list(aopts.keys()), format_func=lambda k: aopts[k])
                new_status = st.selectbox("New status", ["Applied", "In Progress", "Rejected", "Selected"])
                if st.form_submit_button("Update"):
                    code, body = api_send("PUT", f"/applications/{app_id}/status", {"status": new_status})
                    if code == 200:
                        st.success(body["message"] + ". Refresh the page to see it in the table.")
                        if new_status == "Selected":
                            st.info("A placement record was created automatically.")
                    else:
                        st.error(body.get("error", "Failed"))

    elif menu == "Round Results":
        st.header("Round Results")
        show_table(api_get("/round_results"))
        apps = api_get("/applications") or []
        if apps:
            st.subheader("Add a round result")
            aopts = {a["application_id"]: f"#{a['application_id']} - {a['student_name']} ({a['job_role']})" for a in apps}
            with st.form("add_round"):
                app_id = st.selectbox("Application", list(aopts.keys()), format_func=lambda k: aopts[k])
                round_name = st.text_input("Round name", "Technical Interview")
                status = st.selectbox("Status", ["Pending", "Cleared", "Rejected"])
                remarks = st.text_input("Remarks")
                if st.form_submit_button("Add result"):
                    code, body = api_send("POST", "/round_results", {
                        "application_id": app_id, "round_name": round_name,
                        "status": status, "remarks": remarks,
                    })
                    if code == 201:
                        st.success("Round result added. Refresh the page to see it in the table.")
                    else:
                        st.error(body.get("error", "Failed"))

    elif menu == "Placements":
        st.header("Placement Records")
        show_table(api_get("/placements"))

    elif menu == "Predictions":
        st.header("🔮 Placement Predictions")
        if st.button("Generate predictions for ALL students"):
            code, body = api_send("POST", "/predict_all")
            if code == 200:
                st.success(body["message"])
            else:
                st.error(body.get("error", "Failed"))
        show_table(api_get("/predictions"))


user = st.session_state.user

if user is None:
    login_page()
else:
    st.sidebar.write(f"👤 **{user['name']}**")
    st.sidebar.caption(f"Logged in as {user['role']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()
    st.sidebar.divider()

    st.title("🎓 Placement Management System")
    if user["role"] == "Student":
        student_app(user)
    else:
        admin_app(user)
