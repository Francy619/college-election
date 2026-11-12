import streamlit as st
import pandas as pd
from fpdf import FPDF
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Withdrawals & Final List", page_icon="🛑", layout="wide")

# --- DATABASE HELPER FUNCTIONS ---
DATA_FILE = "election_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# --- PDF GENERATION CLASS ---
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
            # Filter candidates: Only include those who are strictly "Nominated"
            active_candidates = [c for c in data.get('candidates', []) if c.get('status') == "Nominated"]
            
            # Skip printing this class entirely if everyone withdrew or no one was nominated
            if not active_candidates:
                continue
                
            self.set_font("Arial", "BU", 11)
            label = "Class" if is_class else "Post"
            self.cell(0, 10, f"{label}: {heading} (Seats: {data['seats']})", ln=True, align="L")
            
            # Table Header
            self.set_font("Arial", "B", 10)
            self.cell(20, 8, "SL No", border=1, align="C")
            self.cell(40, 8, "Electoral Roll No", border=1, align="C")
            self.cell(90, 8, "Name of Candidate", border=1, align="C")
            if is_class:
                self.cell(40, 8, "Gender", border=1, align="C")
            self.ln()
            
            # Table Data
            self.set_font("Arial", "", 10)
            for idx, cand in enumerate(active_candidates):
                self.cell(20, 8, str(idx+1), border=1, align="C")
                self.cell(40, 8, str(cand['roll_no']), border=1, align="C")
                self.cell(90, 8, str(cand['name']), border=1)
                if is_class:
                    self.cell(40, 8, str(cand['gender']), border=1, align="C")
                self.ln()
            self.ln(5) 

# --- HEADER ---
st.title("🛑 Scrutiny & Withdrawals")
st.markdown("Manage candidate withdrawals and generate the final list of valid contestants for the ballot.")

if not db:
    st.warning("No election data found. Please set up the election and add nominations first.")
    st.stop()

available_years = list(db.keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = db[selected_year]

if "class_reps" not in year_data or not year_data["class_reps"]:
    st.info("No class representatives have been nominated for this year yet.")
    st.stop()

# --- FLATTEN DATA FOR EDITOR ---
# We extract all candidates into a flat list so we can edit them in one big table
flat_candidates = []
for c_name, c_data in year_data["class_reps"].items():
    for cand in c_data["candidates"]:
        flat_candidates.append({
            "ID": cand["id"],
            "Class": c_name,
            "Roll No": cand["roll_no"],
            "Name": cand["name"],
            "Gender": cand["gender"],
            "Status": cand.get("status", "Nominated")
        })

if not flat_candidates:
    st.info("No candidates found.")
    st.stop()

df = pd.DataFrame(flat_candidates)

# --- WITHDRAWAL MANAGEMENT (DATA EDITOR) ---
st.markdown("### Manage Candidate Status")
st.write("Double-click a cell in the **Status** column to change a candidate from `Nominated` to `Withdrawn`.")

# Create an editable dataframe where ONLY the 'Status' column can be changed
edited_df = st.data_editor(
    df,
    column_config={
        "ID": None, # Hide the internal ID from the user
        "Class": st.column_config.TextColumn(disabled=True),
        "Roll No": st.column_config.NumberColumn(disabled=True),
        "Name": st.column_config.TextColumn(disabled=True),
        "Gender": st.column_config.TextColumn(disabled=True),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Change to Withdrawn to remove them from the ballot",
            options=["Nominated", "Withdrawn"],
            required=True
        )
    },
    use_container_width=True,
    hide_index=True,
    key="withdrawal_editor"
)

# --- SAVE CHANGES LOGIC ---
if st.button("💾 Save Status Changes", type="primary"):
    # Iterate through the edited dataframe and update the main JSON database
    for index, row in edited_df.iterrows():
        cand_id = row["ID"]
        class_name = row["Class"]
        new_status = row["Status"]
        
        # Find the specific candidate in the nested JSON and update their status
        for c in year_data["class_reps"][class_name]["candidates"]:
            if c["id"] == cand_id:
                c["status"] = new_status
                break
                
    save_data(db)
    st.success("Candidate statuses updated successfully! The final lists and ballots will now reflect these changes.")
    st.rerun()

# --- SUMMARY & PDF GENERATION ---
st.markdown("---")
st.markdown("### 🖨️ Final List Generation")

# Calculate summary stats
total_noms = len(df)
withdrawn_count = len(df[df["Status"] == "Withdrawn"])
active_count = total_noms - withdrawn_count

col1, col2, col3 = st.columns(3)
col1.metric("Total Nominations", total_noms)
col2.metric("Total Withdrawn", withdrawn_count)
col3.metric("Final Active Candidates", active_count)

st.write("Click below to generate the official **Final Valid Candidate List**. Candidates marked as 'Withdrawn' above will be automatically excluded from this document.")

pdf_list = ElectionPDF()
pdf_list.consolidated_candidate_list(
    "Final Valid Candidate List - Class Representatives", 
    year_data["class_reps"], 
    selected_year, 
    is_class=True
)

st.download_button(
    label="📥 Download Final Valid Candidate List (PDF)", 
    data=pdf_list.output(dest='S').encode('latin1'), 
    file_name=f"Final_Class_Reps_List_{selected_year}.pdf"
)
