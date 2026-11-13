import streamlit as st
import pandas as pd
import uuid
import os
import io
import json
from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
import db_utils

st.set_page_config(page_title="Main Post Nominations", page_icon="📝", layout="wide")

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

# --- PDF GENERATOR CLASS (SINGLE COLUMN LAYOUT) ---
class MainNominationPDF(FPDF):
    def header(self):
        if hasattr(self, 'logo_path_val') and self.logo_path_val and os.path.exists(self.logo_path_val):
            self.image(self.logo_path_val, 10, 8, w=20)
            
        self.set_font("Times", "B", 14)
        self.cell(0, 8, getattr(self, 'college_name_val', ''), ln=True, align="C")
        self.cell(0, 8, f"College Union Election {getattr(self, 'year_str', '')}", ln=True, align="C")
        self.cell(0, 8, "LIST OF VALID NOMINATIONS OF", ln=True, align="C")
        self.cell(0, 8, "MAIN POST ELECTION", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Times", "B", 12)
        self.cell(0, 10, "Returning Officer", align="R")

    def draw_post_table(self, post_name, candidates):
        self.set_font("Times", "B", 14)
        self.cell(0, 10, f"Post: {post_name}", ln=True, align="L")
        
        # Table Headers (Full Width = 190mm)
        self.set_font("Times", "B", 12)
        self.cell(15, 10, "SL No", border=1, align="C")
        self.cell(30, 10, "Roll No", border=1, align="C")
        self.cell(75, 10, "Name of Candidate", border=1, align="C")
        self.cell(50, 10, "Class", border=1, align="C")
        self.cell(20, 10, "Gender", border=1, align="C")
        self.ln()
        
        self.set_font("Times", "", 12)
        for idx, cand in enumerate(candidates):
            self.cell(15, 10, str(idx + 1), border=1, align="C")
            self.cell(30, 10, str(cand["roll_no"]), border=1, align="C")
            
            # Auto-shrink logic for name
            name_text = str(cand["name"])
            font_sz = 12
            self.set_font("Times", "", font_sz)
            while self.get_string_width(name_text) > 73 and font_sz > 6:
                font_sz -= 0.5
                self.set_font("Times", "", font_sz)
            self.cell(75, 10, name_text, border=1)
            
            # Auto-shrink logic for class
            class_text = str(cand.get("class_name", ""))
            font_sz_cls = 12
            self.set_font("Times", "", font_sz_cls)
            while self.get_string_width(class_text) > 48 and font_sz_cls > 6:
                font_sz_cls -= 0.5
                self.set_font("Times", "", font_sz_cls)
            self.cell(50, 10, class_text, border=1, align="C")
            
            self.set_font("Times", "", 12)
            g = "M" if cand["gender"] == "Male" else "F"
            self.cell(20, 10, g, border=1, align="C")
            self.ln()
            
        self.ln(5) # Gap between different posts

# --- CACHED FILE GENERATORS (SINGLE COLUMN LAYOUT) ---
@st.cache_data(show_spinner=False)
def get_main_excel_bytes_cached(col_name, yr_str, active_posts, post_data_json):
    post_data = json.loads(post_data_json)
    wb = Workbook()
    ws = wb.active
    ws.title = "Main Nominations"

    font_heading = Font(name="Times New Roman", size=14, bold=True)
    font_header = Font(name="Times New Roman", size=12, bold=True)
    font_data = Font(name="Times New Roman", size=12)
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", shrink_to_fit=True)
    border_thin = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    ws.column_dimensions['A'].width = 8   # SL No
    ws.column_dimensions['B'].width = 15  # Roll No
    ws.column_dimensions['C'].width = 40  # Name
    ws.column_dimensions['D'].width = 25  # Class
    ws.column_dimensions['E'].width = 12  # Gender

    ws.merge_cells('A1:E1'); ws['A1'] = col_name; ws['A1'].font = font_heading; ws['A1'].alignment = align_center
    ws.merge_cells('A2:E2'); ws['A2'] = f"College Union Election {yr_str}"; ws['A2'].font = font_heading; ws['A2'].alignment = align_center
    ws.merge_cells('A3:E3'); ws['A3'] = "LIST OF VALID NOMINATIONS OF"; ws['A3'].font = font_heading; ws['A3'].alignment = align_center
    ws.merge_cells('A4:E4'); ws['A4'] = "MAIN POST ELECTION"; ws['A4'].font = font_heading; ws['A4'].alignment = align_center

    curr_row = 6
    
    for post in active_posts:
        active_cands = sorted([c for c in post_data[post]["candidates"] if c.get("status") == "Nominated"], key=lambda x: x["name"])
        
        ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=5)
        c_post = ws.cell(row=curr_row, column=1, value=f"Post: {post}"); c_post.font = font_heading; c_post.alignment = align_left
        
        ws.cell(row=curr_row+1, column=1, value="SL No").font = font_header; ws.cell(row=curr_row+1, column=1).alignment = align_center; ws.cell(row=curr_row+1, column=1).border = border_thin
        ws.cell(row=curr_row+1, column=2, value="Roll No").font = font_header; ws.cell(row=curr_row+1, column=2).alignment = align_center; ws.cell(row=curr_row+1, column=2).border = border_thin
        ws.cell(row=curr_row+1, column=3, value="Name of Candidate").font = font_header; ws.cell(row=curr_row+1, column=3).alignment = align_center; ws.cell(row=curr_row+1, column=3).border = border_thin
        ws.cell(row=curr_row+1, column=4, value="Class").font = font_header; ws.cell(row=curr_row+1, column=4).alignment = align_center; ws.cell(row=curr_row+1, column=4).border = border_thin
        ws.cell(row=curr_row+1, column=5, value="Gender").font = font_header; ws.cell(row=curr_row+1, column=5).alignment = align_center; ws.cell(row=curr_row+1, column=5).border = border_thin
        
        r = curr_row + 2
        for idx, c in enumerate(active_cands):
            ws.cell(row=r, column=1, value=idx+1).font = font_data; ws.cell(row=r, column=1).alignment = align_center; ws.cell(row=r, column=1).border = border_thin
            ws.cell(row=r, column=2, value=c["roll_no"]).font = font_data; ws.cell(row=r, column=2).alignment = align_center; ws.cell(row=r, column=2).border = border_thin
            ws.cell(row=r, column=3, value=c["name"]).font = font_data; ws.cell(row=r, column=3).alignment = align_left; ws.cell(row=r, column=3).border = border_thin
            ws.cell(row=r, column=4, value=c.get("class_name", "")).font = font_data; ws.cell(row=r, column=4).alignment = align_center; ws.cell(row=r, column=4).border = border_thin
            ws.cell(row=r, column=5, value="M" if c["gender"]=="Male" else "F").font = font_data; ws.cell(row=r, column=5).alignment = align_center; ws.cell(row=r, column=5).border = border_thin
            r += 1
            
        curr_row = r + 1

    for row_idx in range(1, curr_row): ws.row_dimensions[row_idx].height = 20
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

