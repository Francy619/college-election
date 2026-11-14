import streamlit as st
import pandas as pd
import json
import os
import io
from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
import db_utils

st.set_page_config(page_title="Main Post Results", page_icon="🏆", layout="wide")

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
class MainResultsPDF(FPDF):
    def header(self):
        if hasattr(self, 'logo_path_val') and self.logo_path_val and os.path.exists(self.logo_path_val):
            self.image(self.logo_path_val, 10, 8, w=20)
            
        self.set_font("Times", "B", 14)
        self.cell(0, 8, getattr(self, 'college_name_val', ''), ln=True, align="C")
        self.cell(0, 8, f"College Union Election {getattr(self, 'year_str', '')}", ln=True, align="C")
        self.cell(0, 8, "OFFICIAL DECLARATION OF RESULTS", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Times", "B", 12)
        self.cell(0, 10, "Returning Officer", align="R")

    def draw_post_table(self, post_name, candidates):
        # Auto-shrink logic for extremely long post names to keep them perfectly centered
        font_sz_title = 14
        self.set_font("Times", "B", font_sz_title)
        while self.get_string_width(post_name) > 180 and font_sz_title > 8:
            font_sz_title -= 0.5
            self.set_font("Times", "B", font_sz_title)
            
        # Post name centered, no "Post: " prefix
        self.cell(0, 10, post_name, ln=True, align="C")
        
        # Table Headers (Full Width = 190mm)
        self.set_font("Times", "B", 12)
        self.cell(15, 10, "SL No", border=1, align="C")
        self.cell(30, 10, "Roll No", border=1, align="C")
        self.cell(75, 10, "Name of Winner", border=1, align="C")
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
            
        self.ln(5)

# --- CACHED FILE GENERATORS ---
@st.cache_data(show_spinner=False)
def get_main_results_excel_bytes(col_name, yr_str, active_posts, post_data_json):
    post_data = json.loads(post_data_json)
    wb = Workbook()
    ws = wb.active
    ws.title = "Main Post Results"

    font_heading = Font(name="Times New Roman", size=14, bold=True)
    font_header = Font(name="Times New Roman", size=12, bold=True)
    font_data = Font(name="Times New Roman", size=12)
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", shrink_to_fit=True)
    border_thin = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 40
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 12

    ws.merge_cells('A1:E1'); ws['A1'] = col_name; ws['A1'].font = font_heading; ws['A1'].alignment = align_center
    ws.merge_cells('A2:E2'); ws['A2'] = f"College Union Election {yr_str}"; ws['A2'].font = font_heading; ws['A2'].alignment = align_center
    ws.merge_cells('A3:E3'); ws['A3'] = "OFFICIAL DECLARATION OF RESULTS"; ws['A3'].font = font_heading; ws['A3'].alignment = align_center

    curr_row = 5
    for post in active_posts:
        active_cands = sorted([c for c in post_data[post]["candidates"] if c.get("status") == "Elected"], key=lambda x: x["name"])
        if not active_cands:
            continue
            
        ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=5)
        # Post name centered, no "Post: " prefix
        c_post = ws.cell(row=curr_row, column=1, value=post); c_post.font = font_heading; c_post.alignment = align_center
        
        ws.cell(row=curr_row+1, column=1, value="SL No").font = font_header; ws.cell(row=curr_row+1, column=1).alignment = align_center; ws.cell(row=curr_row+1, column=1).border = border_thin
        ws.cell(row=curr_row+1, column=2, value="Roll No").font = font_header; ws.cell(row=curr_row+1, column=2).alignment = align_center; ws.cell(row=curr_row+1, column=2).border = border_thin
        ws.cell(row=curr_row+1, column=3, value="Name of Winner").font = font_header; ws.cell(row=curr_row+1, column=3).alignment = align_center; ws.cell(row=curr_row+1, column=3).border = border_thin
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
            
        curr_row = r + 2

    for row_idx in range(1, curr_row): ws.row_dimensions[row_idx].height = 20
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

@st.cache_data(show_spinner=False)
def get_main_results_pdf_bytes(col_name, yr_str, active_posts, post_data_json, logo_p):
    post_data = json.loads(post_data_json)
    pdf = MainResultsPDF()
    pdf.college_name_val = col_name
    pdf.year_str = yr_str
    pdf.logo_path_val = logo_p
    pdf.add_page()
    
    for post in active_posts:
        active_cands = sorted([c for c in post_data[post]["candidates"] if c.get("status") == "Elected"], key=lambda x: x["name"])
        
        if not active_cands:
            continue
            
        estimated_height = 20 + (len(active_cands) * 10)
        if pdf.get_y() + estimated_height > 270:
            pdf.add_page()
            
        pdf.draw_post_table(post, active_cands)
        
    return pdf.output(dest='S').encode('latin1')


