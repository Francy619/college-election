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
    year_data["main_posts_config"] = [
        {"post_name": "The Chairperson", "seats": 1},
        {"post_name": "General Secretary", "seats": 1}
    ]
    db_utils.save_data(db)

posts_config = year_data["main_posts_config"]

st.markdown("### Add New Main Post")
with st.form("add_post_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        new_post_name = st.text_input("Name of the Post").title()
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

st.markdown("### Configured Posts")
if posts_config:
    for idx, post in enumerate(posts_config):
        c1, c2, c3 = st.columns([4, 2, 2])
        c1.text(f"📌 {post['post_name']}")
        updated_seats = c2.number_input("Seats", min_value=1, value=post['seats'], key=f"seats_val_{idx}", label_visibility="collapsed")
        if updated_seats != post['seats']:
            posts_config[idx]['seats'] = updated_seats
            db_utils.save_data(db)
            
        if c3.button("🗑️ Delete", key=f"del_post_{idx}"):
            post_to_remove = post['post_name']
            posts_config.pop(idx)
            if "main_post_candidates" in year_data and post_to_remove in year_data["main_post_candidates"]:
                del year_data["main_post_candidates"][post_to_remove]
            db_utils.save_data(db)
            st.rerun()
