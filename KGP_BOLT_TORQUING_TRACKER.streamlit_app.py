# KGP_BOLT_TORQUING_TRACKER.py
import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

# ---------- Config ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"  # File must be in same folder
LEFT_LOGO = "left_logo.png"
RIGHT_LOGO = "right_logo.png"

DEFAULT_ADMIN_PASSWORD = "Admin@1234"
ADMIN_PASSWORD = os.environ.get("BOLT_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

# ---------- Helpers ----------
def load_logo_as_base64(path: str, width: int = 80) -> str:
    """Loads logo as base64 for inline HTML display."""
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"<img src='data:image/png;base64,{b64}' width='{width}'/>"
    return ""

def read_data():
    """Read and clean CSV."""
    if not os.path.exists(CSV_FILE):
        st.error(f"CSV file '{CSV_FILE}' not found. Please place it in this folder.")
        st.stop()
    df = pd.read_csv(CSV_FILE)
    df.columns = df.columns.str.strip().str.upper()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df

def save_data(df: pd.DataFrame):
    """Save back to CSV."""
    df.to_csv(CSV_FILE, index=False)

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

# ---------- Flexible Column Detection ----------
def find_col(possible_names):
    for name in possible_names:
        if name in df.columns:
            return name
    return None

col_line = find_col(["LINE NO", "LINE NUMBER", "LINE"])
col_testpack = find_col(["TEST PACK NUMBER", "TEST PACK NO", "PACK NO"])
col_bolt = find_col(["BOLT TORQUING NUMBER", "BOLT NUMBER", "BOLT NO"])
col_type = find_col(["TYPE OF BOLTING", "BOLTING TYPE"])
col_date = find_col(["DATE"])
col_supervisor = find_col(["SUPERVISOR"])
col_torque = find_col(["TORQUE VALUE", "TORQUE"])
col_status = find_col(["STATUS"])
col_remarks = find_col(["REMARKS"])

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Quick Stats & Admin")
    st.write(f"Total Records: {len(df)}")
    if col_bolt:
        st.write(f"Unique Bolt Numbers: {df[col_bolt].nunique()}")

    st.markdown("---")
    st.write("🔐 Admin Access")
    admin_pass = st.text_input("Enter admin password", type="password")
    if admin_pass:
        if admin_pass == ADMIN_PASSWORD:
            st.success("Access granted ✅")
            if os.path.exists(CSV_FILE):
                with open(CSV_FILE, "rb") as f:
                    st.download_button("📥 Download CSV", f, file_name=CSV_FILE)
        else:
            st.error("Incorrect password ❌")

# ---------- Main Interface ----------
st.subheader("Bolt Torquing Entry Form")

# LINE NUMBER Dropdown
if not col_line:
    st.error("Column 'LINE NUMBER' not found in CSV.")
    st.stop()
line_options = sorted(df[col_line].dropna().unique().tolist())
selected_line = st.selectbox("LINE NUMBER", line_options)

# TEST PACK NUMBER (auto from selected line)
testpack_value = ""
if col_testpack and selected_line:
    df_line = df[df[col_line] == selected_line]
    testpacks = sorted(df_line[col_testpack].dropna().unique().tolist())
    if testpacks:
        testpack_value = testpacks[0]
        st.write(f"**TEST PACK NUMBER:** {testpack_value}")

# ✅ BOLT TORQUING NUMBER(S) — all values from CSV (multi-select)
if col_bolt:
    bolt_options = sorted(df[col_bolt].dropna().unique().tolist())
    selected_bolts = st.multiselect("BOLT TORQUING NUMBER(S)", bolt_options)
else:
    selected_bolts = []
    st.warning("BOLT TORQUING NUMBER column not found in CSV.")

# TYPE OF BOLTING
if col_type:
    type_options = sorted(df[col_type].dropna().unique().tolist())
    type_selected = st.selectbox("TYPE OF BOLTING", [""] + type_options)
else:
    type_selected = ""

# DATE
date_selected = st.date_input("DATE", value=datetime.today().date())

# SUPERVISOR
if col_supervisor:
    sup_options = sorted(df[col_supervisor].dropna().unique().tolist())
    supervisor_selected = st.selectbox("SUPERVISOR", [""] + sup_options)
else:
    supervisor_selected = ""

# TORQUE, STATUS, REMARKS
torque_value = st.text_input("TORQUE VALUE", "")
status_value = st.selectbox("STATUS", ["", "OK", "NOT OK", "PENDING"])
remarks_value = st.text_area("REMARKS", "")

# ---------- Save New Record ----------
if st.button("💾 Save Record"):
    new_row = {
        col_line or "LINE NUMBER": selected_line,
        col_testpack or "TEST PACK NUMBER": testpack_value,
        col_bolt or "BOLT TORQUING NUMBER": ", ".join(selected_bolts),
        col_type or "TYPE OF BOLTING": type_selected,
        col_date or "DATE": date_selected.strftime("%Y-%m-%d"),
        col_supervisor or "SUPERVISOR": supervisor_selected,
        col_torque or "TORQUE VALUE": torque_value,
        col_status or "STATUS": status_value,
        col_remarks or "REMARKS": remarks_value
    }

    # Ensure all columns exist before saving
    for c in new_row.keys():
        if c not in df.columns:
            df[c] = ""

    new_df = pd.DataFrame([new_row])
    df2 = pd.concat([df, new_df], ignore_index=True)
    save_data(df2)
    st.success("✅ Record saved successfully!")

st.markdown("---")
st.caption("© 2025 KGP BOLT TORQUING TRACKER — Admin Restricted")
