# KGP_BOLT_TORQUING_TRACKER.py
import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

# ---------- Config ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"
LEFT_LOGO = "left_logo.png"
RIGHT_LOGO = "right_logo.png"

# ---------- Helpers ----------
def ensure_csv_exists():
    if not os.path.exists(CSV_FILE):
        cols = [
            "LINE NO", "TEST PACK NO", "BOLT TORQUING NUMBER(S)",
            "TYPE OF BOLTING", "DATE", "SUPERVISOR", "STATUS", "REMARKS"
        ]
        pd.DataFrame(columns=cols).to_csv(CSV_FILE, index=False)

def read_data():
    ensure_csv_exists()
    df = pd.read_csv(CSV_FILE, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip().str.upper()
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    return df

def save_data(df):
    os.makedirs(os.path.dirname(os.path.abspath(CSV_FILE)), exist_ok=True)
    df.to_csv(CSV_FILE, index=False)

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

# ---------- Page Setup ----------
st.set_page_config(page_title="KGP BOLT TORQUING TRACKER", layout="wide")

st.markdown(
    """
    <div style="background-color:#f5f7fb;padding:10px;border-radius:8px;
         display:flex;justify-content:space-between;align-items:center;">
      <div></div>
      <h1 style="text-align:center;color:#0c2d6b;">KGP BOLT TORQUING TRACKER</h1>
      <div></div>
    </div>
    """, unsafe_allow_html=True
)

# ---------- Load Data ----------
df = read_data()

# ---------- Column detection ----------
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

# ---------- Session state for showing newly added (keeps after rerun) ----------
if "new_records" not in st.session_state:
    st.session_state.new_records = pd.DataFrame()

# ---------- UI ----------
st.subheader("Bolt Torquing Entry Form")

# Prepare line options (no blank)
if not col_line:
    st.error("CSV does not contain a LINE column (e.g. 'LINE NO' or 'LINE NUMBER'). Please add it.")
    st.stop()

line_options = sorted([v for v in df[col_line].unique() if str(v).strip()], key=natural_sort_key)
if not line_options:
    st.error("No LINE values found in CSV. Add values or ensure CSV has correct headers.")
    st.stop()

# Put all entry widgets inside the same form so clear_on_submit resets them
with st.form("entry_form", clear_on_submit=True):
    # LINE NUMBER (select from list)
    line_choice = st.selectbox("LINE NUMBER", options=line_options)

    # Compute TEST PACK NO options for selected line
    testpack_options = []
    if col_testpack:
        df_line = df[df[col_line] == line_choice]
        testpack_options = sorted([v for v in df_line[col_testpack].unique() if str(v).strip()], key=natural_sort_key)

    # If no testpack_options, present an empty selectbox or a text input fallback.
    if testpack_options:
        testpack_choice = st.selectbox("TEST PACK NO", options=testpack_options)
    else:
        testpack_choice = st.text_input("TEST PACK NO (no values found for this line)", value="")

    # BOLT TORQUING NUMBER(S): fixed J1..J200
    bolt_options = [f"J{i}" for i in range(1, 201)]
    selected_bolts = st.multiselect(
        "BOLT TORQUING NUMBER(S)",
        options=sorted(bolt_options, key=natural_sort_key)
    )

    # TYPE OF BOLTING: either select from CSV values or text input if none
    type_options = sorted([v for v in df[col_type].dropna().unique() if str(v).strip()], key=str) if col_type else []
    if type_options:
        type_choice = st.selectbox("TYPE OF BOLTING", options=type_options)
    else:
        type_choice = st.text_input("TYPE OF BOLTING", value="")

    # DATE
    date_choice = st.date_input("DATE", value=datetime.today().date())

    # SUPERVISOR: select or text input fallback
    sup_options = sorted([v for v in df[col_supervisor].dropna().unique() if str(v).strip()], key=str) if col_supervisor else []
    if sup_options:
        supervisor_choice = st.selectbox("SUPERVISOR", options=sup_options)
    else:
        supervisor_choice = st.text_input("SUPERVISOR", value="")

    # STATUS: no blank option
    status_choice = st.selectbox("STATUS", options=["OK", "NOT OK", "PENDING"])

    # REMARKS
    remarks_choice = st.text_area("REMARKS", value="")

    # Submit button
    submitted = st.form_submit_button("💾 Save Record")

# ---------- Save handling ----------
if submitted:
    errors = []
    if not line_choice:
        errors.append("Please select LINE NUMBER.")
    if not selected_bolts:
        errors.append("Please select at least one BOLT TORQUING NUMBER.")
    if col_testpack and (not testpack_choice or str(testpack_choice).strip() == ""):
        errors.append("Please select or enter TEST PACK NO.")

    if errors:
        for e in errors:
            st.warning(e)
    else:
        # prepare rows (one row per selected bolt)
        rows = []
        for bolt in selected_bolts:
            row = {}
            row[col_line] = line_choice
            # store testpack under header if exists, else under "TEST PACK NO"
            if col_testpack:
                row[col_testpack] = testpack_choice
            else:
                row["TEST PACK NO"] = testpack_choice
            row["BOLT TORQUING NUMBER(S)"] = bolt
            row[col_type or "TYPE OF BOLTING"] = type_choice
            row[col_date or "DATE"] = date_choice.strftime("%Y-%m-%d")
            row[col_supervisor or "SUPERVISOR"] = supervisor_choice
            row[col_status or "STATUS"] = status_choice
            row[col_remarks or "REMARKS"] = remarks_choice
            rows.append(row)

        new_df = pd.DataFrame(rows)

        # append to CSV
        df_all = pd.concat([df, new_df], ignore_index=True, sort=False).fillna("")
        save_data(df_all)

        # store recently added in session_state so it can be shown after rerun
        st.session_state.new_records = new_df

        st.success(f"✅ {len(new_df)} record(s) saved successfully.")

        # Rerun to refresh UI and clear the form (clear_on_submit=True handled clearing widgets)
        st.rerun()

# ---------- Recently added display ----------
if not st.session_state.new_records.empty:
    st.markdown("### 🆕 Recently Added Records")
    st.dataframe(st.session_state.new_records, use_container_width=True)

# ---------- Full history (collapsed) ----------
with st.expander("📋 All Records (Full History)", expanded=False):
    st.markdown("<style>button[data-testid='stBaseButton-download']{display:none;}</style>", unsafe_allow_html=True)
    df_all = read_data()
    if col_date and col_date in df_all.columns:
        df_all[col_date] = pd.to_datetime(df_all[col_date], errors="coerce")
        df_all = df_all.sort_values(by=col_date, ascending=False)
    else:
        df_all = df_all.iloc[::-1]
    st.dataframe(df_all, use_container_width=True)

st.caption("© 2025 KGP BOLT TORQUING TRACKER")
