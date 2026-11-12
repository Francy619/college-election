import streamlit as st
import pandas as pd
import json
import os

# --- PERSISTENT DATABASE SETUP ---
DATA_FILE = "election_data.json"

def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# --- PAGE CONFIG ---
st.set_page_config(page_title="College Election Manager", layout="wide", page_icon="🗳️")

# --- INITIALIZE DEFAULTS IN SESSION STATE ---
if "ug_text" not in st.session_state:
    st.session_state.ug_text = "B. Sc Mathematics\nB. Sc Physics\nB. Sc Chemistry\nB. Sc Botany\nB. Sc Zoology\nB. A English\nB. A Economics\nB. A History\nB. Com F&T\nB. Com FM\nB. Com LM\nB. Com Accounting\nB. Voc Agriculture Technology\nBCA\nBBA"
if "pg_text" not in st.session_state:
    st.session_state.pg_text = "M. Sc Mathematics\nM. Sc Physics\nM. Sc Chemistry\nM. Sc Botany\nM. Sc Zoology\nM. A English\nM. A Economics\nM. A History\nM. Com"

# --- GLOBAL SETTINGS (SIDEBAR) ---
st.sidebar.header("Global Settings")
election_year = st.sidebar.text_input("Election Year", value="2026-27")
poll_date = st.sidebar.text_input("Date of Poll (e.g., 14-Nov-2026)", value="")

# Ensure year structure exists in database
if election_year not in db:
    db[election_year] = {
        "poll_date": poll_date,
        "programs": {
            "UG": [p.strip() for p in st.session_state.ug_text.split('\n') if p.strip()],
            "PG": [p.strip() for p in st.session_state.pg_text.split('\n') if p.strip()]
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
    # Update poll date if changed
    db[election_year]["poll_date"] = poll_date
    save_data(db)

st.sidebar.markdown("---")
st.sidebar.header("Program List Manager")
st.sidebar.write("Edit college programs below (one per line):")

ug_input = st.sidebar.text_area("UG Programs", key="ug_text", height=220)
pg_input = st.sidebar.text_area("PG Programs", key="pg_text", height=180)

# Update programs in DB for current year
db[election_year]["programs"]["UG"] = [p.strip() for p in ug_input.split('\n') if p.strip()]
db[election_year]["programs"]["PG"] = [p.strip() for p in pg_input.split('\n') if p.strip()]
save_data(db)

# --- CUSTOM HEADER ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120) 
    else:
        st.markdown("<div style='height: 120px; width: 120px; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center;'><small>Add logo.png</small></div>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='color: #2E4053; margin-top: -15px;'>ST. DOMINIC'S COLLEGE, KANJIRAPALLY</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #5D6D7E; margin-top: -10px;'>College Union Election Management ({election_year})</h3>", unsafe_allow_html=True)

st.markdown("---")

# --- MAIN DASHBOARD HOME PAGE ---
st.subheader("📊 Election Dashboard")
st.write(f"Welcome to the College Election Management Portal. You are currently managing records for **Academic Year {election_year}**.")

year_data = db[election_year]
class_reps_data = year_data.get("class_reps", {})

# Calculate quick metrics
total_classes_configured = len(class_reps_data)
total_nominations = sum(len(c_data["candidates"]) for c_data in class_reps_data.values())
total_withdrawn = sum(len([c for c in c_data["candidates"] if c.get("status") == "Withdrawn"]) for c_data in class_reps_data.values())
total_active = total_nominations - total_withdrawn

m1, m2, m3, m4 = st.columns(4)
m1.metric("Classes with Nominations", total_classes_configured)
m2.metric("Total Nominations", total_nominations)
m3.metric("Withdrawn Candidates", total_withdrawn)
m4.metric("Active Contestants", total_active)

st.markdown("---")
st.markdown("### 🧭 Quick Navigation Guide")
st.write("Use the **Sidebar menu on the left** (generated automatically by the `pages/` folder) to navigate through each phase of the election:")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("""
    * **1. Class Rep Nominations**: Add students, roll numbers, and genders for UG/PG classes.
    * **2. Withdrawals & Final List**: Process candidate dropouts and export official valid lists.
    * **3. Ballot Generation**: Print individual or master consolidated ballot packets (2 per page).
    """)
with col_b:
    st.markdown("""
    * **4. Class Rep Results**: Record election outcomes (Elected / Lost) to lock in the electoral college.
    * **5. Main Post Config**: Define union executive posts like Chairperson and UUC.
    * **6. Main Post Elections**: Nominate winning class reps, handle withdrawals, and print main ballots.
    """)

# --- CUSTOM FOOTER ---
st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #808B96; font-size: 14px;'>Developed by Francis Thomas</p>", unsafe_allow_html=True)
