import streamlit as st
import pandas as pd
import uuid
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
    # Updated to include "IV" for UG programs
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
            st.success(f"Success")

st.markdown("### 3. Current Nominations (All Classes)")
class_reps_data = year_data.get("class_reps", {})
has_any_candidates = False

# Loop through all classes and display them if they have candidates
for cls, cls_data in class_reps_data.items():
    cands = cls_data.get("candidates", [])
    if cands:
        has_any_candidates = True
        st.markdown(f"#### {cls}")
        
        df = pd.DataFrame(cands)
        display_df = df[["roll_no", "name", "gender", "status"]].rename(
            columns={"roll_no": "Roll No", "name": "Candidate Name", "gender": "Gender", "status": "Status"}
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Unique delete expander for each specific class
        with st.expander(f"Delete an incorrect entry from {cls} (Typo correction)"):
            cand_to_delete = st.selectbox(
                "Select candidate to remove:", 
                options=[c["id"] for c in cands],
                format_func=lambda x: next(c["name"] for c in cands if c["id"] == x),
                key=f"del_box_{cls}"
            )
            if st.button("Delete Entry", type="primary", key=f"del_btn_{cls}"):
                year_data["class_reps"][cls]["candidates"] = [
                    c for c in cands if c["id"] != cand_to_delete
                ]
                db_utils.save_data(db)
                st.rerun()

if not has_any_candidates:
    st.info("No candidates nominated yet for any class.")
