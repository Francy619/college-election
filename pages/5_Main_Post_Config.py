import streamlit as st
import pandas as pd
import db_utils

st.set_page_config(page_title="Main Post Configuration", page_icon="⚙️", layout="wide")

if not st.session_state.get("authenticated", False):
    st.warning("🔒 Please log in from the Home page to access this module.")
    st.stop()

db = db_utils.load_data()
current_user = st.session_state.username

if current_user not in db["users"]: st.stop()
college_id = db["users"][current_user]["college_id"]
if college_id not in db["colleges"]: st.stop()

college_data = db["colleges"][college_id]

st.title("⚙️ Main Union Post Configuration")

if "election_years" not in college_data or not college_data["election_years"]:
    st.warning("No election data found.")
    st.stop()

available_years = list(college_data["election_years"].keys())
selected_year = st.selectbox("Select Election Year", available_years, index=len(available_years)-1)
year_data = college_data["election_years"][selected_year]

if "main_posts_config" not in year_data:
    year_data["main_posts_config"] = []

posts_config = year_data["main_posts_config"]

st.markdown("### Add New Main Post")
with st.form("add_post_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        new_post_name = st.text_input("Name of the Post").strip()
    with col2:
        new_seats = st.number_input("Number of Seats", min_value=1, value=1)
    with col3:
        st.write("")
        st.write("")
        if st.form_submit_button("Add Post", type="primary") and new_post_name:
            existing_names = [p["post_name"] for p in posts_config]
            if new_post_name in existing_names:
                st.error("Post already exists!")
            else:
                posts_config.append({"post_name": new_post_name, "seats": int(new_seats)})
                db_utils.save_data(db)
                st.success(f"Added '{new_post_name}'!")
                st.rerun()

st.markdown("### Configured Posts (Order of Ballot)")
st.write("Use the buttons below to edit names, reorder, or delete posts.")

# --- BUTTON TO FORCE LOAD DEFAULTS ON EXISTING DATABASES ---
with st.expander("🛠️ Advanced: Reset to Default Prescribed Posts"):
    st.warning("Clicking this will replace your current list with the standard 12 university posts.")
    if st.button("🔄 Reset to 12 Default Posts"):
        year_data["main_posts_config"] = [
            {"post_name": "The Chairperson", "seats": 1},
            {"post_name": "The Vice Chairperson", "seats": 1},
            {"post_name": "General Secretary", "seats": 1},
            {"post_name": "University Union Councillor (UUC)", "seats": 2}, 
            {"post_name": "The Arts Club Secretary", "seats": 1},
            {"post_name": "The Magazine Editor", "seats": 1},
            {"post_name": "Lady Representative", "seats": 2},
            {"post_name": "I Year Representative", "seats": 1},
            {"post_name": "II Year Representative", "seats": 1},
            {"post_name": "III Year Representative", "seats": 1},
            {"post_name": "I PG Representative", "seats": 1},
            {"post_name": "II PG Representative", "seats": 1}
        ]
        db_utils.save_data(db)
        st.success("Default posts loaded successfully!")
        st.rerun()

if not posts_config:
    st.info("No posts configured yet. Add one above or load the defaults.")
else:
    for idx, post in enumerate(posts_config):
        # Track edit mode state for this specific post
        edit_key = f"edit_mode_{idx}"
        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        c1, c2, c3, c4, c5, c6 = st.columns([3.5, 1.5, 0.8, 0.8, 0.8, 0.8])
        
        # --- EDIT TOGGLE LOGIC ---
        if st.session_state[edit_key]:
            new_name = c1.text_input("Edit Name", value=post['post_name'], key=f"edit_input_{idx}", label_visibility="collapsed")
            if c3.button("💾", key=f"save_{idx}", help="Save changes", type="primary"):
                old_name = post['post_name']
                if new_name.strip() and new_name.strip() != old_name:
                    post['post_name'] = new_name.strip()
                    # Safely migrate candidate data to the new post name so data isn't lost!
                    if "main_post_candidates" in year_data and old_name in year_data["main_post_candidates"]:
                        year_data["main_post_candidates"][post['post_name']] = year_data["main_post_candidates"].pop(old_name)
                    db_utils.save_data(db)
                st.session_state[edit_key] = False
                st.rerun()
        else:
            c1.markdown(f"**📌 {post['post_name']}**")
            if c3.button("✏️", key=f"edit_btn_{idx}", help="Edit Post Name"):
                st.session_state[edit_key] = True
                st.rerun()
                
        # --- SEATS & MOVEMENT LOGIC ---
        updated_seats = c2.number_input("Seats", min_value=1, value=post['seats'], key=f"seats_val_{idx}", label_visibility="collapsed")
        if updated_seats != post['seats']:
            posts_config[idx]['seats'] = updated_seats
            db_utils.save_data(db)
            
        if c4.button("⬆️", key=f"up_{idx}", disabled=(idx == 0), help="Move up"):
            posts_config.insert(idx - 1, posts_config.pop(idx))
            db_utils.save_data(db)
            st.rerun()
            
        if c5.button("⬇️", key=f"down_{idx}", disabled=(idx == len(posts_config) - 1), help="Move down"):
            posts_config.insert(idx + 1, posts_config.pop(idx))
            db_utils.save_data(db)
            st.rerun()
            
        if c6.button("🗑️", key=f"del_post_{idx}", help="Delete Post"):
            post_to_remove = post['post_name']
            posts_config.pop(idx)
            if "main_post_candidates" in year_data and post_to_remove in year_data["main_post_candidates"]:
                del year_data["main_post_candidates"][post_to_remove]
            db_utils.save_data(db)
            st.rerun()

# --- INJECT FOOTER ---
if hasattr(db_utils, 'add_footer'):
    db_utils.add_footer()
