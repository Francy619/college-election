import streamlit as st
import pandas as pd
import json
import os
import io
from fpdf import FPDF
import db_utils

st.set_page_config(page_title="Main Post Ballots", page_icon="🖨️", layout="wide")

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
class MainBallotPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Turn OFF auto page breaks so the bottom ballot's Date of Poll NEVER jumps to a new page
        self.set_auto_page_break(auto=False, margin=0)

    def generate_ballots(self, valid_posts, post_candidates_data, posts_config, year_str, poll_date_str, college_name):
        
        # Helper to get seats for a post
        def get_seats(p_name):
            for p in posts_config:
                if p["post_name"] == p_name:
                    return p["seats"]
            return 1

        for post_name in valid_posts:
            self.add_page()
            
            c_data = post_candidates_data.get(post_name, {})
            active_cands = [c for c in c_data.get("candidates", []) if c.get('status') == "Nominated"]
            sorted_cands = sorted(active_cands, key=lambda x: x['name'])
            seats = get_seats(post_name)
            
            # 1. TOP HALF BALLOT
            self._draw_single_ballot(0, post_name, sorted_cands, seats, year_str, poll_date_str, college_name)
            
            # Draw horizontal perforation line across the middle of the page
            self.set_line_width(0.4)
            for x in range(0, 210, 4):  
                self.line(x, 148.5, x + 2, 148.5)
                
            # 2. BOTTOM HALF BALLOT
            self._draw_single_ballot(148.5, post_name, sorted_cands, seats, year_str, poll_date_str, college_name)

    def _draw_single_ballot(self, y_offset, post_name, candidates, seats, year_str, poll_date_str, college_name):
        # ==========================================
        # LEFT SIDE: Counter Foil
        # ==========================================
        self.set_xy(15, 12 + y_offset)
        self.set_font("Times", "", 8) 
        line_ht = 8 
        
        self.cell(60, line_ht, "SL. No. __________________", ln=True)
        self.cell(60, line_ht, f"Election to College Union {year_str}", ln=True)
        self.set_font("Times", "B", 8)
        self.cell(60, line_ht, "Counter foil of Ballot Paper", ln=True)
        self.ln(3)
        
        self.set_font("Times", "", 8)
        self.cell(60, line_ht, "Name of the post:", ln=True)
        
        # Auto-shrink for exceptionally long post names in counterfoil
        font_sz_title = 10
        self.set_font("Times", "B", font_sz_title)
        while self.get_string_width(post_name) > 58 and font_sz_title > 7:
            font_sz_title -= 0.5
            self.set_font("Times", "B", font_sz_title)
        self.cell(60, line_ht, post_name, ln=True)
        
        self.set_font("Times", "", 8)
        self.cell(60, line_ht, f"No. of Seats: {seats}", ln=True)
        self.ln(5)
        
        line_ht_btm = 7
        self.cell(60, line_ht_btm, "Name of the elector: ___________________", ln=True)
        self.cell(60, line_ht_btm, "Electoral Roll No. : ___________________", ln=True)
        
        # Date of poll moved up directly beneath the roll number with a gap
        self.ln(3)
        self.set_font("Times", "", 9)
        self.cell(60, 5, f"Date of poll: {poll_date_str}", ln=True)
        
        # Draw vertical perforation line (Positioned at 78)
        self.set_line_width(0.4)
        for y in range(int(5 + y_offset), int(143 + y_offset), 4):
            self.line(78, y, 78, y + 2)
            
        # ==========================================
        # RIGHT SIDE: Main Ballot Headers
        # ==========================================
        self.set_xy(85, 12 + y_offset)
        self.set_font("Times", "", 8)
        self.cell(50, 6, "SL. No. _________________")
        
        # Signature is pushed down to Y=20 to leave empty space ABOVE it for the RO Seal
        self.set_xy(145, 20 + y_offset)
        self.cell(50, 6, "Signature of the RO..................", align="R")
        
        # College Name resumes below the signature (Y=28)
        self.set_xy(85, 28 + y_offset)
        self.set_font("Times", "B", 10)
        self.cell(110, 6, college_name, ln=True, align="C")
        self.set_x(85)
        self.set_font("Times", "", 10)
        self.cell(110, 6, f"Election to College Union {year_str}", ln=True, align="C")
        self.ln(4)
        
        self.set_x(85)
        str_start = "Name of the post: "
        self.set_font("Times", "", 10)
        self.cell(self.get_string_width(str_start), 6, str_start)
        
        # Auto-shrink for main ballot post name if too long
        font_sz_title_main = 10
        self.set_font("Times", "B", font_sz_title_main)
        while self.get_string_width(post_name) > (110 - self.get_string_width(str_start)) and font_sz_title_main > 7:
            font_sz_title_main -= 0.5
            self.set_font("Times", "B", font_sz_title_main)
        
        self.cell(self.get_string_width(post_name), 6, post_name, ln=True)
        
        self.set_x(85)
        self.set_font("Times", "", 10)
        self.cell(110, 6, f"No. of Seats: {seats}", ln=True, align="L")
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
        self.set_font("Times", "B", 10)
        # Widened Name column to 65, reduced Roll to 15
        self.cell(15, 8, "Roll No", border=1, align="C")
        self.cell(65, 8, "Name & Class", border=1, align="C")
        self.cell(30, 8, "Space for Mark", border=1, align="C")
        self.ln()
        
        # Increased row height to fit both Name and Class
        row_height = 14 
        
        for cand in candidates:
            start_y = self.get_y()
            
            self.set_xy(85, start_y)
            self.set_font("Times", "B", 12)
            self.cell(15, row_height, str(cand['roll_no']), border=1, align="C")
            
            # Draw empty borders for Name and Mark columns
            self.set_xy(100, start_y)
            self.cell(65, row_height, "", border=1)
            self.set_xy(165, start_y)
            self.cell(30, row_height, "", border=1)
            
            # Fill in Candidate Name (Top Half)
            name_text = str(cand['name'])
            font_sz = 12
            self.set_font("Times", "B", font_sz)
            while self.get_string_width(name_text) > 63 and font_sz > 6:
                font_sz -= 0.5
                self.set_font("Times", "B", font_sz)
            
            self.set_xy(100, start_y + 2)
            self.cell(65, 6, name_text, align="C")
            
            # Fill in Class Name (Bottom Half)
            class_text = str(cand.get('class_name', ''))
            font_sz_cls = 10
            self.set_font("Times", "", font_sz_cls)
            while self.get_string_width(class_text) > 63 and font_sz_cls > 6:
                font_sz_cls -= 0.5
                self.set_font("Times", "", font_sz_cls)
                
            self.set_xy(100, start_y + 7.5)
            self.cell(65, 5, class_text, align="C")
            
            self.set_xy(85, start_y + row_height)

