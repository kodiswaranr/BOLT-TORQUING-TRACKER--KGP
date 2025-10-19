# KGP_BOLT_TORQUING_TRACKER.py
import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
from io import BytesIO
import zipfile
import re

# ---------- Config ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"  # Main CSV file
LEFT_LOGO = "left_logo.png"
RIGHT_LOGO = "right_logo.png"
EXPORT_PASSWORD = "KGP2025"  # Hidden password for export

# ---------- Helper Functions ----------
def load_logo_as_base64(path: str, width: int = 80) -> str:
    """Convert logo image to base64 for embedding."""
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"<img src='data:image/png;base64,{b64}' width='{width}'/>"
    return ""

def read_data():
    """Read or create the main CSV file."""
    if not os.path.exists(CSV_FILE):
        cols = [
            "LINE NUMBER", "TEST PACK NUMBER", "BOLT TORQUING NUMBER",
            "TYPE OF BOLTING", "DATE", "SUPERVISOR", "TORQUE VALUE",
            "STATUS", "REMARKS"
        ]
        pd.DataFrame(columns=cols).to_csv(CSV_FILE, index=False)
    df = pd.read_csv(CSV_FILE)
    df.columns = df.columns.str.strip().str.upper()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df

def save_data(df: pd.DataFrame):
    """Save all data and also create daily backup."""
    df.to_csv(CSV_FILE, index=False)
    today = datetime.today().strftime("%Y-%m-%d")
    daily_file = f"BOLT TORQING TRACKING_{today}.csv"
    df.to_csv(daily_file, index=False)

def create_password_protected_zip(df, filename, password):
    """Generate a ZIP file with password protection."""
    buffer = BytesIO()
    temp_csv = f"{filename}.csv"
    df.to_csv(temp_csv, index=False)
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.setpassword(password.encode())
        zf.write(temp_csv, arcname=os.path.basename(temp_csv))
    os.remove(temp_csv)
    buffer.seek(0)
    return buffer

def natural_sort_key(s):
    """Sort strings naturally (J1 < J2 < J10)."""
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

# ---------- Detect Columns ----------
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

# ---------- Initialize State ----------
if "new_records" not in st.session_state:
    st.session_state.new_records = pd.DataFrame()

# ---------- Main Form ----------
st.subheader("Bolt Torquing Entry Form")

with st.form("bolt_form", clear_on_submit=True):
    # LINE NUMBER
    line_options = sorted(df[col_line].dropna().unique().tolist()) if col_line else []
    selected_line = st.selectbox("LINE NUMBER", line_options)

    # TEST PACK (auto-fill)
    testpack_value = ""
    if col_testpack and selected_line:
        df_line = df[df[col_line] == selected_line]
        testpacks = sorted(df_line[col_testpack].dropna().unique().tolist())
        if testpacks:
            testpack_value = testpacks[0]
            st.write(f"**TEST PACK NUMBER:** {testpack_value}")

    # BOLT TORQUING NUMBER(S) — natural ascending sort
    if col_bolt:
        bolt_options = df[col_bolt].dropna().unique().tolist()
        bolt_options = sorted(bolt_options, key=natural_sort_key)
    else:
        bolt_options = []

    selected_bolts = st.multiselect("BOLT TORQUING NUMBER(S)", bolt_options)

    # TYPE OF BOLTING
    type_options = sorted(df[col_type].dropna().unique().tolist()) if col_type else []
    type_selected = st.selectbox("TYPE OF BOLTING", [""] + type_options)

    # DATE
    date_selected = st.date_input("DATE", value=datetime.today().date())

    # SUPERVISOR
    sup_options = sorted(df[col_supervisor].dropna().unique().tolist()) if col_supervisor else []
    supervisor_selected = st.selectbox("SUPERVISOR", [""] + sup_options)

    # OTHER FIELDS
    torque_value = st.text_input("TORQUE VALUE", "")
    status_value = st.selectbox("STATUS", ["", "OK", "NOT OK", "PENDING"])
    remarks_value = st.text_area("REMARKS", "")

    submitted = st.form_submit_button("💾 Save Record")

# ---------- Handle Submission ----------
if submitted:
    if not selected_line:
        st.warning("Please select a LINE NUMBER.")
    elif not selected_bolts:
        st.warning("Please select at least one BOLT TORQUING NUMBER.")
    else:
        new_rows = []
        for bolt in selected_bolts:
            new_rows.append({
                col_line or "LINE NUMBER": selected_line,
                col_testpack or "TEST PACK NUMBER": testpack_value,
                col_bolt or "BOLT TORQUING NUMBER": bolt,
                col_type or "TYPE OF BOLTING": type_selected,
                col_date or "DATE": date_selected.strftime("%Y-%m-%d"),
                col_supervisor or "SUPERVISOR": supervisor_selected,
                col_torque or "TORQUE VALUE": torque_value,
                col_status or "STATUS": status_value,
                col_remarks or "REMARKS": remarks_value
            })

        new_df = pd.DataFrame(new_rows)
        df_all = pd.concat([df, new_df], ignore_index=True)
        save_data(df_all)
        st.session_state.new_records = new_df
        st.success(f"✅ {len(selected_bolts)} record(s) saved successfully!")
        st.rerun()

# ---------- Show All Records (Full History, Newest on Top) ----------
with st.expander("📋 All Records (Full History)", expanded=False):
    df_all = read_data()
    if col_date in df_all.columns:
        df_all[col_date] = pd.to_datetime(df_all[col_date], errors="coerce")
        df_all = df_all.sort_values(by=col_date, ascending=False)
    else:
        df_all = df_all.iloc[::-1]
    st.dataframe(df_all, use_container_width=True)

# ---------- Secure Export ----------
with st.expander("🔒 Secure Data Export"):
    entered_password = st.text_input("Enter export password", type="password")
    if entered_password == EXPORT_PASSWORD:
        df_export = read_data()
        if col_date in df_export.columns:
            df_export[col_date] = pd.to_datetime(df_export[col_date], errors="coerce")
            df_export = df_export.sort_values(by=col_date, ascending=False)
        else:
            df_export = df_export.iloc[::-1]
        zip_buffer = create_password_protected_zip(df_export, "KGP_BOLT_TRACKING_EXPORT", EXPORT_PASSWORD)
        st.download_button(
            label="📦 Download Encrypted Data (ZIP)",
            data=zip_buffer,
            file_name="KGP_BOLT_TRACKING_EXPORT.zip",
            mime="application/zip"
        )
    elif entered_password:
        st.error("Incorrect password.")

st.markdown("---")
st.caption("© 2025 KGP BOLT TORQUING TRACKER — Admin Restricted")
