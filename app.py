import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os
import json

# --- PERSISTENT DATABASE SETUP ---
DATA_FILE = "election_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# --- PAGE CONFIG ---
st.set_page_config(page_title="College Election Manager", layout="wide", page_icon="🗳️")

# Default program lists
if "ug_programs_text" not in st.session_state:
    st.session_state.ug_programs_text = "B. Sc Mathematics\nB. Sc Physics\nB. Sc Chemistry\nB. Sc Botany\nB. Sc Zoology\nB. A English\nB. A Economics\nB. A History\nB. Com F&T\nB. Com FM\nB. Com LM\nB. Com Accounting\nB. Voc Agriculture Technology\nBCA\nBBA"
if "pg_programs_text" not in st.session_state:
    st.session_state.pg_programs_text = "M. Sc Mathematics\nM. Sc Physics\nM. Sc Chemistry\nM. Sc Botany\nM. Sc Zoology\nM. A English\nM. A Economics\nM. A History\nM. Com"

# --- GLOBAL SETTINGS (SIDEBAR) ---
st.sidebar.header("Global Settings")
election_year = st.sidebar.text_input("Election Year", value="2026-27")
poll_date = st.sidebar.text_input("Date of Poll (Leave blank for line)", value="")
poll_date_display = f"{poll_date}" if poll_date else "____________"

# Initialize the selected year in the database if it doesn't exist
if election_year not in db:
    db[election_year] = {"classes": {}, "main_posts": {}}
    save_data(db)

st.sidebar.markdown("---")
st.sidebar.header("Edit Program Lists")
st.sidebar.write("Edit the courses below (one per line).")

st.sidebar.text_area("UG Programs", key="ug_programs_text", height=250)
st.sidebar.text_area("PG Programs", key="pg_programs_text", height=200)

ug_programs = [p.strip() for p in st.session_state.ug_programs_text.split('\n') if p.strip()]
pg_programs = [p.strip() for p in st.session_state.pg_programs_text.split('\n') if p.strip()]

# --- CUSTOM HEADER ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120) 
    else:
        st.markdown("<div style='height: 120px; width: 120px; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center;'><small>Add logo.png</small></div>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='color: #2E4053; margin-top: -15px;'>ST. DOMINIC'S COLLEGE, KANJIRAPALLY</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #5D6D7E; margin-top: -10px;'>College Union Election Management {election_year}</h3>", unsafe_allow_html=True)
st.markdown("---")

