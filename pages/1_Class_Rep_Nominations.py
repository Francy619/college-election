import streamlit as st
import pandas as pd
import uuid
import os
import io
from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
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
            
        self.set_font("Times", "B", 14)
        self.cell(0, 8, college_name, ln=True, align="C")
        
        self.cell(0, 8, f"College Union Election {self.year_str}", ln=True, align="C")
        
        # Split heading to prevent overlap with logo
        self.cell(0, 8, "LIST OF VALID NOMINATIONS OF", ln=True, align="C")
        self.cell(0, 8, "CLASS REPRESENTATIVE ELECTION", ln=True, align="C")
        
        # Extra gap after the main headings
        self.ln(10)

    def draw_class_table(self, class_name, candidates, start_x, start_y):
        # Class Name Heading - Centered relative to the table width (90)
        self.set_xy(start_x, start_y)
        self.set_font("Times", "B", 14)
        self.cell(90, 8, class_name, ln=False, align="C")
        
        # Table Header (with wrapped Electoral Roll No)
        self.set_xy(start_x, start_y + 8)
        self.set_font("Times", "B", 12)
        
        # Draw outer borders for header
        self.rect(start_x, start_y + 8, 25, 12)       # Roll No box
        self.rect(start_x + 25, start_y + 8, 50, 12)  # Name box
        self.rect(start_x + 75, start_y + 8, 15, 12)  # Gender box
        
        # Draw text inside headers
        self.set_xy(start_x, start_y + 8)
        self.cell(25, 6, "Electoral", align="C")
        self.cell(50, 12, "Name", align="C")
        self.cell(15, 12, "Gender", align="C")
        
        self.set_xy(start_x, start_y + 14)
        self.cell(25, 6, "Roll No.", align="C")
        
        # Table Data Rows
        curr_y = start_y + 20
        
        for cand in candidates:
            self.set_xy(start_x, curr_y)
            self.set_font("Times", "", 12) # Reset font to 12 for Roll No
            self.cell(25, 8, str(cand["roll_no"]), border=1, align="C")
            
            # --- AUTO-SHRINK FONT LOGIC FOR LENGTHY NAMES ---
            name_text = str(cand["name"])
            font_sz = 12
            self.set_font("Times", "", font_sz)
            
            # 48 is the max width inside the 50-width cell (leaves 1 unit padding on each side)
            while self.get_string_width(name_text) > 48 and font_sz > 5:
                font_sz -= 0.5
                self.set_font("Times", "", font_sz)
                
            self.cell(50, 8, name_text, border=1)
            # ------------------------------------------------
            
            self.set_font("Times", "", 12) # Reset font to 12 for Gender
            g = "M" if cand["gender"] == "Male" else "F"
            self.cell(15, 8, g, border=1, align="C")
            curr_y += 8
            
        return curr_y