@st.cache_data(show_spinner=False)
def get_main_pdf_bytes_cached(col_name, yr_str, active_posts, post_data_json, logo_p):
    post_data = json.loads(post_data_json)
    pdf = MainNominationPDF()
    pdf.college_name_val = col_name
    pdf.year_str = yr_str
    pdf.logo_path_val = logo_p
    pdf.add_page()
    
    for post in active_posts:
        active_cands = sorted([c for c in post_data[post]["candidates"] if c.get("status") == "Nominated"], key=lambda x: x["name"])
        
        estimated_height = 20 + (len(active_cands) * 10)
        if pdf.get_y() + estimated_height > 270:
            pdf.add_page()
            
        pdf.draw_post_table(post, active_cands)
        
    return pdf.output(dest='S').encode('latin1')

# --- MAIN APP UI ---
st.title("📝 Main Post Nominations")
st.markdown(f"Register candidates for the Main Union Posts at **{college_name}**.")

if "election_years" not in college_data or not college_data["election_years"]:
    st.warning("No election data found. Please set up the Election Year first.")
    st.stop()

available_years = list(college_data["election_years"].keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = college_data["election_years"][selected_year]

if "main_posts_config" not in year_data or not year_data["main_posts_config"]:
    st.warning("Main Posts have not been configured yet. Please configure them first.")
    st.stop()

posts_config = year_data["main_posts_config"]
post_names = [p["post_name"] for p in posts_config]

st.markdown("### 1. Select Post & Search Candidate")
selected_post = st.selectbox("Choose Main Post", post_names)

# --- AUTO-FILL SMART SEARCH LOGIC ---
st.write("Type a Roll Number to auto-fetch details of an **Elected Class Representative**.")
search_roll = st.number_input("🔍 Search Electoral Roll No.", min_value=0, value=0, step=1, help="Leave as 0 to manually type candidate details")

fetched_name = ""
fetched_gender = "Male"
fetched_class = ""

if search_roll > 0:
    class_reps_data = year_data.get("class_reps", {})
    candidate_found = False
    
    for c_name, c_data in class_reps_data.items():
        for cand in c_data.get("candidates", []):
            if cand.get("status") == "Elected" and cand.get("roll_no") == search_roll:
                fetched_name = cand.get("name")
                fetched_gender = cand.get("gender")
                fetched_class = c_name
                candidate_found = True
                break
        if candidate_found:
            break
            
    if candidate_found:
        st.success(f"✅ Candidate Found: **{fetched_name}** ({fetched_class})")
    else:
        st.warning("⚠️ No elected Class Representative found with this Roll Number. You can enter details manually below.")

# Initialize storage for main post candidates
if "main_post_candidates" not in year_data:
    year_data["main_post_candidates"] = {}
if selected_post not in year_data["main_post_candidates"]:
    year_data["main_post_candidates"][selected_post] = {"candidates": []}

st.markdown("### 2. Add / Verify Candidate Details")
with st.form("nomination_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        roll_no = st.number_input("Electoral Roll No.", min_value=1, value=search_roll if search_roll > 0 else 1, step=1)
        cand_name = st.text_input("Candidate Name", value=fetched_name).upper()
    with col2:
        cand_class = st.text_input("Class", value=fetched_class)
        gender_index = 0 if fetched_gender == "Male" else 1
        gender = st.selectbox("Gender", ["Male", "Female"], index=gender_index)
        
    submitted = st.form_submit_button("Submit Nomination", type="primary")
    
    if submitted and cand_name and cand_class:
        candidate_id = f"cand_{str(uuid.uuid4())[:8]}"
        new_candidate = {
            "id": candidate_id,
            "roll_no": roll_no,
            "name": cand_name,
            "class_name": cand_class,
            "gender": gender,
            "status": "Nominated"
        }
        year_data["main_post_candidates"][selected_post]["candidates"].append(new_candidate)
        db_utils.save_data(db)
        st.success(f"Successfully nominated {cand_name} for {selected_post}!")
        st.rerun()

# --- 3. DISPLAY & EXPORT ---
st.markdown("### 3. Current Nominations & Export")

main_post_data = year_data.get("main_post_candidates", {})
posts_with_candidates = []
for post_cfg in posts_config: 
    p_name = post_cfg["post_name"]
    if p_name in main_post_data:
        active = [c for c in main_post_data[p_name].get("candidates", []) if c.get("status") == "Nominated"]
        if active:
            posts_with_candidates.append(p_name)

if not posts_with_candidates:
    st.info("No candidates nominated yet for any Main Post.")
else:
    col_export1, col_export2 = st.columns([1, 1])
    post_data_json_str = json.dumps(main_post_data)
    
    with col_export1:
        excel_bytes = get_main_excel_bytes_cached(college_name, selected_year, posts_with_candidates, post_data_json_str)
        st.download_button(
            label="📥 Download Master Excel (.xlsx)", 
            data=excel_bytes, 
            file_name=f"Main_Post_Nominations_{selected_year}.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
        
    with col_export2:
        pdf_bytes = get_main_pdf_bytes_cached(college_name, selected_year, posts_with_candidates, post_data_json_str, logo_path)
        st.download_button(
            label="📥 Download Master PDF", 
            data=pdf_bytes, 
            file_name=f"Main_Post_Nominations_{selected_year}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )

    st.markdown("---")
    
    current_post_cands = main_post_data.get(selected_post, {}).get("candidates", [])
    active_current_cands = sorted([c for c in current_post_cands if c.get("status") == "Nominated"], key=lambda x: x["name"])
    
    if active_current_cands:
        st.markdown(f"#### Edit Candidates for: {selected_post}")
        
        df = pd.DataFrame(active_current_cands)
        display_df = df[["roll_no", "name", "class_name", "gender"]].rename(
            columns={"roll_no": "Roll No", "name": "Candidate Name", "class_name": "Class", "gender": "Gender"}
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        with st.expander(f"✏️ Edit or Delete entry from {selected_post}"):
            cand_to_edit_id = st.selectbox(
                "Select candidate to edit:", 
                options=[c["id"] for c in active_current_cands],
                format_func=lambda x: next(c["name"] for c in active_current_cands if c["id"] == x),
                key=f"edit_box_{selected_post}"
            )
            
            selected_cand = next(c for c in active_current_cands if c["id"] == cand_to_edit_id)
            
            c_e1, c_e2, c_e3, c_e4 = st.columns([1, 2, 2, 1])
            new_roll = c_e1.number_input("Roll No.", value=int(selected_cand["roll_no"]), step=1, key=f"r_{cand_to_edit_id}")
            new_name = c_e2.text_input("Name", value=selected_cand["name"], key=f"n_{cand_to_edit_id}").upper()
            new_class = c_e3.text_input("Class", value=selected_cand.get("class_name", ""), key=f"c_{cand_to_edit_id}")
            new_gender = c_e4.selectbox("Gender", ["Male", "Female"], index=0 if selected_cand["gender"]=="Male" else 1, key=f"g_{cand_to_edit_id}")
            
            b1, b2 = st.columns(2)
            if b1.button("💾 Save Changes", type="primary", key=f"save_{cand_to_edit_id}"):
                for c in main_post_data[selected_post]["candidates"]:
                    if c["id"] == cand_to_edit_id:
                        c["roll_no"] = new_roll
                        c["name"] = new_name
                        c["class_name"] = new_class
                        c["gender"] = new_gender
                db_utils.save_data(db)
                st.rerun()
                
            if b2.button("🗑️ Delete Entry", key=f"del_{cand_to_edit_id}"):
                year_data["main_post_candidates"][selected_post]["candidates"] = [
                    c for c in current_post_cands if c["id"] != cand_to_edit_id
                ]
                db_utils.save_data(db)
                st.rerun()
