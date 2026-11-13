import streamlit as st
import pandas as pd
import json
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import db_utils

# --- SUPER ADMIN CREDENTIALS ---
SUPERADMIN_USER = "superadmin"
SUPERADMIN_PASS = "superadmin123"

# --- DEFAULT PROGRAM LISTS ---
DEFAULT_UG = [
    "B. Sc Mathematics", "B. Sc Physics", "B. Sc Chemistry", "B. Sc Botany", 
    "B. Sc Zoology", "B. A English", "B. A Economics", "B. A History", 
    "B. Com F&T", "B. Com FM", "B. Com LM", "B. Com Accounting", 
    "B. Voc Agriculture Technology", "BCA", "BBA"
]
DEFAULT_PG = [
    "M. Sc Mathematics", "M. Sc Physics", "M. Sc Chemistry", "M. Sc Botany", 
    "M. Sc Zoology", "M. A English", "M. A Economics", "M. A History", "M. Com"
]

# --- INITIALIZE DATABASE ---
db = db_utils.load_data()

# Auto-repair missing keys for legacy databases on Streamlit Cloud
if "colleges" not in db: db["colleges"] = {}
if "users" not in db: db["users"] = {}

# --- PAGE CONFIG ---
st.set_page_config(page_title="College Election Manager", layout="wide", page_icon="🗳️")

# --- AUTHENTICATION SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "otp_sent_to" not in st.session_state:
    st.session_state.otp_sent_to = None

