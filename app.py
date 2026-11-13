import streamlit as st
import pandas as pd
import json
import os

# --- PERSISTENT DATABASE SETUP ---
DATA_FILE = "election_data.json"

def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return {"users": {}}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if "users" not in data:
                data["users"] = {}
            return data
    except json.JSONDecodeError:
        return {"users": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# --- PAGE CONFIG ---
st.set_page_config(page_title="College Election Manager", layout="wide", page_icon="🗳️")

# --- AUTHENTICATION SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- LOGIN / AUTHENTICATION SCREEN ---
if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; color: #2E4053;'>COLLEGE UNION ELECTION PORTAL</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #5D6D7E;'>Multi-Institution Election Management System</h4><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Login", "📝 Register College", "🔄 Forgot Password"])
        
        with auth_tab1:
            st.subheader("Institution Login")
            with st.form("login_form"):
                u_input = st.text_input("Username")
                p_input = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Login", type="primary")
                
                if login_btn:
                    users_db = db.get("users", {})
                    if u_input in users_db and users_db[u_input]["password"] == p_input:
                        st.session_state.authenticated = True
                        st.session_state.username = u_input
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                        
        with auth_tab2:
            st.subheader("Register New College Portal")
            with st.form("signup_form"):
                new_user = st.text_input("Choose Username (e.g., st_thomas_pala)")
                new_pass = st.text_input("Choose Password", type="password")
                c_name = st.text_input("Official College Name", value="ST. THOMAS COLLEGE")
                hint = st.text_input("Password Recovery Hint")
                signup_btn = st.form_submit_button("Create Institution Account")
                
                if signup_btn:
                    if not new_user or not new_pass or not c_name:
                        st.warning("Please fill in all mandatory fields.")
                    elif new_user in db["users"]:
                        st.error("Username already taken.")
                    else:
                        db["users"][new_user] = {
                            "password": new_pass,
                            "recovery_hint": hint,
                            "college_name": c_name.upper(),
                            "logo_path": ""
                        }
                        save_data(db)
                        st.success("Account created successfully! Switch to the Login tab.")
                        
        with auth_tab3:
            st.subheader("Password Recovery")
            with st.form("forgot_form"):
                f_user = st.text_input("Username")
                f_hint = st.text_input("Recovery Hint Answer")
                recover_btn = st.form_submit_button("Recover Password")
                
                if recover_btn:
                    users_db = db.get("users", {})
                    if f_user in users_db:
                        if users_db[f_user]["recovery_hint"].strip().lower() == f_hint.strip().lower():
                            st.info(f"Your password is: **{users_db[f_user]['password']}**")
                        else:
                            st.error("Incorrect recovery hint answer.")
                    else:
                        st.error("Username not found.")
                        
    st.stop()

# --- CURRENT USER PROFILE SETUP ---
current_user = st.session_state.username
user_profile = db["users"][current_user]

if current_user not in db:
    db[current_user] = {}
    save_data(db)

college_data = db[current_user]

# --- SIDEBAR CONTROLS ---
st.sidebar.write(f"👤 Logged in as: **{current_user}**")
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🏛️ Institution Settings")

updated_college_name = st.sidebar.text_input("College Name", value=user_profile.get("college_name", "MY COLLEGE"))
if updated_college_name != user_profile.get("college_name"):
    user_profile["college_name"] = updated_college_name.upper()
    save_data(db)

uploaded_logo = st.sidebar.file_uploader("Upload College Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
if uploaded_logo is not None:
    os.makedirs("logos", exist_ok=True)
    logo_filename = f"logos/{current_user}_logo.png"
    with open(logo_filename, "wb") as f:
        f.write(uploaded_logo.getbuffer())
    user_profile["logo_path"] = logo_filename
    save_data(db)
    st.sidebar.success("Logo updated!")

st.sidebar.markdown("---")
st.sidebar.header("Global Election Settings")
election_year = st.sidebar.text_input("Election Year", value="2026-27")
poll_date = st.sidebar.text_input("Date of Poll", value="")

if election_year not in college_data:
    college_data[election_year] = {
        "poll_date": poll_date,
        "programs": {
            "UG": ["B. Sc Mathematics", "B. Sc Physics", "B. Com", "BBA", "BCA"],
            "PG": ["M. Sc Mathematics", "M. Com", "M. A English"]
        },
        "class_reps": {},
        "main_posts_config": [
            {"post_name": "The Chairperson", "seats": 1},
            {"post_name": "General Secretary", "seats": 1},
            {"post_name": "University Union Councillor (UUC)", "seats": 2}
        ],
        "main_post_candidates": {}
    }
    save_data(db)
else:
    college_data[election_year]["poll_date"] = poll_date
    save_data(db)

st.sidebar.markdown("---")
st.sidebar.header("Program List Manager")
st.sidebar.write("Edit college programs below (one per line):")

ug_text = "\n".join(college_data[election_year]["programs"].get("UG", []))
pg_text = "\n".join(college_data[election_year]["programs"].get("PG", []))

ug_input = st.sidebar.text_area("UG Programs", value=ug_text, height=150)
pg_input = st.sidebar.text_area("PG Programs", value=pg_text, height=150)

college_data[election_year]["programs"]["UG"] = [p.strip() for p in ug_input.split('\n') if p.strip()]
college_data[election_year]["programs"]["PG"] = [p.strip() for p in pg_input.split('\n') if p.strip()]
save_data(db)

# --- HOME DASHBOARD VIEW ---
def home_page():
    col_logo, col_title = st.columns([1, 6])
    with col_logo:
        logo_path = user_profile.get("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            st.image(logo_path, width=120)
        else:
            st.markdown("<div style='height: 100px; width: 100px; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center;'><small>No Logo</small></div>", unsafe_allow_html=True)
            
    with col_title:
        st.markdown(f"<h1 style='color: #2E4053; margin-top: -15px;'>{user_profile.get('college_name')}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color: #5D6D7E; margin-top: -10px;'>College Union Election Management ({election_year})</h3>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Institution Election Dashboard")
    st.write(f"Welcome back! You are viewing secure, isolated election data for **{user_profile.get('college_name')}** ({election_year}).")

    year_data = college_data[election_year]
    class_reps_data = year_data.get("class_reps", {})

    total_classes = len(class_reps_data)
    total_noms = sum(len(c["candidates"]) for c in class_reps_data.values())
    total_withdrawn = sum(len([c for c in c["candidates"] if c.get("status") == "Withdrawn"]) for c_data in class_reps_data.values() for c in c_data["candidates"])
    total_active = total_noms - total_withdrawn

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Configured Classes", total_classes)
    m2.metric("Total Nominations", total_noms)
    m3.metric("Withdrawn Candidates", total_withdrawn)
    m4.metric("Active Contestants", total_active)

    st.markdown("<br><br><hr>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #808B96; font-size: 14px;'>Developed by Francis Thomas</p>", unsafe_allow_html=True)

# --- NAVIGATION STRUCTURE ---
pg = st.navigation({
    "Overview": [
        st.Page(home_page, title="Dashboard Home", icon="📊")
    ],
    "Election Workflow": [
        st.Page("pages/1_Class_Rep_Nominations.py", title="1. Class Rep Nominations", icon="📝"),
        st.Page("pages/2_Withdrawals_&_Final.py", title="2. Scrutiny & Withdrawals", icon="🛑"),
        st.Page("pages/3_Ballot_Generation.py", title="3. Ballot Generation", icon="🖨️"),
        st.Page("pages/4_Class_Rep_Results.py", title="4. Class Rep Results", icon="🏆"),
        st.Page("pages/5_Main_Post_Config.py", title="5. Main Post Config", icon="⚙️"),
        st.Page("pages/6_Main_Post_Elections.py", title="6. Main Post Elections", icon="🗳️")
    ]
})

pg.run()
