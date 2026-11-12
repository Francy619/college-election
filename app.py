import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="College Election Manager", layout="wide", page_icon="🗳️")

# --- CUSTOM HEADER ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120) 
    else:
        st.markdown("<div style='height: 120px; width: 120px; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center;'><small>Add logo.png</small></div>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='color: #2E4053; margin-top: -15px;'>ST. DOMINIC'S COLLEGE, KANJIRAPALLY</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #5D6D7E; margin-top: -10px;'>College Union Election Management 2026-27</h3>", unsafe_allow_html=True)
st.markdown("---")

# --- INITIALIZE SESSION STATE ---
if "class_candidates" not in st.session_state:
    st.session_state.class_candidates = []
if "main_candidates" not in st.session_state:
    st.session_state.main_candidates = []

# --- PDF GENERATION CLASSES ---
class ElectionPDF(FPDF):
    def candidate_list(self, title, candidates, is_class=True):
        self.add_page()
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "ST. DOMINIC'S COLLEGE, KANJIRAPALLY", ln=True, align="C")
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "College Union Election 2026-27", ln=True, align="C")
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(5)
        
        # Table Header
        self.set_font("Arial", "B", 10)
        self.cell(20, 10, "SL No", border=1, align="C")
        self.cell(40, 10, "Electoral Roll No", border=1, align="C")
        self.cell(90, 10, "Name of Candidate", border=1, align="C")
        if is_class:
            self.cell(40, 10, "Gender", border=1, align="C")
        self.ln()
        
        # Table Data
        self.set_font("Arial", "", 10)
        for idx, cand in enumerate(candidates):
            self.cell(20, 10, str(idx+1), border=1, align="C")
            self.cell(40, 10, str(cand['Roll No']), border=1, align="C")
            self.cell(90, 10, str(cand['Name']), border=1)
            if is_class:
                self.cell(40, 10, str(cand['Gender']), border=1, align="C")
            self.ln()

    def create_ballot(self, post_name, class_name, seats, candidates, is_main_post=False):
        self.add_page()
        self.set_font("Arial", "", 10)
        
        # We will draw the ballot layout. Counterfoil (Left 30%), Cut Line, Ballot (Right 65%)
        # Left Margin: 10, Right Margin: 200
        
        # --- COUNTER FOIL (LEFT) ---
        self.set_xy(10, 15)
        self.set_font("Arial", "B", 10)
        self.cell(60, 5, "SL. No. ________", ln=True)
        self.set_font("Arial", "", 9)
        self.cell(60, 5, "Election to College Union 2026-27", ln=True)
        self.set_font("Arial", "B", 9)
        self.cell(60, 5, "Counter foil of Ballot Paper", ln=True)
        self.set_font("Arial", "", 9)
        
        post_disp = post_name if is_main_post else f"{post_name} ({class_name})"
        self.multi_cell(60, 5, f"Name of the post: {post_disp}")
        self.cell(60, 5, f"No. of Seats: {seats}", ln=True)
        self.ln(2)
        self.cell(60, 5, "Name of the elector: ____________", ln=True)
        if not is_main_post:
            self.cell(60, 5, f"Class: {class_name}", ln=True)
        self.cell(60, 5, "Electoral Roll No.: ____________", ln=True)
        self.cell(60, 5, "Date of poll: ____________", ln=True)
        
       # --- CUT HERE LINE ---
        self.set_line_width(0.5)
        
        # Manually draw a dashed line to ensure compatibility across all fpdf versions
        for y in range(10, 280, 4):
            self.line(75, y, 75, y + 2)
            
        self.set_xy(71, 140)
        self.set_font("Arial", "", 8)
        
        # Vertical text rotation workaround
        self.text(77, 140, "Cut here.........................................................")
        
        # --- BALLOT PAPER (RIGHT) ---
        self.set_xy(85, 15)
        self.set_font("Arial", "B", 10)
        self.cell(50, 5, "SL. No. ________")
        self.cell(60, 5, "Signature of the RO..................", ln=True, align="R")
        
        self.set_xy(85, 25)
        self.set_font("Arial", "", 10)
        self.cell(110, 5, "Election to College Union 2026-27", ln=True, align="C")
        self.set_font("Arial", "B", 10)
        self.multi_cell(110, 5, f"Name of the post: {post_disp}", align="C")
        self.cell(110, 5, f"No. of Seats: {seats}", ln=True, align="C")
        self.set_font("Arial", "B", 12)
        self.cell(110, 8, "BALLOT PAPER", ln=True, align="C")
        self.set_font("Arial", "", 9)
        self.multi_cell(110, 4, "(Vote by placing the mark 'X' against the name of the candidate for whom you vote)", align="C")
        self.ln(3)
        
        # Table Headers
        self.set_x(85)
        self.set_font("Arial", "B", 10)
        self.cell(25, 10, "Electoral Roll No", border=1, align="C")
        self.cell(60, 10, "Name", border=1, align="C")
        self.cell(25, 10, "Space for marking", border=1, align="C")
        self.ln()
        
        # Table Rows
        self.set_font("Arial", "B", 10)
        if is_main_post:
            # Main post layout (No gender split)
            for cand in candidates:
                self.set_x(85)
                self.cell(25, 12, str(cand['Roll No']), border=1, align="C")
                self.cell(60, 12, str(cand['Name']), border=1)
                self.cell(25, 12, "", border=1)
                self.ln()
        else:
            # Class Rep layout (Gender split)
            males = [c for c in candidates if c['Gender'] == 'Male']
            females = [c for c in candidates if c['Gender'] == 'Female']
            
            if males:
                self.set_x(85)
                self.cell(110, 8, "Class Representative Male", border=1, align="C")
                self.ln()
                for cand in males:
                    self.set_x(85)
                    self.cell(25, 12, str(cand['Roll No']), border=1, align="C")
                    self.cell(60, 12, str(cand['Name']), border=1)
                    self.cell(25, 12, "", border=1)
                    self.ln()
            if females:
                self.set_x(85)
                self.cell(110, 8, "Class Representative Female", border=1, align="C")
                self.ln()
                for cand in females:
                    self.set_x(85)
                    self.cell(25, 12, str(cand['Roll No']), border=1, align="C")
                    self.cell(60, 12, str(cand['Name']), border=1)
                    self.cell(25, 12, "", border=1)
                    self.ln()

