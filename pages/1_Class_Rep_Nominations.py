import streamlit as st
import pandas as pd
import json
import os
import uuid

# --- PAGE CONFIG ---
st.set_page_config(page_title="Class Rep Nominations", page_icon="📝", layout="wide")

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

# --- HEADER ---
st.title("📝 Class Representative Nominations")
st.markdown("Register new candidates for Class Representative posts. All entries are saved as **Nominated**.")

# --- YEAR SELECTION ---
if not db:
    st.warning("No election data found. Please go to the Home page (app.py) to set up the Election Year and Programs first.")
    st.stop()

# Let the user select which year they are working on (defaults to the most recently created)
available_years = list(db.keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)

year_data = db[selected_year]

# --- CLASS SELECTION ---
st.markdown("### 1. Select Class")
c1, c2, c3, c4 = st.columns(4)

with c1:
    degree_level = st.selectbox("Course Level", ["UG", "PG"])
with c2:
    year_options = ["I", "II", "III"] if degree_level == "UG" else ["I", "II"]
    course_year = st.selectbox("Year", year_options)
with c3:
    # Pull the exact program list saved for this specific year from the DB
    program_list = year_data.get("programs", {}).get(degree_level, [])
    if not program_list:
        st.error(f"No {degree_level} programs found for {selected_year}. Add them on the Home page.")
        st.stop()
    program = st.selectbox("Program", program_list)
with c4:
    class_seats = st.number_input("Number of Seats", min_value=1, value=2)

class_name = f"{course_year} {program}"
st.info(f"Currently managing nominations for: **{class_name}**")

# Ensure the class exists in the database structure
if "class_reps" not in year_data:
    year_data["class_reps"] = {}
    
if class_name not in year_data["class_reps"]:
    year_data["class_reps"][class_name] = {"seats": class_seats, "candidates": []}
else:
    # Update seats in case it was changed
    year_data["class_reps"][class_name]["seats"] = class_seats
    save_data(db)

# --- CANDIDATE ENTRY FORM ---
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
            # Generate a unique ID for status tracking (withdrawals, results)
            candidate_id = f"cand_{str(uuid.uuid4())[:8]}"
            
            new_candidate = {
                "id": candidate_id,
                "roll_no": roll_no,
                "name": cand_name,
                "gender": gender,
                "status": "Nominated" # Default starting status
            }
            
            # Append and save
            year_data["class_reps"][class_name]["candidates"].append(new_candidate)
            save_data(db)
            st.success(f"Successfully nominated {cand_name}!")

# --- DISPLAY CURRENT NOMINATIONS ---
st.markdown("### 3. Current Nominations")
current_candidates = year_data["class_reps"][class_name]["candidates"]

if current_candidates:
    # Convert to DataFrame for a clean table view, but hide the internal 'id' from the user
    df = pd.DataFrame(current_candidates)
    display_df = df[["roll_no", "name", "gender", "status"]].rename(
        columns={"roll_no": "Roll No", "name": "Candidate Name", "gender": "Gender", "status": "Status"}
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Allow emergency deletion if a typo was made during data entry
    with st.expander("Delete an incorrect entry (Typo correction)"):
        cand_to_delete = st.selectbox(
            "Select candidate to remove from database completely:", 
            options=[c["id"] for c in current_candidates],
            format_func=lambda x: next(c["name"] for c in current_candidates if c["id"] == x)
        )
        if st.button("Delete Entry", type="primary"):
            year_data["class_reps"][class_name]["candidates"] = [
                c for c in current_candidates if c["id"] != cand_to_delete
            ]
            save_data(db)
            st.rerun()
else:
    st.info(f"No candidates nominated yet for {class_name}.")