def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def send_reset_email(recipient_email, otp_code, username):
    """Sends an OTP to the user's email using Streamlit Secrets."""
    try:
        sender = st.secrets["email_sender"]
        password = st.secrets["email_password"]
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient_email
        msg['Subject'] = "College Election Portal - Password Reset"
        
        body = f"""
        Hello {username},
        
        You requested a password reset for your College Union Election Portal admin account.
        
        Your 6-digit recovery code is: {otp_code}
        
        Enter this code in the app to set a new password. If you did not request this, please ignore this email.
        """
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        text = msg.as_string()
        server.sendmail(sender, recipient_email, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email. Please check your Streamlit Secrets. Error: {e}")
        return False

# ==========================================
# 🔐 LOGIN & REGISTRATION PORTAL 
# ==========================================
if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; color: #2E4053;'>COLLEGE UNION ELECTION PORTAL</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #5D6D7E;'>Multi-Institution Election Management System</h4><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["🔑 Login", "🏛️ Register New College", "🔄 Forgot Password"])
        
        # --- TAB 1: LOGIN ---
        with auth_tab1:
            st.subheader("Institution & Admin Login")
            with st.form("login_form"):
                u_input = st.text_input("Username")
                p_input = st.text_input("Password", type="password")
                if st.form_submit_button("Login", type="primary"):
                    if u_input == SUPERADMIN_USER and p_input == SUPERADMIN_PASS:
                        st.session_state.authenticated = True
                        st.session_state.username = u_input
                        st.success("Super Admin Login successful!")
                        st.rerun()
                    elif u_input in db["users"] and db["users"][u_input]["password"] == p_input:
                        st.session_state.authenticated = True
                        st.session_state.username = u_input
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                        
        # --- TAB 2: REGISTER NEW COLLEGE ---
        with auth_tab2:
            st.subheader("Register Institution")
            st.write("Create the master account for your college.")
            with st.form("signup_form"):
                c_name = st.text_input("Official College Name", value="ST. THOMAS COLLEGE")
                e_mode = st.radio("Election Mode", ["Parliamentary (Indirect - Class Reps First)", "Presidential (Direct - Main Posts Only)"])
                st.markdown("---")
                new_user = st.text_input("Choose Admin Username")
                admin_email = st.text_input("Admin Email Address (For Password Recovery)")
                new_pass = st.text_input("Choose Password", type="password")
                
                if st.form_submit_button("Create Institution Account"):
                    if "colleges" not in db: db["colleges"] = {}
                    if "users" not in db: db["users"] = {}
                        
                    if not new_user or not new_pass or not c_name or not admin_email:
                        st.warning("Please fill in all fields.")
                    elif new_user == SUPERADMIN_USER or new_user in db["users"]:
                        st.error("Username already taken. Please choose another.")
                    else:
                        college_id = f"college_{generate_id().lower()}"
                        mode_val = "Parliamentary" if "Parliamentary" in e_mode else "Presidential"
                        
                        db["colleges"][college_id] = {
                            "college_name": c_name.upper(),
                            "election_mode": mode_val,
                            "logo_path": "",
                            "election_years": {}
                        }
                        
                        db["users"][new_user] = {
                            "password": new_pass,
                            "email": admin_email.lower(),
                            "college_id": college_id,
                            "role": "Admin",
                            "reset_otp": ""
                        }
                        db_utils.save_data(db)
                        st.success("College registered successfully! Switch to the Login tab.")

        # --- TAB 3: FORGOT PASSWORD ---
        with auth_tab3:
            st.subheader("Reset Password")
            
            if not st.session_state.otp_sent_to:
                with st.form("request_reset_form"):
                    reset_user = st.text_input("Enter your Admin Username")
                    if st.form_submit_button("Send Recovery Code"):
                        if reset_user in db["users"] and "email" in db["users"][reset_user]:
                            # Generate random 6-digit OTP
                            otp = str(random.randint(100000, 999999))
                            db["users"][reset_user]["reset_otp"] = otp
                            db_utils.save_data(db)
                            
                            # Send Email
                            user_email = db["users"][reset_user]["email"]
                            if send_reset_email(user_email, otp, reset_user):
                                st.session_state.otp_sent_to = reset_user
                                st.success(f"OTP sent to {user_email[:3]}***@***")
                                st.rerun()
                        else:
                            st.error("Username not found or no email associated.")
            
            else:
                # OTP was sent, now verify and set new password
                with st.form("verify_reset_form"):
                    st.info(f"An OTP was sent to the email associated with **{st.session_state.otp_sent_to}**.")
                    entered_otp = st.text_input("Enter 6-digit OTP")
                    new_password = st.text_input("Enter New Password", type="password")
                    
                    if st.form_submit_button("Reset Password"):
                        target_user = st.session_state.otp_sent_to
                        saved_otp = db["users"][target_user].get("reset_otp", "")
                        
                        if entered_otp == saved_otp and saved_otp != "":
                            # Success! Change password and clear OTP
                            db["users"][target_user]["password"] = new_password
                            db["users"][target_user]["reset_otp"] = "" 
                            db_utils.save_data(db)
                            st.session_state.otp_sent_to = None # Reset state
                            st.success("Password successfully changed! You can now log in.")
                        else:
                            st.error("Invalid OTP code.")
                            
                if st.button("Cancel / Restart"):
                    st.session_state.otp_sent_to = None
                    st.rerun()
                        
    st.stop()

current_user = st.session_state.username

# ==========================================
# 🛡️ SUPER ADMIN VIEW 
# ==========================================
if current_user == SUPERADMIN_USER:
    st.sidebar.write("👤 **Logged in as: SUPER ADMIN**")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Download Master DB Backup",
        data=json.dumps(db, indent=4),
        file_name="master_election_data.json",
        mime="application/json"
    )

    def super_admin_dashboard():
        st.title("🛡️ Developer Master Control Panel")
        st.write("Welcome, Developer. Here you can oversee all tenant data, recover lost passwords, and manage platforms.")
        
        colleges = db.get("colleges", {})
        users = db.get("users", {})
        
        c1, c2 = st.columns(2)
        c1.metric("Total Registered Colleges", len(colleges))
        c2.metric("Total User Accounts", len(users))
        
        st.markdown("---")
        st.subheader("Registered Institutions")
        
        if not colleges:
            st.info("No colleges have registered yet.")
        else:
            for cid, cdata in colleges.items():
                with st.expander(f"🏫 {cdata['college_name']} (ID: {cid})"):
                    st.write(f"**Election Mode:** {cdata.get('election_mode', 'Unknown')}")
                    
                    c_users = {u: d for u, d in users.items() if d.get("college_id") == cid}
                    
                    if c_users:
                        st.markdown("**Associated User Accounts & Passwords:**")
                        df_users = pd.DataFrame([
                            {"Username": u, "Password": d["password"], "Role": d["role"], "Email": d.get("email", "N/A")} 
                            for u, d in c_users.items()
                        ])
                        st.dataframe(df_users, hide_index=True, use_container_width=True)
                    else:
                        st.write("No users found for this college.")
                        
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button(f"🗑️ Permanently Delete {cdata['college_name']}", key=f"del_{cid}", type="primary"):
                        for u in list(c_users.keys()):
                            del db["users"][u]
                        del db["colleges"][cid]
                        db_utils.save_data(db)
                        st.success(f"College and associated users deleted!")
                        st.rerun()

    pg = st.navigation({"Developer": [st.Page(super_admin_dashboard, title="Master Control", icon="🛡️")]})
    pg.run()
    st.stop()


