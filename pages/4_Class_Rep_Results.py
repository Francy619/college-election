import streamlit as st
import pandas as pd
import json
import os
import io
from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
import db_utils

st.set_page_config(page_title="Class Rep Results", page_icon="🏆", layout="wide")

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
class ResultsPDF(FPDF):
    def header(self):
        if hasattr(self, 'logo_path_val') and self.logo_path_val and os.path.exists(self.logo_path_val):
            self.image(self.logo_path_val, 10, 8, w=20)
            
        self.set_font("Times", "B", 14)
        self.cell(0, 8, getattr(self, 'college_name_val', ''), ln=True, align="C")
        self.cell(0, 8, f"College Union Election {getattr(self, 'year_str', '')}", ln=True, align="C")
        self.cell(0, 8, "LIST OF CLASS REPRESENTATIVES", ln=True, align="C")
        self.cell(0, 8, "CLASS REPRESENTATIVE ELECTION", ln=True, align="C")
        self.ln(10)

    def footer(self):
        # Position at 15 mm from bottom
        self.set_y(-15)
        self.set_font("Times", "B", 12)
        self.cell(0, 10, "Returning Officer", align="R")

    def draw_class_table(self, class_name, candidates, start_x, start_y):
        self.set_xy(start_x, start_y)
        self.set_font("Times", "B", 14)
        self.cell(90, 8, class_name, ln=False, align="C")
        
        self.set_xy(start_x, start_y + 8)
        self.set_font("Times", "B", 12)
        
        self.rect(start_x, start_y + 8, 25, 12)       
        self.rect(start_x + 25, start_y + 8, 50, 12)  
        self.rect(start_x + 75, start_y + 8, 15, 12)  
        
        self.set_xy(start_x, start_y + 8)
        self.cell(25, 6, "Electoral", align="C")
        self.cell(50, 12, "Name", align="C")
        self.cell(15, 12, "Gender", align="C")
        
        self.set_xy(start_x, start_y + 14)
        self.cell(25, 6, "Roll No.", align="C")
        
        curr_y = start_y + 20
        
        for cand in candidates:
            self.set_xy(start_x, curr_y)
            self.set_font("Times", "", 12)
            self.cell(25, 8, str(cand["roll_no"]), border=1, align="C")
            
            name_text = str(cand["name"])
            font_sz = 12
            self.set_font("Times", "", font_sz)
            while self.get_string_width(name_text) > 48 and font_sz > 5:
                font_sz -= 0.5
                self.set_font("Times", "", font_sz)
                
            self.cell(50, 8, name_text, border=1)
            
            self.set_font("Times", "", 12)
            g = "M" if cand["gender"] == "Male" else "F"
            self.cell(15, 8, g, border=1, align="C")
            curr_y += 8
            
        return curr_y

