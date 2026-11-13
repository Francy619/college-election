import streamlit as st
import pandas as pd
from fpdf import FPDF
import json
import os
import uuid

st.set_page_config(page_title="Main Post Elections", page_icon="🗳️", layout="wide")

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

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()
user_profile = db.get("users", {}).get(current_user, {})
college_name = user_profile.get("college_name", "COLLEGE UNION ELECTION")
college_data = db.get(current_user, {})

class MainPostPDF(FPDF):
    def candidate_list(self, title, post_name, candidates, year_str, college_name):
        self.add_page()
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, college_name, ln=True, align="C")
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, f"College Union Election {year_str}", ln=True, align="C")
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(5)
        
        self.set_font("Arial", "BU", 11)
        self.cell(0, 10, f"Post: {post_name}", ln=True, align="L")
        
        self.set_font("Arial", "B", 10)
        self.cell(20, 8, "SL No", border=1, align="C")
        self.cell(40, 8, "Electoral Roll No", border=1, align="C")
        self.cell(90, 8, "Name of Candidate", border=1, align="C")
        self.cell(40, 8, "Original Class", border=1, align="C")
        self.ln()
        
        self.set_font("Arial", "", 10)
        for idx, cand in enumerate(candidates):
            self.cell(20, 8, str(idx+1), border=1, align="C")
            self.cell(40, 8, str(cand['roll_no']), border=1, align="C")
            self.cell(90, 8, str(cand['name']), border=1)
            self.cell(40, 8, str(cand.get('class_origin', 'N/A')), border=1, align="C")
            self.ln()

    def create_ballots(self, count, post_name, seats, candidates, year_str, poll_date_str, college_name):
        for idx in range(count):
            if idx % 2 == 0:
                self.add_page()
                y_offset = 0
            else:
                y_offset = 148.5
                self.set_line_width(0.5)
                for x in range(0, 210, 4):
                    self.line(x, 148.5, x + 2, 148.5)
            self._draw_ballot(y_offset, post_name, seats, candidates, year_str, poll_date_str, college_name)

    def _draw_ballot(self, y_offset, post_name, seats, candidates, year_str, poll_date_str, college_name):
        self.set_font("Arial", "", 10)
        self.set_xy(10, 15 + y_offset)
        self.set_font("Arial", "B", 10)
        self.cell(60, 5, "SL. No. ________", ln=True)
        self.set_font("Arial", "", 9)
        self.cell(60, 5, f"Election to College Union {year_str}", ln=True)
        self.set_font("Arial", "B", 9)
        self.cell(60, 5, "Counter foil of Ballot Paper", ln=True)
        self.set_font("Arial", "", 9)
        
        self.multi_cell(60, 5, f"Name of the post: {post_name}")
        self.set_x(10)
        self.cell(60, 5, f"No. of Seats: {seats}", ln=True)
        self.ln(2)
        self.set_x(10)
        self.cell(60, 5, "Name of Elector: ____________", ln=True)
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
        self.multi_cell(110, 5, f"Name of the post: {post_name}", align="C")
        self.set_x(85)
        self.cell(110, 5, f"No. of Seats: {seats}", ln=True, align="C")
        self.set_x(85)
        self.set_font("Arial", "B", 12)
        self.cell(110, 8, "BALLOT PAPER", ln=True, align="C")
        self.ln(3)
        
        self.set_x(85)
        self.set_font("Arial", "B", 10)
        self.cell(25, 8, "Roll No", border=1, align="C")
        self.cell(60, 8, "Name", border=1, align="C")
        self.cell(25, 8, "Space", border=1, align="C")
        self.ln()
        
        self.set_font("Arial", "B", 10)
        row_height = 10
        active_cands = [c for c in candidates if c.get('status') == "Nominated"]
        for cand in active_cands:
            self.set_x(85)
            self.cell(25, row_height, str(cand['roll_no']), border=1, align="C")
            self.cell(60, row_height, str(cand['name']), border=1)
            self.cell(25, row_height, "", border=1)
            self.ln()