# --- PDF GENERATION CLASSES ---
class ElectionPDF(FPDF):
    def consolidated_candidate_list(self, title, data_dict, year_str, is_class=True):
        self.add_page()
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "ST. DOMINIC'S COLLEGE, KANJIRAPALLY", ln=True, align="C")
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, f"College Union Election {year_str}", ln=True, align="C")
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(5)
        
        for heading, data in data_dict.items():
            if not data['candidates']:
                continue
                
            self.set_font("Arial", "BU", 11)
            label = "Class" if is_class else "Post"
            self.cell(0, 10, f"{label}: {heading} (Seats: {data['seats']})", ln=True, align="L")
            
            self.set_font("Arial", "B", 10)
            self.cell(20, 8, "SL No", border=1, align="C")
            self.cell(40, 8, "Electoral Roll No", border=1, align="C")
            self.cell(90, 8, "Name of Candidate", border=1, align="C")
            if is_class:
                self.cell(40, 8, "Gender", border=1, align="C")
            self.ln()
            
            self.set_font("Arial", "", 10)
            for idx, cand in enumerate(data['candidates']):
                self.cell(20, 8, str(idx+1), border=1, align="C")
                self.cell(40, 8, str(cand['Roll No']), border=1, align="C")
                self.cell(90, 8, str(cand['Name']), border=1)
                if is_class:
                    self.cell(40, 8, str(cand['Gender']), border=1, align="C")
                self.ln()
            self.ln(5) 

    def create_multiple_ballots(self, count, post_name, class_name, seats, candidates, year_str, poll_date_str, is_main_post=False):
        for idx in range(count):
            if idx % 2 == 0:
                self.add_page()
                y_offset = 0
            else:
                y_offset = 148.5 
                self.set_line_width(0.5)
                for x in range(0, 210, 4):
                    self.line(x, 148.5, x + 2, 148.5)
            
            self._draw_single_ballot(y_offset, post_name, class_name, seats, candidates, year_str, poll_date_str, is_main_post)

    def _draw_single_ballot(self, y_offset, post_name, class_name, seats, candidates, year_str, poll_date_str, is_main_post):
        self.set_font("Arial", "", 10)
        
        self.set_xy(10, 15 + y_offset)
        self.set_font("Arial", "B", 10)
        self.cell(60, 5, "SL. No. ________", ln=True)
        self.set_font("Arial", "", 9)
        self.cell(60, 5, f"Election to College Union {year_str}", ln=True)
        self.set_font("Arial", "B", 9)
        self.cell(60, 5, "Counter foil of Ballot Paper", ln=True)
        self.set_font("Arial", "", 9)
        
        post_disp = post_name if is_main_post else f"{post_name} ({class_name})"
        self.multi_cell(60, 5, f"Name of the post: {post_disp}")
        self.set_x(10)
        self.cell(60, 5, f"No. of Seats: {seats}", ln=True)
        self.ln(2)
        self.set_x(10)
        self.cell(60, 5, "Name of the elector: ____________", ln=True)
        if not is_main_post:
            self.set_x(10)
            self.cell(60, 5, f"Class: {class_name}", ln=True)
        self.set_x(10)
        self.cell(60, 5, "Electoral Roll No.: ____________", ln=True)
        self.set_x(10)
        self.cell(60, 5, f"Date of poll: {poll_date_str}", ln=True)
        
        self.set_line_width(0.5)
        for y in range(int(10 + y_offset), int(140 + y_offset), 4):
            self.line(75, y, 75, y + 2)
            
        self.set_font("Arial", "", 8)
        self.text(77, 135 + y_offset, "Cut here.........................................................")
        
        self.set_xy(85, 15 + y_offset)
        self.set_font("Arial", "B", 10)
        self.cell(50, 5, "SL. No. ________")
        self.cell(60, 5, "Signature of the RO..................", ln=True, align="R")
        
        self.set_xy(85, 25 + y_offset)
        self.set_font("Arial", "", 10)
        self.cell(110, 5, f"Election to College Union {year_str}", ln=True, align="C")
        self.set_x(85)
        self.set_font("Arial", "B", 10)
        self.multi_cell(110, 5, f"Name of the post: {post_disp}", align="C")
        self.set_x(85)
        self.cell(110, 5, f"No. of Seats: {seats}", ln=True, align="C")
        self.set_x(85)
        self.set_font("Arial", "B", 12)
        self.cell(110, 8, "BALLOT PAPER", ln=True, align="C")
        self.set_x(85)
        self.set_font("Arial", "", 9)
        self.multi_cell(110, 4, "(Vote by placing the mark 'X' against the name of the candidate for whom you vote)", align="C")
        self.ln(3)
        
        self.set_x(85)
        self.set_font("Arial", "B", 10)
        self.cell(25, 8, "Roll No", border=1, align="C")
        self.cell(60, 8, "Name", border=1, align="C")
        self.cell(25, 8, "Space", border=1, align="C")
        self.ln()
        
        self.set_font("Arial", "B", 10)
        row_height = 10
        if is_main_post:
            for cand in candidates:
                self.set_x(85)
                self.cell(25, row_height, str(cand['Roll No']), border=1, align="C")
                self.cell(60, row_height, str(cand['Name']), border=1)
                self.cell(25, row_height, "", border=1)
                self.ln()
        else:
            males = [c for c in candidates if c['Gender'] == 'Male']
            females = [c for c in candidates if c['Gender'] == 'Female']
            
            if len(males) > 1:
                self.set_x(85)
                self.cell(110, 6, "Class Representative Male", border=1, align="C")
                self.ln()
                for cand in males:
                    self.set_x(85)
                    self.cell(25, row_height, str(cand['Roll No']), border=1, align="C")
                    self.cell(60, row_height, str(cand['Name']), border=1)
                    self.cell(25, row_height, "", border=1)
                    self.ln()
                    
            if len(females) > 1:
                self.set_x(85)
                self.cell(110, 6, "Class Representative Female", border=1, align="C")
                self.ln()
                for cand in females:
                    self.set_x(85)
                    self.cell(25, row_height, str(cand['Roll No']), border=1, align="C")
                    self.cell(60, row_height, str(cand['Name']), border=1)
                    self.cell(25, row_height, "", border=1)
                    self.ln()

