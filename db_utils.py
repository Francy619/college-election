# db_utils.py
import json
import os
import uuid

DATA_FILE = "election_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def init_year(year):
    data = load_data()
    if year not in data:
        data[year] = {
            "poll_date": "",
            "programs": {"UG": [], "PG": []},
            "class_reps": {},
            "main_posts_config": [],
            "main_post_candidates": {}
        }
        save_data(data)
    return data

def add_candidate(year, class_name, roll_no, name, gender):
    data = load_data()
    candidate_id = str(uuid.uuid4())[:8] # Generate a unique ID
    
    new_cand = {
        "id": candidate_id,
        "roll_no": roll_no,
        "name": name,
        "gender": gender,
        "status": "Nominated"
    }
    data[year]["class_reps"][class_name]["candidates"].append(new_cand)
    save_data(data)

def update_candidate_status(year, class_name, candidate_id, new_status):
    data = load_data()
    for cand in data[year]["class_reps"][class_name]["candidates"]:
        if cand["id"] == candidate_id:
            cand["status"] = new_status
            break
    save_data(data)
