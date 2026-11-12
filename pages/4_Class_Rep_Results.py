import streamlit as st
import pandas as pd
from fpdf import FPDF
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Class Rep Results", page_icon="🏆", layout="wide")

# --- DATABASE HELPER FUNCTIONS ---
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

# --- PDF GENERATION CLASS FOR RESULTS ---
class ResultsPDF(FPDF):
    def elected_candidates_list(self, title, data_dict, year_str):
        self.add_page()
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "ST. DOMINIC'S COLLEGE, KANJIRAPALLY", ln=True, align="C")
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, f"College Union Election {year_str}", ln=True, align="C")
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(5)
        
        has_elected_records = False
        
        for class_name, data in data_dict.items():
            # Filter only candidates marked as "Elected"
            elected_cands = [c for c in data.get('candidates', []) if c.get('status') == "Elected"]
            
            if not elected_cands:
                continue
                
            has_elected_records = True
            
            # Print Class Heading
            self.set_font("Arial", "BU", 11)
            self.cell(0, 10, f"Class: {class_name}", ln=True, align="L")
            
            # Table Header
            self.set_font("Arial", "B", 10)
            self.cell(20, 8, "SL No", border=1, align="C")
            self.cell(40, 8, "Electoral Roll No", border=1, align="C")
            self.cell(90, 8, "Name of Winner", border=1, align="C")
            self.cell(40, 8, "Gender", border=1, align="C")
            self.ln()
            
            # Table Data
            self.set_font("Arial", "", 10)
            for idx, cand in enumerate(elected_cands):
                self.cell(20, 8, str(idx+1), border=1, align="C")
                self.cell(40, 8, str(cand['roll_no']), border=1, align="C")
                self.cell(90, 8, str(cand['name']), border=1)
                self.cell(40, 8, str(cand['gender']), border=1, align="C")
                self.ln()
            self.ln(5) 
            
        if not has_elected_records:
            self.set_font("Arial", "I", 11)
            self.cell(0, 10, "No candidates have been marked as Elected yet.", ln=True, align="C")

# --- HEADER ---
st.title("🏆 Class Representative Election Results")
st.markdown("Record election outcomes. Mark active contestants as **Elected** or **Lost** to establish the official electoral college for the Main Post elections.")

if not db:
    st.warning("No election data found.")
    st.stop()

available_years = list(db.keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = db[selected_year]

if "class_reps" not in year_data or not year_data["class_reps"]:
    st.info("No class representatives configured for this year.")
    st.stop()

# --- CLASS SELECTION FOR RESULT ENTRY ---
classes_list = list(year_data["class_reps"].keys())
selected_class = st.selectbox("Select Class to Update Results", classes_list)

class_info = year_data["class_reps"][selected_class]
candidates = class_info.get("candidates", [])

# Filter out withdrawn candidates (only show Nominated, Elected, or Lost)
active_candidates = [c for c in candidates if c.get("status") != "Withdrawn"]

if not active_candidates:
    st.warning("No active (non-withdrawn) candidates found for this class.")
    st.stop()

st.markdown(f"### Results Management for: **{selected_class}** (Seats: {class_info['seats']})")
st.write("Update each candidate's status based on the election vote count.")

# --- INTERACTIVE STATUS EDITOR ---
with st.form(f"results_form_{selected_class}"):
    updated_statuses = {}
    
    for cand in active_candidates:
        c1, c2, c3, c4 = st.columns([2, 4, 2, 3])
        c1.text(f"Roll: {cand['roll_no']}")
        c2.text(f"{cand['name']}")
        c3.text(f"{cand['gender']}")
        
        current_status = cand.get("status", "Nominated")
        # Default index lookup for selectbox
        status_options = ["Nominated", "Elected", "Lost"]
        default_idx = status_options.index(current_status) if current_status in status_options else 0
        
        new_status = c4.selectbox(
            f"Status_{['id']}", 
            status_options, 
            index=default_idx, 
            key=f"status_{cand['id']}",
            label_visibility="collapsed"
        )
        updated_statuses[cand['id']] = new_status

    submitted = st.form_submit_button("💾 Save Results for This Class", type="primary")
    if submitted:
        for c in year_data["class_reps"][selected_class]["candidates"]:
            if c["id"] in updated_statuses:
                c["status"] = updated_statuses[c["id"]]
        save_data(db)
        st.success(f"Results for {selected_class} saved successfully!")
        st.rerun()

# --- SUMMARY & OFFICIAL WINNERS PDF EXPORT ---
st.markdown("---")
st.markdown("### 🖨️ Official Declaration of Winners")
st.write("Generate the official document listing all officially declared **Elected Class Representatives** across the college. This list will be referenced when nominating candidates for Main Posts (like Chairperson).")

pdf_results = ResultsPDF()
pdf_results.elected_candidates_list(
    "Official Declaration of Elected Class Representatives", 
    year_data["class_reps"], 
    selected_year
)

st.download_button(
    label="📥 Download Official Elected Representatives List (PDF)",
    data=pdf_results.output(dest='S').encode('latin1'),
    file_name=f"Elected_Class_Reps_{selected_year}.pdf"
)