st.title("🗳️ Main Post Elections")

if not college_data:
    st.warning("No election data found.")
    st.stop()

selected_year = st.selectbox("Select Election Year", list(college_data.keys()), index=len(college_data)-1)
year_data = college_data[selected_year]

if "main_post_candidates" not in year_data:
    year_data["main_post_candidates"] = {}

posts = [p["post_name"] for p in year_data.get("main_posts_config", [])]
if not posts:
    st.warning("No main posts configured. Go to Config module.")
    st.stop()

selected_post = st.selectbox("Select Post to Manage", posts)
seats_for_post = next(p["seats"] for p in year_data["main_posts_config"] if p["post_name"] == selected_post)

if selected_post not in year_data["main_post_candidates"]:
    year_data["main_post_candidates"][selected_post] = []

eligible_cands = []
for c_name, c_data in year_data.get("class_reps", {}).items():
    for cand in c_data.get("candidates", []):
        if cand.get("status") == "Elected":
            cand_copy = cand.copy()
            cand_copy["class_origin"] = c_name
            eligible_cands.append(cand_copy)

st.markdown(f"### Nominate from Electoral College")
with st.form("main_nomination_form"):
    if not eligible_cands:
        st.warning("No Elected Class Reps available to nominate.")
        st.form_submit_button("Submit", disabled=True)
    else:
        options = {c['id']: f"{c['name']} ({c['class_origin']})" for c in eligible_cands}
        selected_cand_id = st.selectbox("Select Elected Representative", options.keys(), format_func=lambda x: options[x])
        if st.form_submit_button("Nominate for Post", type="primary"):
            c_data = next(c for c in eligible_cands if c['id'] == selected_cand_id)
            new_cand = {
                "id": str(uuid.uuid4())[:8],
                "roll_no": c_data["roll_no"],
                "name": c_data["name"],
                "gender": c_data["gender"],
                "class_origin": c_data["class_origin"],
                "status": "Nominated"
            }
            year_data["main_post_candidates"][selected_post].append(new_cand)
            save_data(db)
            st.success(f"Nominated {c_data['name']} for {selected_post}!")
            st.rerun()

st.markdown("### Withdrawals & Final List Generation")
current_cands = year_data["main_post_candidates"][selected_post]
if current_cands:
    df = pd.DataFrame(current_cands)
    edited_df = st.data_editor(
        df,
        column_config={
            "id": None, "roll_no": st.column_config.NumberColumn(disabled=True),
            "name": st.column_config.TextColumn(disabled=True), "gender": st.column_config.TextColumn(disabled=True),
            "class_origin": st.column_config.TextColumn(disabled=True),
            "status": st.column_config.SelectboxColumn("Status", options=["Nominated", "Withdrawn"])
        },
        use_container_width=True, hide_index=True
    )
    
    if st.button("Save Changes"):
        for idx, row in edited_df.iterrows():
            for c in year_data["main_post_candidates"][selected_post]:
                if c["id"] == row["id"]:
                    c["status"] = row["status"]
        save_data(db)
        st.rerun()
        
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        pdf_list = MainPostPDF()
        active = [c for c in current_cands if c.get("status") == "Nominated"]
        pdf_list.candidate_list(f"Candidate List - {selected_post}", selected_post, active, selected_year, college_name)
        st.download_button("📥 Download Candidate List (PDF)", data=pdf_list.output(dest='S').encode('latin1'), file_name=f"Candidates_{selected_post}.pdf")
    with c2:
        ballot_count = st.number_input("Number of Ballots", min_value=1, value=50)
        pdf_ballots = MainPostPDF()
        pdf_ballots.create_ballots(ballot_count, selected_post, seats_for_post, current_cands, selected_year, year_data.get("poll_date", "___"), college_name)
        st.download_button("🖨️ Download Ballot Papers (PDF)", data=pdf_ballots.output(dest='S').encode('latin1'), file_name=f"Ballots_{selected_post}.pdf")
