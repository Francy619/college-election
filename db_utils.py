import json
import os
import streamlit as st

DATA_FILE = "election_data.json"

def load_data():
    """
    Loads the election data from the JSON file. 
    Safely returns the base multi-tenant structure if the file is missing or corrupted.
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
    Saves the entire dictionary back to the JSON file.
    """
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_footer():
    """Injects a fixed footer at the bottom of the Streamlit app across all pages."""
    footer_html = """
    <style>
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
            z-index: 9999;
        }
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .custom-footer {
                background-color: rgba(14, 17, 23, 0.95);
                color: #bbb;
                border-top: 1px solid #333;
            }
        }
        /* Add padding to the bottom of the main container so content isn't hidden behind the footer */
        .block-container {
            padding-bottom: 70px !important;
        }
    </style>
    <div class="custom-footer">
        Developed by: <strong>Francis Thomas</strong>, Assistant Professor, Department of Chemistry, St. Dominic's College, Kanjirapally
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