# --- CACHED PDF GENERATOR ---
@st.cache_data(show_spinner=False)
def generate_main_ballot_pdf_cached(valid_posts, post_data_json, posts_config_json, year_str, poll_date_str, col_name):
    post_data = json.loads(post_data_json)
    posts_config = json.loads(posts_config_json)
    pdf = MainBallotPDF()
    pdf.generate_ballots(valid_posts, post_data, posts_config, year_str, poll_date_str, col_name)
    return pdf.output(dest='S').encode('latin1')

# --- MAIN UI ---
st.title("🖨️ Main Post Ballot Generation (Press Copy)")
st.markdown("Generate master copies of the ballot papers for the printing press. **Each printed sheet will contain exactly 1 Post, repeated twice (Top & Bottom halves)**.")

if "election_years" not in college_data or not college_data["election_years"]:
    st.warning("No election data found.")
    st.stop()

available_years = list(college_data["election_years"].keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = college_data["election_years"][selected_year]

poll_date_display = year_data.get("poll_date", "____________") or "____________"
main_post_data = year_data.get("main_post_candidates", {})
posts_config = year_data.get("main_posts_config", [])

if not main_post_data or not posts_config:
    st.info("No main post candidates have been nominated for this year yet.")
    st.stop()

# Pre-calculate which posts actually have a contested election
contested_posts = []
for post_cfg in posts_config:
    p_name = post_cfg["post_name"]
    seats_available = post_cfg["seats"]
    
    if p_name in main_post_data:
        active = [c for c in main_post_data[p_name].get("candidates", []) if c.get('status') == "Nominated"]
        # It is only contested if the number of active candidates is greater than the available seats!
        if len(active) > seats_available:
            contested_posts.append(p_name)

# --- EXPORT SECTION ---
st.markdown("---")
st.markdown("### Print Master Ballot PDF")

if not contested_posts:
    st.info("No contested elections found for any Main Posts. Posts where candidates are unopposed do not require printed ballots.")
else:
    st.success(f"Found {len(contested_posts)} Main Post(s) requiring ballots.")
    
    # Generate cached strings
    post_data_json_str = json.dumps(main_post_data)
    posts_config_json_str = json.dumps(posts_config)
    
    pdf_bytes = generate_main_ballot_pdf_cached(
        contested_posts, 
        post_data_json_str,
        posts_config_json_str,
        selected_year, 
        poll_date_display, 
        college_name
    )
    
    st.download_button(
        label="📥 Download Master Main Post Ballots (PDF)", 
        data=pdf_bytes, 
        file_name=f"Main_Post_Master_Ballots_{selected_year}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )
    
    with st.expander("Show list of Posts included in this PDF"):
        for p in contested_posts:
            st.write(f"- {p}")

# --- INJECT FOOTER ---
if hasattr(db_utils, 'add_footer'):
    db_utils.add_footer()
