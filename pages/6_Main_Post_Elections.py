import streamlit as st
import pandas as pd
from fpdf import FPDF
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Main Post Elections", page_icon="🗳️", layout="wide")

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

# --- PDF GENERATION CLASS FOR MAIN POSTS ---
class MainPostPDF(FPDF):
    def candidate_list(self, title, post_name, candidates, year_str):
        self.add_page()
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "ST. DOMINIC'S COLLEGE, KANJIRAPALLY", ln=True, align="C")
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, f"College Union Election {year_str}", ln=True, align="C")
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(5)
        
        self.set_font("Arial", "BU", 11)
        self.cell(0, 10, f"Post: {post_name}", ln=True, align="L")
        
        # Table Header
        self.set_font("Arial", "B", 10)
        self.cell(20, 8, "SL No", border=1, align="C")
        self.cell(40, 8, "Electoral Roll No", border=1, align="C")
        self.cell(90, 8, "Name of Candidate", border=1, align="C")
        self.cell(40, 8, "Original Class", border=1, align="C")
        self.ln()
        
        # Table Data
        self.set_font("Arial", "", 10)
        for idx, cand in enumerate(candidates):
            self.cell(20, 8, str(idx+1), border=1, align="C")
            self.cell(40, 8, str(cand['roll_no']), border=1, align="C")
            self.cell(90, 8, str(cand['name']), border=1)
            self.cell(40, 8, str(cand.get('class_origin', 'N/A')), border=1, align="C")
            self.ln()

    def create_ballots(self, count, post_name, seats, candidates, year_str, poll_date_str):
        for idx in range(count):
            if idx % 2 == 0:
                self.add_page()
                y_offset = 0
            else:
                y_offset = 148.5 # Halfway down A4
                self.set_line_width(0.5)
                for x in range(0, 210, 4):
                    self.line(x, 148.5, x + 2, 148.5)
            
            self._draw_ballot(y_offset, post_name, seats, candidates, year_str, poll_date_str)

    def _draw_ballot(self, y_offset, post_name, seats, candidates, year_str, poll_date_str):
        self.set_font("Arial", "", 10)
        
        # --- COUNTER FOIL (LEFT) ---
        self.set_xy(10, 15 + y_offset)
        self.set_font("Arial", "B", 10)
        self.cell(60, 5, "SL. No. ________", ln=True)
        self.set_font("Arial", "", 9)
        self.cell(60, 5, f"Election to College Union {year_str}", ln=True)
        self.set_font("Arial", "B", 9)
        self.cell(60, 5, "Counter foil of Ballot Paper", ln=True)
        self.set_font("Arial", "", 9)
        
        self.multi_cell(60, 5, f"Name of the post: {post_name}")
        self.set_x(10)
        self.cell(60, 5, f"No. of Seats: {seats}", ln=True)
        self.ln(2)
        self.set_x(10)
        self.cell(60, 5, "Name of the elector (Councillor): ____________", ln=True)
        self.set_x(10)
        self.cell(60, 5, "Class: ____________", ln=True)
        self.set_x(10)
        self.cell(60, 5, "Electoral Roll No.: ____________", ln=True)
        self.set_x(10)
        self.cell(60, 5, f"Date of poll: {poll_date_str}", ln=True)
        
        # --- VERTICAL CUT LINE ---
        self.set_line_width(0.5)
        for y in range(int(10 + y_offset), int(140 + y_offset), 4):
            self.
