import streamlit as st
import pandas as pd
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Main Post Configuration", page_icon="⚙️", layout="wide")

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

# --- HEADER ---
st.title("⚙️ Main Union Post Configuration")
st.markdown("Define the executive posts for the College Union election (e.g., Chairperson, General Secretary, UUC) and specify how many seats each post carries.")

if not db:
    st.warning("No election data found.")
    st.stop()

available_years = list(db.keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = db[selected_year]

# Ensure configuration dictionary exists
if "main_posts_config" not in year_data:
    year_data["main_posts_config"] = [
        {"post_name": "The Chairperson", "seats": 1},
        {"post_name": "General Secretary", "seats": 1},
        {"post_name": "University Union Councillor (UUC)", "seats": 2}
    ]
    save_data(db)

if "main_post_candidates" not in year_data:
    year_data["main_post_candidates"] = {}
    save_data(db)

posts_config = year_data["main_posts_config"]

# --- ADD NEW POST FORM ---
st.markdown("### Add New Main Post")
with st.form("add_post_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        new_post_name = st.text_input("Name of the Post (e.g., Magazine Editor)").title()
    with col2:
        new_seats = st.number_input("Number of Seats", min_value=1, value=1)
    with col3:
        st.write("")
        st.write("")
        add_submitted = st.form_submit_button("Add Post", type="primary")
        if add_submitted and new_post_name:
            # Check if post already exists
            existing_names = [p["post_name"] for p in posts_config]
            if new_post_name in existing_names:
                st.error("A post with this name already exists!")
            else:
                posts_config.append({"post_name": new_post_name, "seats": int(new_seats)})
                save_data(db)
                st.success(f"Added '{new_post_name}' successfully!")
                st.rerun()

# --- EDIT / REMOVE EXISTING POSTS ---
st.markdown("### Configured Posts for " + selected_year)

if posts_config:
    # Convert configuration to a dataframe for clean visualization
    df_posts = pd.DataFrame(posts_config)
    
    # We allow modifying seat counts or deleting posts
    for idx, post in enumerate(posts_config):
        c1, c2, c3 = st.columns([4, 2, 2])
        c1.text(f"📌 {post['post_name']}")
        
        # Quick seat adjustment
        updated_seats = c2.number_input(
            f"Seats_{idx}", 
            min_value=1, 
            value=post['seats'], 
            key=f"seats_val_{idx}",
            label_visibility="collapsed"
        )
        if updated_seats != post['seats']:
            posts_config[idx]['seats'] = updated_seats
            save_data(db)
            
        if c3.button("🗑️ Delete", key=f"del_post_{idx}"):
            post_to_remove = post['post_name']
            # Remove from config
            posts_config.pop(idx)
            # Remove candidates record if any exists
            if post_to_remove in year_data["main_post_candidates"]:
                del year_data["main_post_candidates"][post_to_remove]
            save_data(db)
            st.success(f"Removed {post_to_remove}.")
            st.rerun()
else:
    st.info("No main posts configured yet. Add one above.")

st.markdown("---")
st.info("💡 **Next Step:** Once your main posts are configured here, navigate to **6. Main Post Elections** in the sidebar to nominate winning Class Representatives and generate ballots for these central posts.")

<ElicitationsGroup message="Next steps for your application:">
  <Elicitation label="Build Main Post Elections Page" query="Provide the Streamlit code for 'pages/6_Main_Post_Elections.py' where winning class reps can run for main executive positions."/>
</ElicitationsGroup>
