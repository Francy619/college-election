import streamlit as st
import pandas as pd
import json
import os
import io
from fpdf import FPDF
import db_utils

st.set_page_config(page_title="Ballot Generation", page_icon="🖨️", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("🔒 Please log in from the Home page to access this module.")
    st.stop()

db = db_utils.load_data()
current_user = st.session_state.username

if current_user not in db["users"]: st.stop()
college_id = db["users"][current_user]["college_id"]
if college_id not in db["colleges"]: st.stop()

college_data = db["colleges"][college_id]
college_name = college_data.get("college_name", "COLLEGE UNION ELECTION")

# --- PDF GENERATOR CLASS ---
class BallotPDF(FPDF):
    def generate_ballots(self, class_list, class_reps_data, year_str, poll_date_str, college_name):
        valid_classes = []
        
        for cls in class_list:
            c_data = class_reps_data.get(cls, {})
            active_cands = [c for c in c_data.get("candidates", []) if c.get('status') == "Nominated"]
            
            males = sorted([c for c in active_cands if c['gender'] == 'Male'], key=lambda x: x['name'])
            females = sorted([c for c in active_cands if c['gender'] == 'Female'], key=lambda x: x['name'])
            
            if len(males) > 1 or len(females) > 1:
                valid_classes.append({
                    "class_name": cls,
                    "males": males,
                    "females": females
                })
        
        for cls_info in valid_classes:
            self.add_page()
            
            # 1. TOP HALF BALLOT
            self._draw_single_ballot(0, cls_info, year_str, poll_date_str, college_name)
            
            # Draw horizontal perforation line across the middle of the page
            self.set_line_width(0.4)
            for x in range(0, 210, 4):  
                self.line(x, 148.5, x + 2, 148.5)
                
            # 2. BOTTOM HALF BALLOT
            self._draw_single_ballot(148.5, cls_info, year_str, poll_date_str, college_name)

    def _draw_single_ballot(self, y_offset, cls_info, year_str, poll_date_str, college_name):
        class_name = cls_info["class_name"]
        males = cls_info["males"]
        females = cls_info["females"]
        
        contesting_males = len(males) > 1
        contesting_females = len(females) > 1
        
        display_seats = 0
        if contesting_males and contesting_females:
            display_seats = 2
        elif contesting_males or contesting_females:
            display_seats = 1

        # ==========================================
        # LEFT SIDE: Counter Foil
        # ==========================================
        self.set_xy(10, 10 + y_offset)
        self.set_font("Times", "", 8) 
        line_ht = 8 
        
        self.cell(65, line_ht, "SL. No. __________________", ln=True)
        self.cell(65, line_ht, f"Election to College Union {year_str}", ln=True)
        self.set_font("Times", "B", 8)
        self.cell(65, line_ht, "Counter foil of Ballot Paper", ln=True)
        self.ln(3)
        
        self.set_font("Times", "", 8)
        self.cell(65, line_ht, "Name of the post: Class Representative", ln=True)
        self.set_font("Times", "B", 9) 
        self.cell(65, line_ht, f"({class_name})", ln=True)
        self.set_font("Times", "", 8)
        
        self.cell(65, line_ht, f"No. of Seats: {display_seats}", ln=True)
        self.ln(5)
        
        line_ht_btm = 7
        self.cell(65, line_ht_btm, "Name of the elector: ___________________", ln=True)
        self.cell(65, line_ht_btm, "Electoral Roll No. : ___________________", ln=True)
        # Date of poll removed from here, moved to absolute bottom
        
        # Draw vertical perforation line (Positioned at 78)
        self.set_line_width(0.4)
        for y in range(int(5 + y_offset), int(143 + y_offset), 4):
            self.line(78, y, 78, y + 2)
            
        # ==========================================
        # RIGHT SIDE: Main Ballot Headers
        # ==========================================
        self.set_xy(85, 8 + y_offset)
        self.set_font("Times", "", 8)
        self.cell(50, 6, "SL. No. _________________")
        self.cell(60, 6, "Signature of the RO..................", ln=True, align="R")
        self.ln(2)
        
        self.set_x(85)
        self.set_font("Times", "B", 10)
        self.cell(110, 6, college_name, ln=True, align="C")
        self.set_x(85)
        self.set_font("Times", "", 10)
        self.cell(110, 6, f"Election to College Union {year_str}", ln=True, align="C")
        self.ln(4)
        
        self.set_x(85)
        str_start = "Name of the post: Class representative ("
        self.set_font("Times", "", 10)
        self.cell(self.get_string_width(str_start), 6, str_start)
        self.set_font("Times", "B", 10)
        self.cell(self.get_string_width(class_name), 6, class_name)
        self.set_font("Times", "", 10)
        self.cell(self.get_string_width(")"), 6, ")", ln=True)
        
        self.set_x(85)
        self.cell(110, 6, f"No. of Seats: {display_seats}", ln=True, align="L")
        self.ln(2)
        
        # ==========================================
        # RIGHT SIDE: Ballot Table
        # ==========================================
        self.set_x(85)
        self.set_font("Times", "B", 13)
        self.cell(110, 7, "BALLOT PAPER", ln=True, align="C")
        self.set_x(85)
        self.set_font("Times", "I", 9) 
        self.cell(110, 5, "(Vote by placing the mark 'X' against the name of the candidate for whom you vote)", ln=True, align="C")
        self.ln(3)
        
        self.set_x(85)
        self.set_font("Times", "B", 11)
        self.cell(20, 8, "Roll No", border=1, align="C")
        self.cell(65, 8, "Name of the Candidate", border=1, align="C")
        self.cell(25, 8, "Space for Mark", border=1, align="C")
        self.ln()
        
        row_height = 10 
        header_height = 7
        
        if contesting_males:
            self.set_x(85)
            self.set_font("Times", "B", 10)
            self.cell(110, header_height, "Class Representative (Male)", border=1, align="C")
            self.ln()
            for cand in males:
                self.set_x(85)
                self.set_font("Times", "B", 12)
                self.cell(20, row_height, str(cand['roll_no']), border=1, align="C")
                
                name_text = str(cand['name'])
                font_sz = 12
                self.set_font("Times", "B", font_sz)
                while self.get_string_width(name_text) > 63 and font_sz > 6:
                    font_sz -= 0.5
                    self.set_font("Times", "B", font_sz)
                    
                self.cell(65, row_height, name_text, border=1)
                self.cell(25, row_height, "", border=1)
                self.ln()
                
        if contesting_females:
            self.set_x(85)
            self.set_font("Times", "B", 10)
            self.cell(110, header_height, "Class Representative (Female)", border=1, align="C")
            self.ln()
            for cand in females:
                self.set_x(85)
                self.set_font("Times", "B", 12)
                self.cell(20, row_height, str(cand['roll_no']), border=1, align="C")
                
                name_text = str(cand['name'])
                font_sz = 12
                self.set_font("Times", "B", font_sz)
                while self.get_string_width(name_text) > 63 and font_sz > 6:
                    font_sz -= 0.5
                    self.set_font("Times", "B", font_sz)
                    
                self.cell(65, row_height, name_text, border=1)
                self.cell(25, row_height, "", border=1)
                self.ln()

        # ==========================================
        # ABSOLUTE BOTTOM POSITIONING (Date of Poll)
        # ==========================================
        # Positioned ~20mm above the bottom cut-line
        self.set_font("Times", "", 9)
        
        # 1. Bottom-Left of Counterfoil
        self.set_xy(10, 138 + y_offset)
        self.cell(65, 5, f"Date of poll: {poll_date_str}")
        

# --- CACHED PDF GENERATOR ---
@st.cache_data(show_spinner=False)
def generate_ballot_pdf_cached(class_list, cls_data_json, year_str, poll_date_str, col_name):
    class_reps_data = json.loads(cls_data_json)
    pdf = BallotPDF()
    pdf.generate_ballots(class_list, class_reps_data, year_str, poll_date_str, col_name)
    return pdf.output(dest='S').encode('latin1')

# --- MAIN UI ---
st.title("🖨️ Master Ballot Generation (Press Copy)")
st.markdown("Generate master copies of the ballot papers for the printing press. **Each printed sheet will contain exactly 1 class, repeated twice (Top & Bottom halves)**.")

if "election_years" not in college_data or not college_data["election_years"]:
    st.warning("No election data found.")
    st.stop()

available_years = list(college_data["election_years"].keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = college_data["election_years"][selected_year]

poll_date_display = year_data.get("poll_date", "____________") or "____________"
class_reps_data = year_data.get("class_reps", {})

if not class_reps_data:
    st.info("No class representatives have been nominated for this year yet.")
    st.stop()

# --- 1. FILTER CONTROLS ---
st.markdown("### 1. Filter Classes for Printing")
c1, c2, c3 = st.columns(3)

with c1:
    lvl_filter = st.selectbox("Course Level", ["All", "UG", "PG"])
with c2:
    yr_filter = st.selectbox("Year", ["All", "I", "II", "III", "IV"])
with c3:
    progs = ["All"]
    if lvl_filter == "UG":
        progs.extend(year_data.get("programs", {}).get("UG", []))
    elif lvl_filter == "PG":
        progs.extend(year_data.get("programs", {}).get("PG", []))
    else:
        progs.extend(year_data.get("programs", {}).get("UG", []))
        progs.extend(year_data.get("programs", {}).get("PG", []))
        
    prog_filter = st.selectbox("Program / Class", progs)

# Apply Filter Logic
filtered_classes = []
for cls in class_reps_data.keys():
    parts = cls.split(" ", 1)
    if len(parts) == 2:
        c_yr, c_prog = parts
    else:
        continue
        
    if yr_filter != "All" and c_yr != yr_filter: continue
    if prog_filter != "All" and c_prog != prog_filter: continue
    if lvl_filter != "All":
        if c_prog not in year_data.get("programs", {}).get(lvl_filter, []):
            continue
            
    filtered_classes.append(cls)

filtered_classes.sort()

# Pre-calculate which classes actually have a contested election
contested_classes = []
for cls in filtered_classes:
    c_data = class_reps_data[cls]
    active = [c for c in c_data.get("candidates", []) if c.get('status') == "Nominated"]
    males = [c for c in active if c['gender'] == 'Male']
    females = [c for c in active if c['gender'] == 'Female']
    
    if len(males) > 1 or len(females) > 1:
        contested_classes.append(cls)

# --- 2. EXPORT SECTION ---
st.markdown("---")
st.markdown("### 2. Print Master Ballot PDF")

if not contested_classes:
    st.info("No contested elections found for the selected filters. Classes where candidates are unopposed do not require ballots.")
else:
    st.success(f"Found {len(contested_classes)} class(es) requiring ballots based on your filter.")
    
    # Generate cached string
    cls_data_json_str = json.dumps(class_reps_data)
    
    pdf_bytes = generate_ballot_pdf_cached(
        contested_classes, 
        cls_data_json_str, 
        selected_year, 
        poll_date_display, 
        college_name
    )
    
    st.download_button(
        label="📥 Download Master Ballot PDF", 
        data=pdf_bytes, 
        file_name=f"Master_Ballots_{selected_year}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )
    
    with st.expander("Show list of classes included in this PDF"):
        for c in contested_classes:
            st.write(f"- {c}")
