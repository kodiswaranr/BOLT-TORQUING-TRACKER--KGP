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
    if not os.path.exists(CSV_FILE):
        st.error(f"CSV file '{CSV_FILE}' not found in this folder.")
        st.stop()
    df = pd.read_csv(CSV_FILE, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip().str.upper()
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# ✅ Natural sorting helper (J1 → J2 → J10 → J100 → J200)
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
if "selected_line" not in st.session_state:
    st.session_state.selected_line = None
if "selected_testpack" not in st.session_state:
    st.session_state.selected_testpack = None
if "new_records" not in st.session_state:
    st.session_state.new_records = pd.DataFrame()

# ---------- UI ----------
st.subheader("Bolt Torquing Entry Form")

# LINE NUMBER Dropdown
line_options = sorted([v for v in df[col_line].unique() if v.strip()], key=natural_sort_key) if col_line else []
line_choice = st.selectbox("LINE NUMBER", ["Choose option"] + line_options, key="selected_line")

# Filter TEST PACK options based on selected line
testpack_options = []
if line_choice != "Choose option" and col_line and col_testpack:
    df_line = df[df[col_line] == line_choice]
    testpack_options = sorted([v for v in df_line[col_testpack].unique() if v.strip()], key=natural_sort_key)
selected_testpack = st.selectbox("TEST PACK NO", ["Choose option"] + testpack_options, key="selected_testpack")

# ---------- Form ----------
with st.form("entry_form", clear_on_submit=True):
    # ✅ BOLT TORQUING NUMBER(S): Always show J1–J200 in natural order
    bolt_options = [f"J{i}" for i in range(1, 201)]
    selected_bolts = st.multiselect(
        "BOLT TORQUING NUMBER(S)",
        sorted(bolt_options, key=natural_sort_key),
        key="form_bolts"
    )

    type_options = sorted([v for v in df[col_type].dropna().unique() if v.strip()], key=str) if col_type else []
    type_choice = st.selectbox("TYPE OF BOLTING", ["Choose option"] + type_options, key="form_type")

    date_choice = st.date_input("DATE", datetime.today().date(), key="form_date")

    supervisor_options = sorted([v for v in df[col_supervisor].dropna().unique() if v.strip()], key=str) if col_supervisor else []
    supervisor_choice = st.selectbox("SUPERVISOR", ["Choose option"] + supervisor_options, key="form_supervisor")

    status_choice = st.selectbox("STATUS", ["Choose option", "OK", "NOT OK", "PENDING"], key="form_status")
    remarks_choice = st.text_area("REMARKS", "", key="form_remarks")

    save = st.form_submit_button("💾 Save Record")

# ---------- Save Data ----------
if save:
    errors = []
    if not line_choice or line_choice == "Choose option":
        errors.append("Please select LINE NUMBER.")
    if not selected_testpack or selected_testpack == "Choose option":
        errors.append("Please select TEST PACK NO.")
    if not selected_bolts:
        errors.append("Please select at least one BOLT TORQUING NUMBER.")
    if not type_choice or type_choice == "Choose option":
        errors.append("Please select TYPE OF BOLTING.")
    if not supervisor_choice or supervisor_choice == "Choose option":
        errors.append("Please select SUPERVISOR.")
    if not status_choice or status_choice == "Choose option":
        errors.append("Please select STATUS.")

    if errors:
        for e in errors:
            st.warning(e)
    else:
        new_rows = []
        for bolt in selected_bolts:
            r = {
                col_line: line_choice,
                col_testpack: selected_testpack,
                "BOLT TORQUING NUMBER(S)": bolt,
                col_type: type_choice,
                col_date: date_choice.strftime("%Y-%m-%d"),
                col_supervisor: supervisor_choice,
                col_status: status_choice,
                col_remarks: remarks_choice
            }
            new_rows.append(r)

        new_df = pd.DataFrame(new_rows)
        df_final = pd.concat([df, new_df], ignore_index=True)
        save_data(df_final)
        st.session_state.new_records = new_df

        st.success(f"✅ {len(new_df)} record(s) saved successfully.")

        # ✅ Completely clear all fields after save
        for key in list(st.session_state.keys()):
            if key.startswith("form_") or key in ["selected_line", "selected_testpack"]:
                del st.session_state[key]

        st.rerun()

# ---------- Recently Added ----------
if not st.session_state.new_records.empty:
    st.markdown("### 🆕 Recently Added Records")
    st.dataframe(st.session_state.new_records, use_container_width=True)

# ---------- Full History ----------
with st.expander("📋 All Records (Full History)", expanded=False):
    # Hide download button
    st.markdown("<style>button[data-testid='stBaseButton-download']{display:none;}</style>", unsafe_allow_html=True)
    df_all = read_data()
    if col_date in df_all.columns:
        df_all[col_date] = pd.to_datetime(df_all[col_date], errors="coerce")
        df_all = df_all.sort_values(by=col_date, ascending=False)
    st.dataframe(df_all, use_container_width=True)

st.caption("© 2025 KGP BOLT TORQUING TRACKER")
