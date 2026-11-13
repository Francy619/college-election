import json
import os

DATA_FILE = "election_data.json"

def load_data():
    """
    Loads the election data from the JSON file. 
    If the file doesn't exist, is empty, or gets corrupted, 
    it safely returns the base multi-tenant structure.
    """
    base_structure = {
        "users": {}, 
        "colleges": {}
    }
    
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return base_structure
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            
            # Ensure core dictionaries exist to prevent KeyError on fresh loads
            if "users" not in data:
                data["users"] = {}
            if "colleges" not in data:
                data["colleges"] = {}
                
            return data
            
    except json.JSONDecodeError:
        # Failsafe: If the JSON file breaks during a save, reset to safe defaults
        return base_structure

def save_data(data):
    """
    Saves the entire dictionary back to the JSON file with proper formatting.
    """
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