# --- APP LAYOUT ---
tab1, tab2 = st.tabs(["1. Class Representative Election", "2. Main Post Election"])

with tab1:
    st.subheader("Manage Class Representatives")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        degree_level = st.selectbox("Course Level", ["UG", "PG"])
    with c2:
        year_options = ["I", "II", "III"] if degree_level == "UG" else ["I", "II"]
        year = st.selectbox("Year", year_options)
    with c3:
        program_list = ug_programs if degree_level == "UG" else pg_programs
        program = st.selectbox("Program", program_list)
    with c4:
        class_seats = st.number_input("Number of Seats", min_value=1, value=2, key="c_seats")
        
    class_name = f"{year} {program}"
    st.info(f"Currently managing: **{class_name}** ({election_year})")
    
    # Init class in DB if missing
    if class_name not in db[election_year]["classes"]:
        db[election_year]["classes"][class_name] = {'seats': class_seats, 'candidates': []}
        save_data(db)
    else:
        db[election_year]["classes"][class_name]['seats'] = class_seats
        save_data(db)
        
    st.markdown("##### Add Candidate")
    with st.form("class_candidate_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
        with col1:
            roll_no = st.number_input("Electoral Roll No.", min_value=1, step=1)
        with col2:
            cand_name = st.text_input("Candidate Name").upper()
        with col3:
            gender = st.selectbox("Gender", ["Male", "Female"])
        with col4:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("Add")
            if submitted and cand_name:
                db[election_year]["classes"][class_name]['candidates'].append({"Roll No": roll_no, "Name": cand_name, "Gender": gender})
                save_data(db) # Save instantly

    st.markdown(f"### Candidates Registered for {election_year}")
    has_class_candidates = any(len(data['candidates']) > 0 for data in db[election_year]["classes"].values())
    
    if has_class_candidates:
        for c_name, c_data in db[election_year]["classes"].items():
            if c_data['candidates']:
                with st.expander(f"{c_name} (Seats: {c_data['seats']} | Candidates: {len(c_data['candidates'])})", expanded=True):
                    st.dataframe(pd.DataFrame(c_data['candidates']), use_container_width=True)
                    
        if st.button("⚠️ Clear ALL Class Candidates for this Year"):
            db[election_year]["classes"] = {}
            save_data(db)
            st.rerun()
            
        st.markdown("---")
        st.markdown("### Generate Documents")
        pdf_col1, pdf_col2 = st.columns(2)
        with pdf_col1:
            st.write("**Master Candidate List** (Contains all classes above)")
            pdf_list = ElectionPDF()
            pdf_list.consolidated_candidate_list("Consolidated Candidate List - Class Representatives", db[election_year]["classes"], election_year, is_class=True)
            st.download_button("📥 Download Master Candidate List PDF", data=pdf_list.output(dest='S').encode('latin1'), file_name=f"Master_Class_Reps_{election_year}.pdf")
            
        with pdf_col2:
            st.write(f"**Ballot Papers for {class_name}**")
            ballot_count = st.number_input(f"No. of Ballots for {class_name}", min_value=1, max_value=500, value=60, key="b_count_class")
            if db[election_year]["classes"][class_name]['candidates']:
                pdf_ballot = ElectionPDF()
                pdf_ballot.create_multiple_ballots(ballot_count, "Class representative", class_name, class_seats, db[election_year]["classes"][class_name]['candidates'], election_year, poll_date_display, is_main_post=False)
                st.download_button(f"🖨️ Download Ballots for {class_name}", data=pdf_ballot.output(dest='S').encode('latin1'), file_name=f"Ballots_{class_name}.pdf")
            else:
                st.warning("Add candidates to this class first to generate ballots.")

with tab2:
    st.subheader("Manage Main Post Elections")
    m1, m2 = st.columns(2)
    with m1:
        post_name = st.text_input("Name of the Post", value="The Chairperson")
    with m2:
        main_seats = st.number_input("Number of Seats", min_value=1, value=1, key="m_seats")
        
    st.info(f"Currently managing: **{post_name}** ({election_year})")
    
    if post_name not in db[election_year]["main_posts"]:
        db[election_year]["main_posts"][post_name] = {'seats': main_seats, 'candidates': []}
        save_data(db)
    else:
        db[election_year]["main_posts"][post_name]['seats'] = main_seats
        save_data(db)
        
    st.markdown("##### Add Candidates (From Winning Reps)")
    with st.form("main_candidate_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 4, 1])
        with col1:
            m_roll_no = st.number_input("Electoral Roll No.", min_value=1, step=1, key="m_roll")
        with col2:
            m_cand_name = st.text_input("Candidate Name", key="m_name").upper()
        with col3:
            st.write("")
            st.write("")
            m_submitted = st.form_submit_button("Add")
            if m_submitted and m_cand_name:
                db[election_year]["main_posts"][post_name]['candidates'].append({"Roll No": m_roll_no, "Name": m_cand_name})
                save_data(db)

    st.markdown(f"### Main Posts Registered for {election_year}")
    has_main_candidates = any(len(data['candidates']) > 0 for data in db[election_year]["main_posts"].values())

    if has_main_candidates:
        for p_name, p_data in db[election_year]["main_posts"].items():
            if p_data['candidates']:
                with st.expander(f"{p_name} (Seats: {p_data['seats']} | Candidates: {len(p_data['candidates'])})", expanded=True):
                    st.dataframe(pd.DataFrame(p_data['candidates']), use_container_width=True)
                    
        if st.button("⚠️ Clear ALL Main Post Candidates for this Year"):
            db[election_year]["main_posts"] = {}
            save_data(db)
            st.rerun()
            
        st.markdown("---")
        st.markdown("### Generate Documents")
        mpdf_col1, mpdf_col2 = st.columns(2)
        with mpdf_col1:
            st.write("**Master Candidate List** (Contains all posts above)")
            pdf_mlist = ElectionPDF()
            pdf_mlist.consolidated_candidate_list("Consolidated Candidate List - Main Posts", db[election_year]["main_posts"], election_year, is_class=False)
            st.download_button("📥 Download Master Main Posts List", data=pdf_mlist.output(dest='S').encode('latin1'), file_name=f"Master_MainPosts_{election_year}.pdf")
            
        with mpdf_col2:
            st.write(f"**Ballot Papers for {post_name}**")
            m_ballot_count = st.number_input(f"No. of Ballots for {post_name}", min_value=1, max_value=2000, value=50, key="b_count_main")
            if db[election_year]["main_posts"][post_name]['candidates']:
                pdf_mballot = ElectionPDF()
                pdf_mballot.create_multiple_ballots(m_ballot_count, post_name, "", main_seats, db[election_year]["main_posts"][post_name]['candidates'], election_year, poll_date_display, is_main_post=True)
                st.download_button(f"🖨️ Download Ballots for {post_name}", data=pdf_mballot.output(dest='S').encode('latin1'), file_name=f"Ballots_{post_name}.pdf")
            else:
                st.warning("Add candidates to this post first to generate ballots.")

# --- CUSTOM FOOTER ---
st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #808B96; font-size: 14px;'>Developed by Francis Thomas</p>", unsafe_allow_html=True)