# --- CACHED FILE GENERATORS ---
@st.cache_data(show_spinner=False)
def get_results_excel_bytes_cached(col_name, yr_str, filtered_cls, cls_data_json):
    cls_data = json.loads(cls_data_json)
    wb = Workbook()
    ws = wb.active
    ws.title = "Elected Reps"

    font_heading = Font(name="Times New Roman", size=14, bold=True)
    font_header = Font(name="Times New Roman", size=12, bold=True)
    font_data = Font(name="Times New Roman", size=12)
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", shrink_to_fit=True)
    border_thin = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 5 
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 30
    ws.column_dimensions['G'].width = 10

    ws.merge_cells('A1:G1'); ws['A1'] = col_name; ws['A1'].font = font_heading; ws['A1'].alignment = align_center
    ws.merge_cells('A2:G2'); ws['A2'] = f"College Union Election {yr_str}"; ws['A2'].font = font_heading; ws['A2'].alignment = align_center
    ws.merge_cells('A3:G3'); ws['A3'] = "LIST OF CLASS REPRESENTATIVES"; ws['A3'].font = font_heading; ws['A3'].alignment = align_center

    curr_row = 6
    max_used_row = 6
    pairs = [filtered_cls[i:i+2] for i in range(0, len(filtered_cls), 2)]

    for pair in pairs:
        left_class = pair[0]
        right_class = pair[1] if len(pair) > 1 else None

        # Filter ONLY Elected candidates
        left_cands = sorted([c for c in cls_data[left_class]["candidates"] if c.get("status") == "Elected"], key=lambda x: x["name"])
        right_cands = sorted([c for c in cls_data[right_class]["candidates"] if c.get("status") == "Elected"], key=lambda x: x["name"]) if right_class else []

        ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=3)
        c_left = ws.cell(row=curr_row, column=1, value=left_class); c_left.font = font_heading; c_left.alignment = align_center
        ws.cell(row=curr_row+1, column=1, value="Electoral\nRoll No.").font = font_header; ws.cell(row=curr_row+1, column=1).alignment = align_center; ws.cell(row=curr_row+1, column=1).border = border_thin
        ws.cell(row=curr_row+1, column=2, value="Name").font = font_header; ws.cell(row=curr_row+1, column=2).alignment = align_center; ws.cell(row=curr_row+1, column=2).border = border_thin
        ws.cell(row=curr_row+1, column=3, value="Gender").font = font_header; ws.cell(row=curr_row+1, column=3).alignment = align_center; ws.cell(row=curr_row+1, column=3).border = border_thin

        r_left = curr_row + 2
        for c in left_cands:
            ws.cell(row=r_left, column=1, value=c["roll_no"]).font = font_data; ws.cell(row=r_left, column=1).alignment = align_center; ws.cell(row=r_left, column=1).border = border_thin
            ws.cell(row=r_left, column=2, value=c["name"]).font = font_data; ws.cell(row=r_left, column=2).alignment = align_left; ws.cell(row=r_left, column=2).border = border_thin
            ws.cell(row=r_left, column=3, value="M" if c["gender"]=="Male" else "F").font = font_data; ws.cell(row=r_left, column=3).alignment = align_center; ws.cell(row=r_left, column=3).border = border_thin
            r_left += 1

        r_right = curr_row + 2
        if right_class:
            ws.merge_cells(start_row=curr_row, start_column=5, end_row=curr_row, end_column=7)
            c_right = ws.cell(row=curr_row, column=5, value=right_class); c_right.font = font_heading; c_right.alignment = align_center
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

    for r in range(1, max_used_row + 2): ws.row_dimensions[r].height = 20
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

@st.cache_data(show_spinner=False)
def get_results_pdf_bytes_cached(col_name, yr_str, filtered_cls, cls_data_json, logo_p):
    cls_data = json.loads(cls_data_json)
    pdf = ResultsPDF()
    pdf.college_name_val = col_name
    pdf.year_str = yr_str
    pdf.logo_path_val = logo_p
    pdf.add_page()
    
    pairs = [filtered_cls[i:i+2] for i in range(0, len(filtered_cls), 2)]
    
    for pair in pairs:
        left_class = pair[0]
        right_class = pair[1] if len(pair) > 1 else None
        
        # Filter ONLY Elected candidates
        left_cands = sorted([c for c in cls_data[left_class]["candidates"] if c.get("status") == "Elected"], key=lambda x: x["name"])
        right_cands = sorted([c for c in cls_data[right_class]["candidates"] if c.get("status") == "Elected"], key=lambda x: x["name"]) if right_class else []
        
        # If neither class in the pair has elected candidates, skip drawing them
        if not left_cands and not right_cands:
            continue
            
        max_cands = max(len(left_cands), len(right_cands))
        estimated_height = 20 + (max_cands * 8)
        
        if pdf.get_y() + estimated_height > 260:
            pdf.add_page()
            
        start_y = pdf.get_y()
        end_y_left = start_y
        end_y_right = start_y
        
        if left_cands:
            end_y_left = pdf.draw_class_table(left_class, left_cands, 10, start_y)
        if right_class and right_cands:
            end_y_right = pdf.draw_class_table(right_class, right_cands, 110, start_y)
            
        pdf.set_y(max(end_y_left, end_y_right) + 10)
        
    return pdf.output(dest='S').encode('latin1')

# --- MAIN UI ---
st.title("🏆 Class Representative Election Results")

if "election_years" not in college_data or not college_data["election_years"]:
    st.warning("No election data found. Please set up the election first.")
    st.stop()