# --- APP LAYOUT ---
tab1, tab2 = st.tabs(["1. Class Representative Election", "2. Main Post Election (Chairperson)"])

with tab1:
    st.subheader("Manage Class Representatives")
    c1, c2 = st.columns(2)
    with c1:
        class_name = st.text_input("Name of the Class (e.g., I B. Sc Mathematics)", value="I B. Sc Mathematics")
    with c2:
        class_seats = st.number_input("Number of Seats", min_value=1, value=2, key="c_seats")
        
    st.markdown("##### Add Candidates")
    with st.form("class_candidate_form"):
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
                st.session_state.class_candidates.append({"Roll No": roll_no, "Name": cand_name, "Gender": gender})
                st.rerun()

    if st.session_state.class_candidates:
        st.dataframe(pd.DataFrame(st.session_state.class_candidates), use_container_width=True)
        if st.button("Clear Class Candidates"):
            st.session_state.class_candidates = []
            st.rerun()
            
        st.markdown("---")
        ballot_count = st.number_input("Number of Ballot Papers to Generate", min_value=1, max_value=200, value=10, key="b_count_class")
        
        pdf_col1, pdf_col2 = st.columns(2)
        with pdf_col1:
            # Generate Candidate List
            pdf_list = ElectionPDF()
            pdf_list.candidate_list(f"Candidate List - Class Representative ({class_name})", st.session_state.class_candidates, is_class=True)
            st.download_button("📥 Download Candidate List PDF", data=pdf_list.output(dest='S').encode('latin1'), file_name=f"Candidates_{class_name}.pdf")
            
        with pdf_col2:
            # Generate Ballots
            pdf_ballot = ElectionPDF()
            for _ in range(ballot_count):
                pdf_ballot.create_ballot("Class representative", class_name, class_seats, st.session_state.class_candidates, is_main_post=False)
            st.download_button("🖨️ Download Ballot Papers PDF", data=pdf_ballot.output(dest='S').encode('latin1'), file_name=f"Ballots_{class_name}.pdf")


with tab2:
    st.subheader("Manage Main Post Election")
    m1, m2 = st.columns(2)
    with m1:
        post_name = st.text_input("Name of the Post", value="The Chairperson")
    with m2:
        main_seats = st.number_input("Number of Seats", min_value=1, value=1, key="m_seats")
        
    st.markdown("##### Add Candidates (From Winning Reps)")
    with st.form("main_candidate_form"):
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
                st.session_state.main_candidates.append({"Roll No": m_roll_no, "Name": m_cand_name})
                st.rerun()

    if st.session_state.main_candidates:
        st.dataframe(pd.DataFrame(st.session_state.main_candidates), use_container_width=True)
        if st.button("Clear Main Candidates"):
            st.session_state.main_candidates = []
            st.rerun()
            
        st.markdown("---")
        m_ballot_count = st.number_input("Number of Ballot Papers to Generate", min_value=1, max_value=1000, value=50, key="b_count_main")
        
        mpdf_col1, mpdf_col2 = st.columns(2)
        with mpdf_col1:
            # Generate Candidate List
            pdf_mlist = ElectionPDF()
            pdf_mlist.candidate_list(f"Candidate List - {post_name}", st.session_state.main_candidates, is_class=False)
            st.download_button("📥 Download Candidate List PDF", data=pdf_mlist.output(dest='S').encode('latin1'), file_name=f"Candidates_{post_name}.pdf")
            
        with mpdf_col2:
            # Generate Ballots
            pdf_mballot = ElectionPDF()
            for _ in range(m_ballot_count):
                pdf_mballot.create_ballot(post_name, "", main_seats, st.session_state.main_candidates, is_main_post=True)
            st.download_button("🖨️ Download Ballot Papers PDF", data=pdf_mballot.output(dest='S').encode('latin1'), file_name=f"Ballots_{post_name}.pdf")

# --- CUSTOM FOOTER ---
st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #808B96; font-size: 14px;'>Developed by Francis Thomas</p>", unsafe_allow_html=True)
