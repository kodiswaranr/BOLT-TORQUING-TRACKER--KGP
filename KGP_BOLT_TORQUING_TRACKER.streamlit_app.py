# KGP_BOLT_TORQUING_TRACKER.py

import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

# ---------- CONFIG ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"
LEFT_LOGO = "left_logo.png"
RIGHT_LOGO = "right_logo.png"

# ---------- HELPERS ----------
def load_logo_as_base64(path: str, width: int = 80) -> str:
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"<img src='data:image/png;base64,{b64}' width='{width}'/>"
    return ""

def read_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=[
            "LINE NO", "TEST PACK NO", "BOLT TORQUING NUMBER",
            "TYPE OF BOLTING", "DATE", "SUPERVISOR", "STATUS", "REMARKS"
        ])
    df = pd.read_csv(CSV_FILE)
    df.columns = df.columns.str.strip().str.upper()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df

def save_data(df: pd.DataFrame):
    df.to_csv(CSV_FILE, index=False)

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="KGP BOLT TORQUING TRACKER", layout="wide")

# ---------- HEADER ----------
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

# ---------- LOAD DATA ----------
df = read_data()

# ---------- COLUMN DETECTION ----------
def find_col(possible_names):
    for name in possible_names:
        if name in df.columns:
            return name
    return None

col_line = find_col(["LINE NO", "LINE NUMBER", "LINE"])
col_testpack = find_col(["TEST PACK NO", "TEST PACK NUMBER", "PACK NO"])
col_bolt = find_col(["BOLT TORQUING NUMBER", "BOLT NUMBER", "BOLT NO"])
col_type = find_col(["TYPE OF BOLTING", "BOLTING TYPE"])
col_date = find_col(["DATE"])
col_supervisor = find_col(["SUPERVISOR"])
col_status = find_col(["STATUS"])
col_remarks = find_col(["REMARKS"])

# ---------- SESSION STATE ----------
if "new_records" not in st.session_state:
    st.session_state.new_records = pd.DataFrame()

# ---------- MAIN FORM ----------
st.subheader("Bolt Torquing Entry Form")

with st.form("bolt_form", clear_on_submit=True):

    # LINE NUMBER
    line_options = sorted(df[col_line].dropna().unique().tolist()) if col_line and not df.empty else []
    selected_line = st.selectbox("LINE NUMBER", [""] + line_options, key="line")

    # TEST PACK NO lookup based on selected line
    testpack_value = ""
    testpack_options = []
    if selected_line and col_testpack:
        df_line = df[df[col_line] == selected_line]
        testpack_options = sorted(df_line[col_testpack].dropna().unique().tolist())
    testpack_value = st.selectbox("TEST PACK NO", [""] + testpack_options, key="testpack")

    # Always show BOLT TORQUING NUMBER(S) as J1–J200
    bolt_options = [f"J{i}" for i in range(1, 201)]
    selected_bolts = st.multiselect("BOLT TORQUING NUMBER(S)", bolt_options, key="bolts")

    # TYPE OF BOLTING
    type_options = sorted(df[col_type].dropna().unique().tolist()) if col_type and not df.empty else []
    type_selected = st.selectbox("TYPE OF BOLTING", [""] + type_options, key="type")

    # DATE
    date_selected = st.date_input("DATE", value=datetime.today().date(), key="date")

    # SUPERVISOR
    sup_options = sorted(df[col_supervisor].dropna().unique().tolist()) if col_supervisor and not df.empty else []
    supervisor_selected = st.selectbox("SUPERVISOR", [""] + sup_options, key="supervisor")

    # STATUS
    status_value = st.selectbox("STATUS", ["", "OK", "NOT OK", "PENDING"], key="status")

    # REMARKS
    remarks_value = st.text_area("REMARKS", "", key="remarks")

    # Submit button
    submitted = st.form_submit_button("💾 Save Record")

# ---------- SAVE DATA ----------
if submitted:
    if not selected_line:
        st.warning("Please select a LINE NUMBER.")
    elif not selected_bolts:
        st.warning("Please select at least one BOLT TORQUING NUMBER.")
    else:
        new_rows = []
        for bolt in selected_bolts:
            new_rows.append({
                col_line or "LINE NO": selected_line,
                col_testpack or "TEST PACK NO": testpack_value,
                col_bolt or "BOLT TORQUING NUMBER": bolt,
                col_type or "TYPE OF BOLTING": type_selected,
                col_date or "DATE": date_selected.strftime("%Y-%m-%d"),
                col_supervisor or "SUPERVISOR": supervisor_selected,
                col_status or "STATUS": status_value,
                col_remarks or "REMARKS": remarks_value
            })

        new_df = pd.DataFrame(new_rows)
        df = pd.concat([df, new_df], ignore_index=True)
        save_data(df)

        st.session_state.new_records = new_df
        st.success(f"✅ {len(selected_bolts)} record(s) saved successfully!")

        st.rerun()

# ---------- DISPLAY RECORDS ----------
st.markdown("### 🆕 Recently Added Records")
if not st.session_state.new_records.empty:
    st.dataframe(st.session_state.new_records, use_container_width=True)
else:
    st.info("No new records added yet.")

# ---------- ALL RECORDS (COLLAPSIBLE) ----------
with st.expander("📋 All Records (Full History)", expanded=False):
    if not df.empty:
        df_display = df.iloc[::-1]  # Show latest first
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No records available yet.")

st.markdown("---")
st.caption("© 2025 KGP BOLT TORQUING TRACKER — All Rights Reserved")
