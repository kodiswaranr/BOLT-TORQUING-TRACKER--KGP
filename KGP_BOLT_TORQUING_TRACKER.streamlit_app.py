# KGP_BOLT_TORQUING_TRACKER.py
import streamlit as st
import pandas as pd
import os
import base64
import re
from datetime import datetime

# ---------- Config ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"
LEFT_LOGO = "left_logo.png"
RIGHT_LOGO = "right_logo.png"

# ---------- Helpers ----------
def load_logo_as_base64(path, width=80):
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"<img src='data:image/png;base64,{b64}' width='{width}'/>"
    return ""

def read_data():
    # If file missing, create an empty dataframe with expected headers to avoid crashes
    if not os.path.exists(CSV_FILE):
        cols = [
            "LINE NO", "TEST PACK NO", "BOLT TORQUING NUMBER(S)",
            "TYPE OF BOLTING", "DATE", "SUPERVISOR", "STATUS", "REMARKS"
        ]
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(CSV_FILE, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip().str.upper()
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    return df

def save_data(df):
    # Ensure folder exists (if running in environments where working dir might differ)
    os.makedirs(os.path.dirname(os.path.abspath(CSV_FILE)), exist_ok=True)
    df.to_csv(CSV_FILE, index=False)

# Natural sorting helper (J1 -> J2 -> J10 -> J100 ...)
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

# ---------- Page Setup ----------
st.set_page_config(page_title="KGP BOLT TORQUING TRACKER", layout="wide")

# ---------- Header ----------
left_logo_html = load_logo_as_base64(LEFT_LOGO)
right_logo_html = load_logo_as_base64(RIGHT_LOGO)
st.markdown(
    f"""
    <div style="background-color:#f5f7fb;padding:10px;border-radius:8px;
         display:flex;justify-content:space-between;align-items:center;">
      <div>{left_logo_html}</div>
      <h1 style="text-align:center;color:#0c2d6b;">KGP BOLT TORQUING TRACKER</h1>
      <div>{right_logo_html}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Load Data ----------
df = read_data()

# ---------- Column Detection ----------
def find_col(possible):
    for name in possible:
        if name in df.columns:
            return name
    return None

col_line = find_col(["LINE NO", "LINE NUMBER", "LINE"])
col_testpack = find_col(["TEST PACK NO", "TEST PACK NUMBER", "PACK NO"])
col_type = find_col(["TYPE OF BOLTING", "BOLTING TYPE"])
col_date = find_col(["DATE"])
col_supervisor = find_col(["SUPERVISOR"])
col_status = find_col(["STATUS"])
col_remarks = find_col(["REMARKS"])

# ---------- Session State ----------
if "new_records" not in st.session_state:
    st.session_state.new_records = pd.DataFrame()

# ---------- UI ----------
st.subheader("Bolt Torquing Entry Form")

# Build LINE options (no blank)
line_options = []
if col_line:
    line_options = sorted([v for v in df[col_line].unique() if str(v).strip()], key=natural_sort_key)

# Ensure keys exist before using them
if "selected_line" not in st.session_state:
    st.session_state.selected_line = line_options[0] if line_options else ""

# LINE selectbox (no blank option)
if line_options:
    line_choice = st.selectbox("LINE NUMBER", line_options, index=line_options.index(st.session_state.selected_line) if st.session_state.selected_line in line_options else 0, key="selected_line")
else:
    st.error("No LINE values found in CSV.")
    st.stop()

# TEST PACK NO options filtered by LINE
testpack_options = []
if col_testpack and col_line and line_choice:
    df_line = df[df[col_line] == line_choice]
    testpack_options = sorted([v for v in df_line[col_testpack].unique() if str(v).strip()], key=natural_sort_key)

# Keep selected_testpack in session_state and default to first if available
if "selected_testpack" not in st.session_state:
    st.session_state.selected_testpack = testpack_options[0] if testpack_options else ""

if testpack_options:
    # ensure current selected_testpack is valid
    if st.session_state.selected_testpack not in testpack_options:
        st.session_state.selected_testpack = testpack_options[0]
    selected_testpack = st.selectbox("TEST PACK NO", testpack_options, index=testpack_options.index(st.session_state.selected_testpack), key="selected_testpack")
else:
    selected_testpack = ""
    st.warning("No TEST PACK NO options for selected LINE.")

# ---------- Form ----------
with st.form("entry_form", clear_on_submit=True):
    # BOLT TORQUING NUMBER(S): always J1–J200 in natural order
    bolt_options = [f"J{i}" for i in range(1, 201)]
    selected_bolts = st.multiselect(
        "BOLT TORQUING NUMBER(S)",
        sorted(bolt_options, key=natural_sort_key),
        key="form_bolts"
    )

    type_options = sorted([v for v in df[col_type].dropna().unique() if str(v).strip()], key=str) if col_type else []
    # if type_options is empty, still provide an empty selectbox would error; handle gracefully
    if type_options:
        type_choice = st.selectbox("TYPE OF BOLTING", type_options, index=0, key="form_type")
    else:
        type_choice = ""
        st.text_input("TYPE OF BOLTING (no values found in CSV)", value="", key="form_type_text")

    date_choice = st.date_input("DATE", datetime.today().date(), key="form_date")

    supervisor_options = sorted([v for v in df[col_supervisor].dropna().unique() if str(v).strip()], key=str) if col_supervisor else []
    if supervisor_options:
        supervisor_choice = st.selectbox("SUPERVISOR", supervisor_options, index=0, key="form_supervisor")
    else:
        supervisor_choice = ""
        st.text_input("SUPERVISOR (no values found in CSV)", value="", key="form_supervisor_text")

    status_choices = ["OK", "NOT OK", "PENDING"]
    status_choice = st.selectbox("STATUS", status_choices, index=0, key="form_status")

    remarks_choice = st.text_area("REMARKS", "", key="form_remarks")

    save = st.form_submit_button("💾 Save Record")

# ---------- Save Data ----------
if save:
    errors = []
    if not line_choice:
        errors.append("Please select LINE NUMBER.")
    if not selected_bolts:
        errors.append("
