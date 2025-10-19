# KGP_BOLT_TORQUING_TRACKER.py
import streamlit as st
import pandas as pd
import os
import base64
import io
import zipfile
from datetime import datetime
from pathlib import Path

# ---------- Config ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"  # File must be in same folder
BACKUP_DIR = "backup"
LEFT_LOGO = "left_logo.png"
RIGHT_LOGO = "right_logo.png"

DEFAULT_ADMIN_PASSWORD = "Admin@1234"
ADMIN_PASSWORD = os.environ.get("BOLT_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

# ---------- Helpers ----------
def load_logo_as_base64(path: str, width: int = 80) -> str:
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"<img src='data:image/png;base64,{b64}' width='{width}'/>"
    return ""

def read_data():
    if not os.path.exists(CSV_FILE):
        st.error(f"CSV file '{CSV_FILE}' not found. Please place it in this folder.")
        st.stop()
    df = pd.read_csv(CSV_FILE)
    df.columns = df.columns.str.strip().str.upper()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return df

def save_data(df: pd.DataFrame):
    """Save to main file and create timestamped backup."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_path = Path(BACKUP_DIR) / f"BOLT_TORQING_TRACKING_{timestamp}.csv"
    df.to_csv(CSV_FILE, index=False)
    df.to_csv(backup_path, index=False)
    return str(backup_path)

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

            # Generate password-protected ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.setpassword(bytes(ADMIN_PASSWORD, "utf-8"))
                zf.writestr(CSV_FILE, df.to_csv(index=False))
            zip_buffer.seek(0)

            st.download_button(
                "📥 Download Protected CSV (ZIP)",
                data=zip_buffer,
                file_name="BOLT_TORQING_TRACKING_PROTECTED.zip",
                mime="application/zip",
            )
        else:
            st.error("Incorrect password ❌")

# ---------- Initialize Session State ----------
if "new_records" not in st.session_state:
    st.session_state.new_records = pd.DataFrame()

# ---------- Main Form ----------
st.subheader("Bolt Torquing Entry Form")

with st.form("bolt_form", clear_on_submit=True):
    # LINE NUMBER
    line_options = sorted(df[col_line].dropna().unique().tolist()) if col_line else []
    selected_line = st.selectbox("LINE NUMBER", line_options, key="line")

    # TEST PACK (auto)
    testpack_value = ""
    if col_testpack and selected_line:
        df_line = df[df[col_line] == selected_line]
        testpacks = sorted(df_line[col_testpack].dropna().unique().tolist())
        if testpacks:
            testpack_value = testpacks[0]
            st.write(f"**TEST PACK NUMBER:** {testpack_value}")

    # BOLT TORQUING NUMBERS (multi-select)
    bolt_options = sorted(df_line[col_bolt].dropna().unique().tolist()) if col_bolt and selected_line else []
    selected_bolts = st.multiselect("BOLT TORQUING NUMBER(S)", bolt_options, key="bolts")

    # TYPE OF BOLTING
    type_options = sorted(df[col_type].dropna().unique().tolist()) if col_type else []
    type_selected = st.selectbox("TYPE OF BOLTING", [""] + type_options, key="type")

    # DATE
    date_selected = st.date_input("DATE", value=datetime.today().date(), key="date")

    # SUPERVISOR
    sup_options = sorted(df[col_supervisor].dropna().unique().tolist()) if col_supervisor else []
    supervisor_selected = st.selectbox("SUPERVISOR", [""] + sup_options, key="supervisor")

    # OTHER FIELDS
    torque_value = st.text_input("TORQUE VALUE", "", key="torque")
    status_value = st.selectbox("STATUS", ["", "OK", "NOT OK", "PENDING"], key="status")
    remarks_value = st.text_area("REMARKS", "", key="remarks")

    # Submit button
    submitted = st.form_submit_button("💾 Save Record")

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
        df2 = pd.concat([df, new_df], ignore_index=True)
        backup_path = save_data(df2)

        st.session_state.new_records = new_df
        st.success(f"✅ {len(selected_bolts)} record(s) saved successfully!")
        st.info(f"📦 Backup created: {backup_path}")

        st.rerun()

# ---------- Display Newly Added Records ----------
if not st.session_state.new_records.empty:
    st.markdown("### 🆕 Recently Added Records")
    st.dataframe(st.session_state.new_records, use_container_width=True)

st.markdown("---")
st.caption("© 2025 KGP BOLT TORQUING TRACKER — Admin Restricted")