# --- EXCEL GENERATOR FUNCTION ---
def generate_excel_report(col_name, yr_str, filtered_cls, cls_data):
    wb = Workbook()
    ws = wb.active
    ws.title = "Nominations"

    # Styling matches PDF
    font_heading = Font(name="Times New Roman", size=14, bold=True)
    font_header = Font(name="Times New Roman", size=12, bold=True)
    font_data = Font(name="Times New Roman", size=12)
    
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    # Added shrink_to_fit=True so lengthy names shrink to fit the cell width exactly like the PDF
    align_left = Alignment(horizontal="left", vertical="center", shrink_to_fit=True)
    
    border_thin = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # Column Widths
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 5   # Gap between columns
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 30
    ws.column_dimensions['G'].width = 10

    # Main Headings (Merged across both visual columns)
    ws.merge_cells('A1:G1'); ws['A1'] = col_name; ws['A1'].font = font_heading; ws['A1'].alignment = align_center
    ws.merge_cells('A2:G2'); ws['A2'] = f"College Union Election {yr_str}"; ws['A2'].font = font_heading; ws['A2'].alignment = align_center
    ws.merge_cells('A3:G3'); ws['A3'] = "LIST OF VALID NOMINATIONS OF"; ws['A3'].font = font_heading; ws['A3'].alignment = align_center
    ws.merge_cells('A4:G4'); ws['A4'] = "CLASS REPRESENTATIVE ELECTION"; ws['A4'].font = font_heading; ws['A4'].alignment = align_center

    curr_row = 6
    max_used_row = 6
    pairs = [filtered_cls[i:i+2] for i in range(0, len(filtered_cls), 2)]

    for pair in pairs:
        left_class = pair[0]
        right_class = pair[1] if len(pair) > 1 else None

        left_cands = sorted([c for c in cls_data[left_class]["candidates"] if c.get("status") == "Nominated"], key=lambda x: x["name"])
        right_cands = sorted([c for c in cls_data[right_class]["candidates"] if c.get("status") == "Nominated"], key=lambda x: x["name"]) if right_class else []

        # Left Table
        ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=3)
        c_left = ws.cell(row=curr_row, column=1, value=left_class)
        c_left.font = font_heading
        c_left.alignment = align_center
        
        ws.cell(row=curr_row+1, column=1, value="Electoral\nRoll No.").font = font_header; ws.cell(row=curr_row+1, column=1).alignment = align_center; ws.cell(row=curr_row+1, column=1).border = border_thin
        ws.cell(row=curr_row+1, column=2, value="Name").font = font_header; ws.cell(row=curr_row+1, column=2).alignment = align_center; ws.cell(row=curr_row+1, column=2).border = border_thin
        ws.cell(row=curr_row+1, column=3, value="Gender").font = font_header; ws.cell(row=curr_row+1, column=3).alignment = align_center; ws.cell(row=curr_row+1, column=3).border = border_thin

        r_left = curr_row + 2
        for c in left_cands:
            ws.cell(row=r_left, column=1, value=c["roll_no"]).font = font_data; ws.cell(row=r_left, column=1).alignment = align_center; ws.cell(row=r_left, column=1).border = border_thin
            ws.cell(row=r_left, column=2, value=c["name"]).font = font_data; ws.cell(row=r_left, column=2).alignment = align_left; ws.cell(row=r_left, column=2).border = border_thin
            ws.cell(row=r_left, column=3, value="M" if c["gender"]=="Male" else "F").font = font_data; ws.cell(row=r_left, column=3).alignment = align_center; ws.cell(row=r_left, column=3).border = border_thin
            r_left += 1

        # Right Table
        r_right = curr_row + 2
        if right_class:
            ws.merge_cells(start_row=curr_row, start_column=5, end_row=curr_row, end_column=7)
            c_right = ws.cell(row=curr_row, column=5, value=right_class)
            c_right.font = font_heading
            c_right.alignment = align_center
            
            ws.cell(row=curr_row+1, column=5, value="Electoral\nRoll No.").font = font_header; ws.cell(row=curr_row+1, column=5).alignment = align_center; ws.cell(row=curr_row+1, column=5).border = border_thin
            ws.cell(row=curr_row+1, column=6, value="Name").font = font_header; ws.cell(row=curr_row+1, column=6).alignment = align_center; ws.cell(row=curr_row+1, column=6).border = border_thin
            ws.cell(row=curr_row+1, column=7, value="Gender").font = font_header; ws.cell(row=curr_row+1, column=7).alignment = align_center; ws.cell(row=curr_row+1, column=7).border = border_thin

            for c in right_cands:
                ws.cell(row=r_right, column=5, value=c["roll_no"]).font = font_data; ws.cell(row=r_right, column=5).alignment = align_center; ws.cell(row=r_right, column=5).border = border_thin
                ws.cell(row=r_right, column=6, value=c["name"]).font = font_data; ws.cell(row=r_right, column=6).alignment = align_left; ws.cell(row=r_right, column=6).border = border_thin
                ws.cell(row=r_right, column=7, value="M" if c["gender"]=="Male" else "F").font = font_data; ws.cell(row=r_right, column=7).alignment = align_center; ws.cell(row=r_right, column=7).border = border_thin
                r_right += 1

        curr_row = max(r_left, r_right) + 2
        max_used_row = max(max_used_row, curr_row)

    # Set all used row heights to 20
    for r in range(1, max_used_row):
        ws.row_dimensions[r].height = 20

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


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
            st.success(f"Successfully nominated {cand_name}!")

