import streamlit as st
import pandas as pd
import uuid
import os
import io
from fpdf import FPDF
import db_utils

st.set_page_config(page_title="Class Rep Nominations", page_icon="📝", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("🔒 Please log in from the Home page to access this module.")
    st.stop()

db = db_utils.load_data()
current_user = st.session_state.username

# Tenant Data Loading
if current_user not in db["users"]: st.stop()
college_id = db["users"][current_user]["college_id"]
if college_id not in db["colleges"]: st.stop()

college_data = db["colleges"][college_id]
college_name = college_data.get("college_name", "COLLEGE UNION ELECTION")
logo_path = college_data.get("logo_path", "")

# --- PDF GENERATOR CLASS ---
class NominationPDF(FPDF):
    def header(self):
        # Draw Logo if exists
        if logo_path and os.path.exists(logo_path):
            self.image(logo_path, 10, 8, w=20)
            
        self.set_font("Arial", "B", 14)
        self.cell(0, 8, college_name, ln=True, align="C")
        
        self.set_font("Arial", "B", 12)
        self.cell(0, 6, f"College Union Election {self.year_str}", ln=True, align="C")
        
        self.set_font("Arial", "B", 11)
        self.cell(0, 6, "LIST OF VALID NOMINATIONS OF CLASS REPRESENTATIVE ELECTION", ln=True, align="C")
        
        self.set_font("Arial", "B", 10)
        self.cell(0, 6, f"Category: {self.category_str}", ln=True, align="C")
        self.ln(5)

    def draw_class_table(self, class_name, candidates, start_x, start_y):
        self.set_xy(start_x, start_y)
        self.set_font("Arial", "B", 10)
        self.cell(90, 6, class_name, ln=False, align="L")
        
        self.set_xy(start_x, start_y + 6)
        self.set_font("Arial", "B", 9)
        self.cell(20, 6, "Roll No", border=1, align="C")
        self.cell(55, 6, "Name", border=1, align="C")
        self.cell(15, 6, "Gender", border=1, align="C")
        
        curr_y = start_y + 12
        self.set_font("Arial", "", 9)
        
        for cand in candidates:
            self.set_xy(start_x, curr_y)
            self.cell(20, 6, str(cand["roll_no"]), border=1, align="C")
            self.cell(55, 6, str(cand["name"]), border=1)
            g = "M" if cand["gender"] == "Male" else "F"
            self.cell(15, 6, g, border=1, align="C")
            curr_y += 6
            
        return curr_y

# --- MAIN APP UI ---
st.title("📝 Class Representative Nominations")
st.markdown(f"Register new candidates for **{college_name}**. All entries are saved as **Nominated**.")

if "election_years" not in college_data or not college_data["election_years"]:
    st.warning("No election data found. Please go to the Home page to set up the Election Year first.")
    st.stop()

available_years = list(college_data["election_years"].keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = college_data["election_years"][selected_year]

st.markdown("### 1. Select Class")
c1, c2, c3, c4 = st.columns(4)

with c1:
    degree_level = st.selectbox("Course Level", ["UG", "PG"])
with c2:
    year_options = ["I", "II", "III", "IV"] if degree_level == "UG" else ["I", "II"]
    course_year = st.selectbox("Year", year_options)
with c3:
    program_list = year_data.get("programs", {}).get(degree_level, [])
    if not program_list:
        st.error(f"No {degree_level} programs found for {selected_year}. Add them on the Home page.")
        st.stop()
    program = st.selectbox("Program", program_list)
with c4:
    class_seats = st.number_input("Number of Seats", min_value=1, value=2)

class_name = f"{course_year} {program}"
st.info(f"Currently managing nominations for: **{class_name}**")

if "class_reps" not in year_data:
    year_data["class_reps"] = {}
    
if class_name not in year_data["class_reps"]:
    year_data["class_reps"][class_name] = {"seats": class_seats, "candidates": []}
else:
    year_data["class_reps"][class_name]["seats"] = class_seats
    db_utils.save_data(db)

st.markdown("### 2. Add Candidate")
with st.form("nomination_form", clear_on_submit=True):
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
        submitted = st.form_submit_button("Submit Nomination")
        
        if submitted and cand_name:
            candidate_id = f"cand_{str(uuid.uuid4())[:8]}"
            new_candidate = {
                "id": candidate_id,
                "roll_no": roll_no,
                "name": cand_name,
                "gender": gender,
                "status": "Nominated"
            }
            
            year_data["class_reps"][class_name]["candidates"].append(new_candidate)
            db_utils.save_data(db)
            st.success(f"Success!")

# --- 3. FILTERED DISPLAY & EXPORT ---
st.markdown(f"### 3. Current Nominations ({course_year} Year {degree_level})")

# Filter logic: Only get classes that match the selected Year and Degree Level
filtered_classes = []
class_reps_data = year_data.get("class_reps", {})

for cls in class_reps_data.keys():
    if cls.startswith(f"{course_year} "):
        prog_part = cls[len(course_year)+1:]
        if prog_part in program_list:
            active_cands = [c for c in class_reps_data[cls].get("candidates", []) if c.get("status") == "Nominated"]
            if active_cands:
                filtered_classes.append(cls)

filtered_classes.sort() # Sort classes alphabetically

if not filtered_classes:
    st.info(f"No candidates nominated yet for any {course_year} {degree_level} classes.")
else:
    # --- EXPORT BUTTONS ---
    col_export1, col_export2 = st.columns([1, 1])
    
    # 1. Generate True Excel (.xlsx)
    flat_data = []
    for cls in filtered_classes:
        cands = [c for c in class_reps_data[cls]["candidates"] if c.get("status") == "Nominated"]
        cands_sorted = sorted(cands, key=lambda x: x["name"])
        for c in cands_sorted:
            flat_data.append({
                "Class": cls,
                "Roll No": c["roll_no"],
                "Candidate Name": c["name"],
                "Gender": c["gender"]
            })
    
    df_export = pd.DataFrame(flat_data)
    
    # Create an in-memory buffer to save the Excel file
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name=f"{course_year} {degree_level}")
    
    with col_export1:
        st.download_button(
            label="📥 Download Excel (.xlsx)", 
            data=buffer.getvalue(), 
            file_name=f"Nominations_{course_year}_{degree_level}.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    # 2. Generate PDF
    with col_export2:
        if st.button("🖨️ Generate 2-Column PDF Report", use_container_width=True, type="primary"):
            pdf = NominationPDF()
            pdf.year_str = selected_year
            pdf.category_str = f"{course_year} Year {degree_level}"
            pdf.add_page()
            
            # Pair classes for 2-column layout (Left and Right)
            pairs = [filtered_classes[i:i+2] for i in range(0, len(filtered_classes), 2)]
            
            for pair in pairs:
                left_class = pair[0]
                right_class = pair[1] if len(pair) > 1 else None
                
                left_cands = sorted([c for c in class_reps_data[left_class]["candidates"] if c.get("status") == "Nominated"], key=lambda x: x["name"])
                right_cands = sorted([c for c in class_reps_data[right_class]["candidates"] if c.get("status") == "Nominated"], key=lambda x: x["name"]) if right_class else []
                
                # Estimate height required to prevent ugly page breaks
                max_cands = max(len(left_cands), len(right_cands))
                estimated_height = 12 + (max_cands * 6)
                
                if pdf.get_y() + estimated_height > 270:
                    pdf.add_page()
                    
                start_y = pdf.get_y()
                
                # Draw Left Column (X = 10)
                end_y_left = pdf.draw_class_table(left_class, left_cands, 10, start_y)
                
                # Draw Right Column (X = 110)
                end_y_right = start_y
                if right_class:
                    end_y_right = pdf.draw_class_table(right_class, right_cands, 110, start_y)
                    
                # Move Y down for the next row of pairs
                pdf.set_y(max(end_y_left, end_y_right) + 10)
                
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            st.download_button(
                label="📥 Click here to download PDF", 
                data=pdf_bytes, 
                file_name=f"Nomination_List_{course_year}_{degree_level}.pdf",
                mime="application/pdf"
            )

    st.markdown("---")
    
    # --- DISPLAY CLASSES IN APP ---
    for cls in filtered_classes:
        cands = class_reps_data[cls].get("candidates", [])
        active_cands = [c for c in cands if c.get("status") == "Nominated"]
        
        # Sort Alphabetically
        active_cands = sorted(active_cands, key=lambda x: x["name"])
        
        st.markdown(f"#### {cls}")
        
        df = pd.DataFrame(active_cands)
        display_df = df[["roll_no", "name", "gender"]].rename(
            columns={"roll_no": "Roll No", "name": "Candidate Name", "gender": "Gender"}
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Unique delete expander for each specific class
        with st.expander(f"Delete an incorrect entry from {cls} (Typo correction)"):
            cand_to_delete = st.selectbox(
                "Select candidate to remove:", 
                options=[c["id"] for c in active_cands],
                format_func=lambda x: next(c["name"] for c in active_cands if c["id"] == x),
                key=f"del_box_{cls}"
            )
            if st.button("Delete Entry", type="primary", key=f"del_btn_{cls}"):
                year_data["class_reps"][cls]["candidates"] = [
                    c for c in class_reps_data[cls]["candidates"] if c["id"] != cand_to_delete
                ]
                db_utils.save_data(db)
                st.rerun()