# ==========================================
# 🏫 NORMAL COLLEGE USER VIEW 
# ==========================================
if current_user not in db["users"]:
    st.session_state.authenticated = False
    st.rerun()

user_profile = db["users"][current_user]
college_id = user_profile["college_id"]

if college_id not in db["colleges"]:
    st.session_state.authenticated = False
    st.rerun()
    
college_data = db["colleges"][college_id]

# --- SIDEBAR: USER & SETTINGS ---
st.sidebar.write(f"👤 **{current_user}** ({user_profile['role']})")
st.sidebar.write(f"🏫 **{college_data['college_name']}**")

if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

st.sidebar.markdown("---")

# --- ADMIN-ONLY DASHBOARD CONTROLS ---
if user_profile['role'] == "Admin":
    st.sidebar.header("🏛️ Admin Settings")
    
    updated_college_name = st.sidebar.text_input("College Name", value=college_data["college_name"])
    if updated_college_name != college_data["college_name"]:
        college_data["college_name"] = updated_college_name.upper()
        db_utils.save_data(db)
        
    uploaded_logo = st.sidebar.file_uploader("Upload College Logo", type=["png", "jpg", "jpeg"])
    if uploaded_logo is not None:
        os.makedirs("logos", exist_ok=True)
        logo_filename = f"logos/{college_id}_logo.png"
        with open(logo_filename, "wb") as f:
            f.write(uploaded_logo.getbuffer())
        college_data["logo_path"] = logo_filename
        db_utils.save_data(db)
        
    st.sidebar.markdown("---")
    
    st.sidebar.header("👥 Manage Staff Accounts")
    with st.sidebar.expander("➕ Create New Staff User"):
        with st.form("new_staff_form", clear_on_submit=True):
            staff_user = st.text_input("Staff Username")
            staff_pass = st.text_input("Staff Password", type="password")
            if st.form_submit_button("Create Account"):
                if not staff_user or not staff_pass:
                    st.warning("Provide both username and password.")
                elif staff_user in db["users"] or staff_user == SUPERADMIN_USER:
                    st.error("Username already exists.")
                else:
                    db["users"][staff_user] = {
                        "password": staff_pass,
                        "college_id": college_id,
                        "role": "Staff"
                    }
                    db_utils.save_data(db)
                    st.success(f"Created staff account: {staff_user}")
                    st.rerun()

    staff_list = [u for u, data in db["users"].items() if data["college_id"] == college_id and data["role"] == "Staff"]
    if staff_list:
        st.sidebar.caption("Active Staff Accounts:")
        for s in staff_list:
            st.sidebar.caption(f"- {s}")

st.sidebar.markdown("---")
st.sidebar.header("Global Election Settings")
election_year = st.sidebar.text_input("Election Year", value="2026-27")
poll_date = st.sidebar.text_input("Date of Poll", value="")