# --- 3. FILTERED DISPLAY & EXPORT ---
st.markdown(f"### 3. Current Nominations ({course_year} Year {degree_level})")

# Filter logic
filtered_classes = []
class_reps_data = year_data.get("class_reps", {})

for cls in class_reps_data.keys():
    if cls.startswith(f"{course_year} "):
        prog_part = cls[len(course_year)+1:]
        if prog_part in program_list:
            active_cands = [c for c in class_reps_data[cls].get("candidates", []) if c.get("status") == "Nominated"]
            if active_cands:
                filtered_classes.append(cls)

filtered_classes.sort()

if not filtered_classes:
    st.info(f"No candidates nominated yet for any {course_year} {degree_level} classes.")
else:
    # --- EXPORT BUTTONS ---
    col_export1, col_export2 = st.columns([1, 1])
    
    with col_export1:
        # Generate 2-Column Styled Excel
        excel_bytes = generate_excel_report(
            college_name, selected_year, filtered_classes, class_reps_data
        )
        st.download_button(
            label="📥 Download Excel (.xlsx)", 
            data=excel_bytes, 
            file_name=f"Nominations_{course_year}_{degree_level}.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col_export2:
        # Generate 2-Column PDF
        if st.button("🖨️ Generate 2-Column PDF Report", use_container_width=True, type="primary"):
            pdf = NominationPDF()
            pdf.year_str = selected_year
            pdf.add_page()
            
            pairs = [filtered_classes[i:i+2] for i in range(0, len(filtered_classes), 2)]
            
            for pair in pairs:
                left_class = pair[0]
                right_class = pair[1] if len(pair) > 1 else None
                
                left_cands = sorted([c for c in class_reps_data[left_class]["candidates"] if c.get("status") == "Nominated"], key=lambda x: x["name"])
                right_cands = sorted([c for c in class_reps_data[right_class]["candidates"] if c.get("status") == "Nominated"], key=lambda x: x["name"]) if right_class else []
                
                max_cands = max(len(left_cands), len(right_cands))
                estimated_height = 20 + (max_cands * 8)
                
                if pdf.get_y() + estimated_height > 270:
                    pdf.add_page()
                    
                start_y = pdf.get_y()
                
                # Draw Left Column
                end_y_left = pdf.draw_class_table(left_class, left_cands, 10, start_y)
                
                # Draw Right Column
                end_y_right = start_y
                if right_class:
                    end_y_right = pdf.draw_class_table(right_class, right_cands, 110, start_y)
                    
                pdf.set_y(max(end_y_left, end_y_right) + 10)
                
            st.download_button(
                label="📥 Click here to download PDF", 
                data=pdf.output(dest='S').encode('latin1'), 
                file_name=f"Nomination_List_{course_year}_{degree_level}.pdf",
                mime="application/pdf"
            )

    st.markdown("---")
    
    # --- DISPLAY CLASSES IN APP ---
    for cls in filtered_classes:
        cands = class_reps_data[cls].get("candidates", [])
        active_cands = sorted([c for c in cands if c.get("status") == "Nominated"], key=lambda x: x["name"])
        
        st.markdown(f"#### {cls}")
        
        df = pd.DataFrame(active_cands)
        display_df = df[["roll_no", "name", "gender"]].rename(
            columns={"roll_no": "Roll No", "name": "Candidate Name", "gender": "Gender"}
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
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
