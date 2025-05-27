import streamlit as st
import json
import os
from pathlib import Path

# ----- Config -----
ADMIN_EMAIL = "ahmadarshad01972@gmail.com"
ADMIN_PASS = "ahmad.24580"
DATA_DIR = Path("data")
USER_CREDENTIALS_FILE = "users.json"

# ----- Helper Functions -----
def load_users():
    with open(USER_CREDENTIALS_FILE, "r") as f:
        return json.load(f)

def validate_user(email, password):
    users = load_users()
    for user in users:
        if user["ucp_email"] == email and user["password"] == password:
            return user
    return None

def get_user_courses(roll):
    user_path = DATA_DIR / roll / "current"
    courses = {}
    for file in user_path.glob("*.json"):
        parts = file.stem.split("_")
        course_name = " ".join(parts[:-2])
        section = parts[-2] + "_" + parts[-1]
        if course_name not in courses:
            courses[course_name] = {}
        with open(file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            filtered = [row for row in raw_data if any(cell.strip() for cell in row if isinstance(cell, str))]
            if filtered:
                courses[course_name][section] = filtered
    return courses

def render_course_tabs(courses):
    tab_names = list(courses.keys())
    tabs = st.tabs(tab_names)
    for tab, cname in zip(tabs, tab_names):
        with tab:
            st.markdown(f"<div class='section-title'>📘 {cname}</div>", unsafe_allow_html=True)
            data = courses[cname]

            if "grade_book" in data:
                st.markdown("<h4 class='sub-section'>📝 Grade Book</h4>", unsafe_allow_html=True)
                for row in data["grade_book"]:
                    st.success(f"{row[0]} → {row[1]}")

            if "course_material" in data:
                st.markdown("<h4 class='sub-section'>📎 Course Material</h4>", unsafe_allow_html=True)
                for row in data["course_material"]:
                    st.info(" | ".join(row))

            if "announcements" in data:
                st.markdown("<h4 class='sub-section'>📢 Announcements</h4>", unsafe_allow_html=True)
                for row in data["announcements"]:
                    st.warning(" | ".join(row))

# ----- Page Config -----
st.set_page_config(page_title="UCP Dashboard", layout="wide")

# ----- Inject Custom CSS -----
st.markdown("""
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background-color: #f7f9fc;
        }
        .section-title {
            font-size: 28px;
            font-weight: bold;
            color: #3e64ff;
            margin: 20px 0 10px;
            animation: fadeInDown 0.8s ease;
        }
        .sub-section {
            color: #4a4a4a;
            font-weight: 600;
            margin: 10px 0;
        }
        .stTabs [data-baseweb="tab"] {
            transition: transform 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            transform: scale(1.03);
        }
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
""", unsafe_allow_html=True)

# ----- Session State -----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user = None
    st.session_state.notify_email = ""

# ----- Login Page -----
if not st.session_state.logged_in:
    st.title("🔐 UCP Portal Login")
    role = st.radio("Login as:", ["User", "Admin"])

    if role == "Admin":
        email = st.text_input("Admin Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if email == ADMIN_EMAIL and password == ADMIN_PASS:
                st.session_state.logged_in = True
                st.session_state.role = "admin"
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials.")
    else:
        ucp_email = st.text_input("UCP Email")
        ucp_pass = st.text_input("UCP Password", type="password")

        if st.button("Login"):
            user = validate_user(ucp_email, ucp_pass)
            if user:
                roll = ucp_email.split("@")[0]
                if (DATA_DIR / roll).exists():
                    st.session_state.logged_in = True
                    st.session_state.role = "user"
                    st.session_state.user = roll
                    st.session_state.notify_email = user["notify_email"]
                    st.rerun()
                else:
                    st.error("❌ No data found for this user.")
            else:
                st.error("❌ Invalid email or password.")
    st.stop()

# ----- Sidebar Navigation -----
st.sidebar.title("📊 Navigation")
tabs = st.sidebar.radio("Go to:", ["Dashboard", "About"])

# ----- Main Dashboard -----
if tabs == "Dashboard":
    if st.session_state.role == "admin":
        st.title("👨‍💼 Admin Dashboard")
        all_users = [d.name for d in DATA_DIR.iterdir() if d.is_dir()]
        selected_user = st.selectbox("Select student", all_users)
        st.markdown(f"### 📄 Viewing data for: `{selected_user}`")
        courses = get_user_courses(selected_user)
        render_course_tabs(courses)

    elif st.session_state.role == "user":
        roll = st.session_state.user
        st.title("🎓 Student Dashboard")
        st.markdown(f"👤 Roll Number: `{roll}`")
        st.markdown(f"📬 Notification Email: `{st.session_state.notify_email}`")
        courses = get_user_courses(roll)
        render_course_tabs(courses)

elif tabs == "About":
    st.title("🌟 About This Project")
    st.markdown("""
        <div style='background-color: #eef2ff; padding: 20px; border-left: 6px solid #3e64ff; border-radius: 10px;'>
            <h3 style='color:#3e64ff;'>🔐 End-to-End Encrypted Academic Portal</h3>
            <p>This secure platform empowers UCP students with real-time updates from Horizon Portal in a user-friendly interface.</p>
            <ul>
                <li>🔔 Daily update detection for grades, announcements & materials</li>
                <li>📧 Email notifications when changes are detected</li>
                <li>📁 Clean tabbed dashboard interface</li>
                <li>🎨 Smooth transitions and animations for better UX</li>
                <li>🔒 End-to-End Encrypted Login & Access</li>
            </ul>
            <p>Built with ❤️ using Python and Streamlit.</p>
            <p><b>Developer:</b> Ahmad Arshad</p>
            <p>
                🌐 <a href='https://github.com/ahmadarshad01972' target='_blank'>GitHub</a><br>
                💼 <a href='https://www.linkedin.com/in/ahmadarshad01972' target='_blank'>LinkedIn</a>
            </p>
        </div>
    """, unsafe_allow_html=True)