if "election_years" not in college_data:
    college_data["election_years"] = {}

if election_year not in college_data["election_years"]:
    college_data["election_years"][election_year] = {
        "poll_date": poll_date,
        "programs": {
            "UG": DEFAULT_UG.copy(),
            "PG": DEFAULT_PG.copy()
        },
        "class_reps": {},
        "main_posts_config": [
            {"post_name": "The Chairperson", "seats": 1},
            {"post_name": "General Secretary", "seats": 1},
            {"post_name": "University Union Councillor (UUC)", "seats": 2}
        ],
        "main_post_candidates": {}
    }
    db_utils.save_data(db)
else:
    college_data["election_years"][election_year]["poll_date"] = poll_date
    db_utils.save_data(db)

# --- PROGRAM LIST MANAGER (For College Admin to Edit) ---
if user_profile['role'] == "Admin" and college_data["election_mode"] == "Parliamentary":
    st.sidebar.markdown("---")
    st.sidebar.header("📚 Program List Manager")
    st.sidebar.write("Edit college programs below (one per line):")
    
    ug_text = "\n".join(college_data["election_years"][election_year]["programs"].get("UG", DEFAULT_UG))
    pg_text = "\n".join(college_data["election_years"][election_year]["programs"].get("PG", DEFAULT_PG))
    
    ug_input = st.sidebar.text_area("UG Programs", value=ug_text, height=150)
    pg_input = st.sidebar.text_area("PG Programs", value=pg_text, height=150)
    
    college_data["election_years"][election_year]["programs"]["UG"] = [p.strip() for p in ug_input.split('\n') if p.strip()]
    college_data["election_years"][election_year]["programs"]["PG"] = [p.strip() for p in pg_input.split('\n') if p.strip()]
    db_utils.save_data(db)

# --- HOME DASHBOARD VIEW ---
def home_page():
    col_logo, col_title = st.columns([1, 6])
    with col_logo:
        logo_path = college_data.get("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            st.image(logo_path, width=120)
        else:
            st.markdown("<div style='height: 100px; width: 100px; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center;'><small>No Logo</small></div>", unsafe_allow_html=True)
            
    with col_title:
        st.markdown(f"<h1 style='color: #2E4053; margin-top: -15px;'>{college_data['college_name']}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color: #5D6D7E; margin-top: -10px;'>College Union Election ({election_year}) - {college_data['election_mode']} Mode</h3>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Institution Election Dashboard")
    
    st.download_button(
        label="📥 Download Live Database Backup",
        data=json.dumps(db, indent=4),
        file_name=f"{college_id}_backup.json",
        mime="application/json"
    )

# --- DYNAMIC NAVIGATION LOGIC ---
overview_pages = [st.Page(home_page, title="Dashboard Home", icon="📊")]
workflow_pages = []

if college_data["election_mode"] == "Parliamentary":
    workflow_pages.extend([
        st.Page("pages/1_Class_Rep_Nominations.py", title="1. Class Rep Nominations", icon="📝"),
        st.Page("pages/2_Withdrawals_&_Final.py", title="2. Scrutiny & Withdrawals", icon="🛑"),
        st.Page("pages/3_Ballot_Generation.py", title="3. Class Rep Ballots", icon="🖨️"),
        st.Page("pages/4_Class_Rep_Results.py", title="4. Class Rep Results", icon="🏆"),
    ])

p_prefix = "5" if college_data["election_mode"] == "Parliamentary" else "1"
e_prefix = "6" if college_data["election_mode"] == "Parliamentary" else "2"

workflow_pages.extend([
    st.Page("pages/5_Main_Post_Config.py", title=f"{p_prefix}. Main Post Config", icon="⚙️"),
    st.Page("pages/6_Main_Post_Elections.py", title=f"{e_prefix}. Main Post Elections", icon="🗳️")
])

pg = st.navigation({
    "Overview": overview_pages,
    "Election Workflow": workflow_pages
})

pg.run()
