import streamlit as st
import pandas as pd
from fpdf import FPDF
import db_utils

st.set_page_config(page_title="Class Rep Results", page_icon="🏆", layout="wide")

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

class ResultsPDF(FPDF):
    def elected_candidates_list(self, title, data_dict, year_str, college_name):
        self.add_page()
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, college_name, ln=True, align="C")
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, f"College Union Election {year_str}", ln=True, align="C")
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(5)
        
        for class_name, data in data_dict.items():
            elected_cands = [c for c in data.get('candidates', []) if c.get('status') == "Elected"]
            if not elected_cands:
                continue
                
            self.set_font("Arial", "BU", 11)
            self.cell(0, 10, f"Class: {class_name}", ln=True, align="L")
            
            self.set_font("Arial", "B", 10)
            self.cell(20, 8, "SL No", border=1, align="C")
            self.cell(40, 8, "Electoral Roll No", border=1, align="C")
            self.cell(90, 8, "Name of Winner", border=1, align="C")
            self.cell(40, 8, "Gender", border=1, align="C")
            self.ln()
            
            self.set_font("Arial", "", 10)
            for idx, cand in enumerate(elected_cands):
                self.cell(20, 8, str(idx+1), border=1, align="C")
                self.cell(40, 8, str(cand['roll_no']), border=1, align="C")
                self.cell(90, 8, str(cand['name']), border=1)
                self.cell(40, 8, str(cand['gender']), border=1, align="C")
                self.ln()
            self.ln(5) 

st.title("🏆 Class Representative Election Results")

if "election_years" not in college_data or not college_data["election_years"]:
    st.warning("No election data found.")
    st.stop()

available_years = list(college_data["election_years"].keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = college_data["election_years"][selected_year]

classes_list = list(year_data.get("class_reps", {}).keys())
if not classes_list:
    st.warning("No classes configured.")
    st.stop()

selected_class = st.selectbox("Select Class to Update Results", classes_list)
class_info = year_data["class_reps"][selected_class]
active_candidates = [c for c in class_info.get("candidates", []) if c.get("status") != "Withdrawn"]

if not active_candidates:
    st.warning("No active candidates found for this class.")
else:
    st.markdown(f"### Results Management for: **{selected_class}**")
    with st.form(f"results_form_{selected_class}"):
        updated_statuses = {}
        for cand in active_candidates:
            c1, c2, c3, c4 = st.columns([2, 4, 2, 3])
            c1.text(f"Roll: {cand['roll_no']}")
            c2.text(f"{cand['name']}")
            c3.text(f"{cand['gender']}")
            
            current_status = cand.get("status", "Nominated")
            status_options = ["Nominated", "Elected", "Lost"]
            default_idx = status_options.index(current_status) if current_status in status_options else 0
            
            new_status = c4.selectbox("Status", status_options, index=default_idx, key=f"status_{cand['id']}", label_visibility="collapsed")
            updated_statuses[cand['id']] = new_status

        if st.form_submit_button("💾 Save Results", type="primary"):
            for c in year_data["class_reps"][selected_class]["candidates"]:
                if c["id"] in updated_statuses:
                    c["status"] = updated_statuses[c["id"]]
            db_utils.save_data(db)
            st.success(f"Results saved!")
            st.rerun()

st.markdown("---")
st.markdown("### 🖨️ Official Declaration of Winners")
pdf_results = ResultsPDF()
pdf_results.elected_candidates_list("Official Declaration of Elected Class Representatives", year_data.get("class_reps", {}), selected_year, college_name)
st.download_button("📥 Download Official Elected Representatives List (PDF)", data=pdf_results.output(dest='S').encode('latin1'), file_name=f"Elected_Class_Reps_{selected_year}.pdf")
