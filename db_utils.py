import json
import os

DATA_FILE = "election_data.json"

def load_data():
    # If file doesn't exist or is empty, return the multi-tenant base structure
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return {"users": {}}
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Ensure the "users" dictionary exists to prevent key errors
            if "users" not in data:
                data["users"] = {}
            return data
    except json.JSONDecodeError:
        # If the JSON file gets corrupted, safely reset to the base structure
        return {"users": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
