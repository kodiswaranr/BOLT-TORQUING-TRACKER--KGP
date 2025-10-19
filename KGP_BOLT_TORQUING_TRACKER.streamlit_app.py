# KGP_BOLT_TORQUING_TRACKER.py
import streamlit as st
import pandas as pd
import os
import base64
import io
import zipfile
from datetime import datetime

# ---------- Config ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"  # File must be in same folder
LEFT_LOGO = "left_logo.png"
RIGHT_LOGO = "right_logo.png"
DOWNLOAD_PASSWORD = "KGP@2025"  # 🔐 Change this password if needed

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
    st.header("Quick Stats")
    st.write(f"Total Records: {len(df)}")
    if col_bolt:
        st.write(f"Unique Bolt Numbers: {df[col_bolt].nunique()}")

# ---------- Initialize Session State ----------
if "new_records" not in st.session_state:
    st.session_state.new_records = pd.DataFrame()

# ---------- Main Form ----------
st.subheader("Bolt Torquing Entry Form")

with st.form("bolt_form", clear_on_submit=True):
    # LINE NUMBER
    line_options = sorted(df[col_line].dropna().unique().tolist()) if col_line else []
    selected_line = st.selectbox("LINE NUMBER", line_options, key="line")

    # TEST PACK (auto-detect)
    testpack_value = ""
    if col_testpack and selected_line:
        df_line = df[df[col_line] == selected_line]
        testpacks = sorted(df_line[col_testpack].dropna().unique().tolist())
        if testpacks:
            testpack_value = testpacks[0]
            st.write(f"**TEST PACK NUMBER:** {testpack_value}")

    # BOLT TORQUING NUMBERS (multi-select)
    bolt_options = sorted(df[col_bolt].dropna().unique().tolist()) if col_bolt else []
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
        save_data(df2)

        st.session_state.new_records = new_df
        st.success(f"✅ {len(selected_bolts)} record(s) saved successfully!")
        st.rerun()

# ---------- Display Newly Added Records ----------
if not st.session_state.new_records.empty:
    st.markdown("### 🆕 Recently Added Records")
    st.dataframe(st.session_state.new_records, use_container_width=True)

    # Password-protected download option
    with st.expander("🔐 Export Recently Added Records (Password Protected)"):
        password = st.text_input("Enter Export Password", type="password")
        if password:
            if password == DOWNLOAD_PASSWORD:
                csv_buffer = io.BytesIO()
                # Create a ZIP file with password
                with zipfile.ZipFile(csv_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                    csv_data = st.session_state.new_records.to_csv(index=False).encode("utf-8")
                    zipf.writestr("recent_records.csv", csv_data)
                csv_buffer.seek(0)
                st.download_button(
                    label="📥 Download Encrypted CSV (ZIP)",
                    data=csv_buffer,
                    file_name="recent_records_protected.zip",
                    mime="application/zip"
                )
                st.info("✅ File ready — ZIP password: " + DOWNLOAD_PASSWORD)
            else:
                st.error("❌ Incorrect password")

st.markdown("---")
st.caption("© 2025 KGP BOLT TORQUING TRACKER")
