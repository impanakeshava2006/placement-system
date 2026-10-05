import streamlit as st
import requests

API_URL = "http://127.0.0.1:5000"

st.set_page_config(page_title="Placement System", layout="wide")
st.title("🎓 Placement Management System")

menu = st.sidebar.selectbox(
    "Navigate",
    ["Students", "Companies", "Drives", "Applications", "Apply to a Drive","Predictions"]
)

# ---------- STUDENTS ----------
if menu == "Students":
    st.header("Students")
    response = requests.get(f"{API_URL}/students")
    if response.status_code == 200:
        st.dataframe(response.json(), use_container_width=True)
    else:
        st.error("Could not load students. Is your Flask server running?")

# ---------- COMPANIES ----------
elif menu == "Companies":
    st.header("Companies")
    response = requests.get(f"{API_URL}/companies")
    if response.status_code == 200:
        st.dataframe(response.json(), use_container_width=True)
    else:
        st.error("Could not load companies.")

# ---------- DRIVES ----------
elif menu == "Drives":
    st.header("Placement Drives")
    response = requests.get(f"{API_URL}/drives")
    if response.status_code == 200:
        st.dataframe(response.json(), use_container_width=True)
    else:
        st.error("Could not load drives.")

# ---------- APPLICATIONS ----------
elif menu == "Applications":
    st.header("Applications")
    response = requests.get(f"{API_URL}/applications")
    if response.status_code == 200:
        st.dataframe(response.json(), use_container_width=True)
    else:
        st.error("Could not load applications.")

# ---------- APPLY FORM ----------
elif menu == "Apply to a Drive":
    st.header("Submit a New Application")

    with st.form("apply_form"):
        student_id = st.number_input("Student ID", min_value=1, step=1)
        drive_id = st.number_input("Drive ID", min_value=1, step=1)
        applied_date = st.date_input("Applied Date")
        submitted = st.form_submit_button("Submit Application")

        if submitted:
            payload = {
                "student_id": int(student_id),
                "drive_id": int(drive_id),
                "applied_date": str(applied_date)
            }
            response = requests.post(f"{API_URL}/applications", json=payload)
            if response.status_code == 201:
                st.success(f"Application submitted! ID: {response.json()['application_id']}")
            else:
                st.error(f"Failed: {response.json().get('error', 'Unknown error')}")
# ---------- PREDICTIONS ----------
elif menu == "Predictions":
    st.header("🔮 Placement Prediction")

    student_id = st.number_input("Enter Student ID", min_value=1, step=1)

    if st.button("Generate Prediction"):
        response = requests.post(f"{API_URL}/predict/{int(student_id)}")
        if response.status_code == 200:
            result = response.json()
            st.success(f"{result['name']} — Placement Probability: {result['placement_probability'] * 100:.1f}%")
            st.progress(result['placement_probability'])
        elif response.status_code == 404:
            st.error("Student not found. Check the ID and try again.")
        else:
            st.error("Something went wrong generating the prediction.")
