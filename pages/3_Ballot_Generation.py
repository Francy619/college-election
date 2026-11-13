import streamlit as st
import pandas as pd
from fpdf import FPDF
import json
import os

st.set_page_config(page_title="Ballot Generation", page_icon="🖨️", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("🔒 Please log in from the Home page to access this module.")
    st.stop()

current_user = st.session_state.username
DATA_FILE = "election_data.json"

def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

db = load_data()
user_profile = db.get("users", {}).get(current_user, {})
college_name = user_profile.get("college_name", "COLLEGE UNION ELECTION")
college_data = db.get(current_user, {})

class BallotPDF(FPDF):
    def create_multiple_ballots(self, count, post_name, class_name, seats, candidates, year_str, poll_date_str, college_name, is_main_post=False):
        for idx in range(count):
            if idx % 2 == 0:
                self.add_page()
                y_offset = 0
            else:
                y_offset = 148.5
                self.set_line_width(0.5)
                for x in range(0, 210, 4):
                    self.line(x, 148.5, x + 2, 148.5)
            self._draw_single_ballot(y_offset, post_name, class_name, seats, candidates, year_str, poll_date_str, college_name, is_main_post)

    def _draw_single_ballot(self, y_offset, post_name, class_name, seats, candidates, year_str, poll_date_str, college_name, is_main_post):
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
        self.cell(110, 5, college_name, ln=True, align="C")
        self.set_x(85)
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
            active_cands = [c for c in candidates if c.get('status') == "Nominated"]
            for cand in active_cands:
                self.set_x(85)
                self.cell(25, row_height, str(cand['roll_no']), border=1, align="C")
                self.cell(60, row_height, str(cand['name']), border=1)
                self.cell(25, row_height, "", border=1)
                self.ln()
        else:
            active_cands = [c for c in candidates if c.get('status') == "Nominated"]
            males = [c for c in active_cands if c['gender'] == 'Male']
            females = [c for c in active_cands if c['gender'] == 'Female']
            
            if len(males) > 1:
                self.set_x(85)
                self.cell(110, 6, "Class Representative Male", border=1, align="C")
                self.ln()
                for cand in males:
                    self.set_x(85)
                    self.cell(25, row_height, str(cand['roll_no']), border=1, align="C")
                    self.cell(60, row_height, str(cand['name']), border=1)
                    self.cell(25, row_height, "", border=1)
                    self.ln()
                    
            if len(females) > 1:
                self.set_x(85)
                self.cell(110, 6, "Class Representative Female", border=1, align="C")
                self.ln()
                for cand in females:
                    self.set_x(85)
                    self.cell(25, row_height, str(cand['roll_no']), border=1, align="C")
                    self.cell(60, row_height, str(cand['name']), border=1)
                    self.cell(25, row_height, "", border=1)
                    self.ln()

st.title("🖨️ Ballot Paper Generation")

if not college_data:
    st.warning("No election data found.")
    st.stop()

available_years = list(college_data.keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = college_data[selected_year]

poll_date_display = year_data.get("poll_date", "____________") or "____________"

tab1, tab2 = st.tabs(["1. Single Class Ballot Print", "2. Consolidated Master Ballot PDF (All Classes)"])

with tab1:
    st.subheader("Print Ballots for a Specific Class")
    classes_with_noms = [c for c, d in year_data.get("class_reps", {}).items() if d["candidates"]]
    if not classes_with_noms:
        st.warning("No classes have candidates registered.")
    else:
        selected_class = st.selectbox("Select Class", classes_with_noms)
        class_info = year_data["class_reps"][selected_class]
        ballot_count = st.number_input("Number of Ballot Papers to Print", min_value=1, max_value=1000, value=60)
        
        if st.button("🖨️ Generate Ballot PDF for Selected Class", type="primary"):
            pdf = BallotPDF()
            pdf.create_multiple_ballots(
                count=ballot_count,
                post_name="Class representative",
                class_name=selected_class,
                seats=class_info["seats"],
                candidates=class_info["candidates"],
                year_str=selected_year,
                poll_date_str=poll_date_display,
                college_name=college_name,
                is_main_post=False
            )
            st.download_button(
                label=f"📥 Download Ballot PDF ({selected_class})",
                data=pdf.output(dest='S').encode('latin1'),
                file_name=f"Ballots_{selected_class.replace(' ', '_')}_{selected_year}.pdf"
            )

with tab2:
    st.subheader("Consolidated Master Archive PDF")
    if st.button("🖨️ Generate Consolidated Master Ballot PDF", type="primary"):
        master_pdf = BallotPDF()
        generated_count = 0
        
        for c_name, c_data in year_data.get("class_reps", {}).items():
            active_cands = [c for c in c_data["candidates"] if c.get("status") == "Nominated"]
            males = [c for c in active_cands if c['gender'] == 'Male']
            females = [c for c in active_cands if c['gender'] == 'Female']
            
            if len(males) > 1 or len(females) > 1:
                master_pdf.create_multiple_ballots(
                    count=2,
                    post_name="Class representative",
                    class_name=c_name,
                    seats=c_data["seats"],
                    candidates=c_data["candidates"],
                    year_str=selected_year,
                    poll_date_str=poll_date_display,
                    college_name=college_name,
                    is_main_post=False
                )
                generated_count += 1
                
        if generated_count > 0:
            st.success(f"Consolidated ballot PDF generated for {generated_count} contested classes!")
            st.download_button(
                label="📥 Download Master Consolidated Ballot PDF",
                data=master_pdf.output(dest='S').encode('latin1'),
                file_name=f"Master_Consolidated_Ballots_{selected_year}.pdf"
            )
        else:
            st.warning("No contested classes found.")