# --- MAIN APP UI ---
st.title("🏆 Main Post Election Results")
st.markdown("Tally votes, record the winners for the Main Posts, and generate the Official Declaration.")

if "election_years" not in college_data or not college_data["election_years"]:
    st.warning("No election data found. Please set up the election first.")
    st.stop()

available_years = list(college_data["election_years"].keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = college_data["election_years"][selected_year]

if "main_post_candidates" not in year_data or not year_data["main_post_candidates"]:
    st.info("No candidates have been nominated for any Main Post this year yet.")
    st.stop()

main_post_data = year_data["main_post_candidates"]
posts_config = year_data.get("main_posts_config", [])

# Determine posts that have at least one active (Nominated or Elected) candidate
configured_posts_with_cands = [
    p["post_name"] for p in posts_config 
    if p["post_name"] in main_post_data and 
    any(c.get("status") != "Withdrawn" for c in main_post_data[p["post_name"]].get("candidates", []))
]

if not configured_posts_with_cands:
    st.info("No active candidates found. All candidates may have withdrawn.")
    st.stop()

# --- 1. MANAGE RESULTS ---
st.markdown("### 1. Enter Results")
selected_post = st.selectbox("Select Post to Update Results", configured_posts_with_cands)

# Fetch available seats for the selected post
available_seats = next((p["seats"] for p in posts_config if p["post_name"] == selected_post), 1)
active_candidates = [c for c in main_post_data[selected_post].get("candidates", []) if c.get("status") != "Withdrawn"]

flat_candidates = []
for cand in active_candidates:
    current = cand.get("status", "Nominated")
    
    if current == "Nominated":
        # Smart Auto-Election Logic based on available seats!
        if len(active_candidates) <= available_seats:
            display_status = "Elected"
        else:
            display_status = "Lost"
    else:
        display_status = current
        
    flat_candidates.append({
        "ID": cand["id"],
        "Roll No": cand["roll_no"],
        "Name": cand["name"],
        "Class": cand.get("class_name", ""),
        "Status ✏️": display_status
    })

df = pd.DataFrame(flat_candidates)
st.write(f"This post has **{available_seats} seat(s)** available. Mark the winning candidate(s) as **Elected**.")
if len(active_candidates) <= available_seats:
    st.success("✨ Candidates are unopposed and have been automatically marked as **Elected**.")

edited_df = st.data_editor(
    df,
    column_config={
        "ID": None,
        "Roll No": st.column_config.NumberColumn(disabled=True),
        "Name": st.column_config.TextColumn(disabled=True),
        "Class": st.column_config.TextColumn(disabled=True),
        "Status ✏️": st.column_config.SelectboxColumn("Status ✏️", options=["Elected", "Lost"], required=True)
    },
    use_container_width=True,
    hide_index=True,
    key=f"main_results_editor_{selected_post}"
)

if st.button("💾 Save Results", type="primary"):
    for index, row in edited_df.iterrows():
        cand_id = row["ID"]
        new_status = row["Status ✏️"]
        
        for c in main_post_data[selected_post]["candidates"]:
            if c["id"] == cand_id:
                c["status"] = new_status
                break
    db_utils.save_data(db)
    st.success(f"Results saved for {selected_post}!")
    st.rerun()

# --- 2. EXPORT FINAL RESULTS ---
st.markdown("---")
st.markdown("### 2. 🖨️ Official Declaration of Main Post Winners")
st.write("Generates the final list of **Elected** candidates across all Main Posts.")

# Pre-filter to PREVENT GAPS: Only include posts that actually have Elected candidates
valid_posts = []
for p_name in configured_posts_with_cands:
    if any(c.get("status") == "Elected" for c in main_post_data[p_name].get("candidates", [])):
        valid_posts.append(p_name)

if not valid_posts:
    st.info("No candidates have been marked as Elected yet.")
else:
    c_exp1, c_exp2 = st.columns(2)
    post_data_json_str = json.dumps(main_post_data)
    
    with c_exp1:
        excel_bytes = get_main_results_excel_bytes(college_name, selected_year, configured_posts_with_cands, post_data_json_str)
        st.download_button(
            label="📥 Download Master Declaration Excel (.xlsx)", 
            data=excel_bytes, 
            file_name=f"Main_Post_Results_{selected_year}.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with c_exp2:
        pdf_bytes = get_main_results_pdf_bytes(college_name, selected_year, configured_posts_with_cands, post_data_json_str, logo_path)
        st.download_button(
            label="📥 Download Master Declaration PDF", 
            data=pdf_bytes, 
            file_name=f"Main_Post_Results_{selected_year}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )

# --- INJECT FOOTER ---
if hasattr(db_utils, 'add_footer'):
    db_utils.add_footer()
