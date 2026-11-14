import json
import os
import streamlit as st
import threading

DATA_FILE = "election_data.json"

# Create a "Traffic Light" to prevent two users from writing at the same time
db_lock = threading.Lock() 

def load_data():
    """
    Loads the election data from the JSON file safely. 
    """
    base_structure = {
        "users": {}, 
        "colleges": {}
    }
    
    with db_lock:  # Turn on red light for writers while reading
        if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
            return base_structure
        
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                
                # Ensure core dictionaries exist (Auto-repairs legacy databases)
                if "users" not in data:
                    data["users"] = {}
                if "colleges" not in data:
                    data["colleges"] = {}
                    
                return data
                
        except json.JSONDecodeError:
            return base_structure

def save_data(data):
    """
    Saves data using an Atomic Write and Thread Lock to prevent corruption 
    if multiple users click save at the exact same time.
    """
    temp_file = DATA_FILE + ".tmp"
    
    with db_lock:  # Lock the file so no one else can touch it
        try:
            # 1. Write everything to a temporary file first
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=4)
                
            # 2. Instantly swap the temp file with the real file (Atomic Replacement)
            # This guarantees the file is never caught "half-written"
            os.replace(temp_file, DATA_FILE)
        except Exception as e:
            print(f"Error saving database: {e}")

def add_footer():
    """Injects a fixed footer and forcefully hides Streamlit's default menus and badges."""
    footer_html = """
    <style>
        /* Completely hide the top right hamburger menu & toolbar */
        [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
        
        /* Hide the default Streamlit 'Made with Streamlit' footer */
        footer {visibility: hidden !important; display: none !important;}
        
        /* Forcefully hide the Streamlit Community Cloud 'Viewer Badge' */
        .viewerBadge_container__1QSob {display: none !important;}
        .viewerBadge_link__1S137 {display: none !important;}
        #viewerBadge {display: none !important;}
        a[href^="https://streamlit.io/cloud"] {display: none !important;}
        
        /* Ensure our custom footer stays on top */
        .custom-footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: rgba(255, 255, 255, 0.95);
            color: #444;
            text-align: center;
            padding: 10px;
            font-size: 13px;
            border-top: 1px solid #e6e6e6;
            z-index: 999999;
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .custom-footer {
                background-color: rgba(14, 17, 23, 0.95);
                color: #bbb;
                border-top: 1px solid #333;
            }
        }
        
        /* Add padding to the bottom of the main container */
        .block-container {
            padding-bottom: 70px !important;
        }
    </style>
    <div class="custom-footer">
        Developed by: <strong>Francis Thomas</strong>, Assistant Professor, Department of Chemistry, St. Dominic's College, Kanjirapally
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