available_years = list(college_data["election_years"].keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = college_data["election_years"][selected_year]

class_reps_data = year_data.get("class_reps", {})

if not class_reps_data:
    st.info("No class representatives have been nominated for this year yet.")
    st.stop()

# --- 1. FILTER CONTROLS ---
st.markdown("### 1. Filter & Select Class")
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
        
    prog_filter = st.selectbox("Program", progs)

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

if not filtered_classes:
    st.warning("No classes configured for this filter.")
    st.stop()

# Select a specific class from the filtered list to edit
selected_class = st.selectbox("Select Class to Update Results", filtered_classes)
class_info = class_reps_data[selected_class]
active_candidates = [c for c in class_info.get("candidates", []) if c.get("status") != "Withdrawn"]

# --- 2. MANAGE RESULTS ---
st.markdown("---")
st.markdown(f"### 2. Enter Results for: **{selected_class}**")

if not active_candidates:
    st.info("No active candidates found for this class.")
else:
    flat_candidates = []
    for cand in active_candidates:
        # Default to Lost if they are currently just "Nominated"
        current = cand.get("status", "Nominated")
        display_status = "Lost" if current == "Nominated" else current
        
        flat_candidates.append({
            "ID": cand["id"],
            "Roll No": cand["roll_no"],
            "Name": cand["name"],
            "Gender": cand["gender"],
            "Status": display_status
        })

    df = pd.DataFrame(flat_candidates)
    
    st.write("Mark the winning candidate(s) as **Elected**. All others will be saved as **Lost**.")
    
    edited_df = st.data_editor(
        df,
        column_config={
            "ID": None,
            "Roll No": st.column_config.NumberColumn(disabled=True),
            "Name": st.column_config.TextColumn(disabled=True),
            "Gender": st.column_config.TextColumn(disabled=True),
            "Status": st.column_config.SelectboxColumn("Status", options=["Elected", "Lost"], required=True)
        },
        use_container_width=True,
        hide_index=True,
        key=f"results_editor_{selected_class}"
    )

    if st.button("💾 Save Results", type="primary"):
        for index, row in edited_df.iterrows():
            cand_id = row["ID"]
            new_status = row["Status"]
            
            for c in class_reps_data[selected_class]["candidates"]:
                if c["id"] == cand_id:
                    c["status"] = new_status
                    break
        db_utils.save_data(db)
        st.success(f"Results saved for {selected_class}!")
        st.rerun()

# --- 3. EXPORT RESULTS ---
st.markdown("---")
st.markdown("### 3. 🖨️ Official Declaration of Winners")
st.write("Exports include **only Elected** candidates.")

tab1, tab2 = st.tabs(["📄 Yearwise/Filtered Export", "📚 Complete College Export"])

cls_data_json_str = json.dumps(class_reps_data)
all_classes_sorted = sorted(list(class_reps_data.keys()))

with tab1:
    c_exp1, c_exp2 = st.columns(2)
    
    with c_exp1:
        excel_bytes_filtered = get_results_excel_bytes_cached(college_name, selected_year, filtered_classes, cls_data_json_str)
        st.download_button(
            label="📥 Download Filtered Excel (.xlsx)", 
            data=excel_bytes_filtered, 
            file_name=f"Elected_Reps_Filtered.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with c_exp2:
        pdf_bytes_filtered = get_results_pdf_bytes_cached(college_name, selected_year, filtered_classes, cls_data_json_str, logo_path)
        st.download_button(
            label="📥 Download Filtered PDF", 
            data=pdf_bytes_filtered, 
            file_name=f"Elected_Reps_Filtered.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )

with tab2:
    st.caption("Exporting the official declaration for ALL classes across the entire college.")
    c_exp3, c_exp4 = st.columns(2)
    
    with c_exp3:
        excel_bytes_all = get_results_excel_bytes_cached(college_name, selected_year, all_classes_sorted, cls_data_json_str)
        st.download_button(
            label="📥 Download Complete Excel (.xlsx)", 
            data=excel_bytes_all, 
            file_name=f"Elected_Reps_Complete_{selected_year}.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with c_exp4:
        pdf_bytes_all = get_results_pdf_bytes_cached(college_name, selected_year, all_classes_sorted, cls_data_json_str, logo_path)
        st.download_button(
            label="📥 Download Complete PDF", 
            data=pdf_bytes_all, 
            file_name=f"Elected_Reps_Complete_{selected_year}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
