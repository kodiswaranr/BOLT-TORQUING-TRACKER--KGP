# KGP_BOLT_TORQUING_TRACKER.py
import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
import io
import zipfile

# ---------- Config ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"  # CSV must be in same folder
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
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip().str.upper()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    else:
        df = pd.DataFrame()
    return df

def save_data(df: pd.DataFrame):
    df.to_csv(CSV_FILE, index=False)

# ---------- Page setup ----------
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

if df.empty:
    st.error("CSV file not found or empty. Please ensure 'BOLT TORQING TRACKING.csv' exists in the same folder.")
    st.stop()

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

# ---------- Sidebar (Admin Access + Export) ----------
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

            # Create password-protected ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.setpassword(bytes(ADMIN_PASSWORD, "utf-8"))
                zf.writestr("BOLT TORQING TRACKING.csv", df.to_csv(index=False))
            zip_buffer.seek(0)

            st.download_button(
                "📥 Download Protected CSV (ZIP)",
                data=zip_buffer,
                file_name="BOLT_TORQING_TRACKING_PROTECTED.zip",
                mime="application/zip",
            )
        else:
            st.error("Incorrect password ❌")

# ---------- Main Form ----------
st.subheader("Select Line and Bolt Torquing Number(s)")

if not col_line:
    st.error("Column 'LINE NUMBER' not found in CSV. Check your header names.")
    st.stop()

line_options = sorted(df[col_line].dropna().unique().tolist())
selected_line = st.selectbox("LINE NUMBER", line_options)

if selected_line:
    df_line = df[df[col_line] == selected_line]

    # TEST PACK NUMBER
    if col_testpack:
        testpacks = sorted(df_line[col_testpack].dropna().unique().tolist())
        if testpacks:
            st.write(f"**TEST PACK NUMBER:** {', '.join(map(str, testpacks))}")
        else:
            testpacks = [""]

    # MULTI-SELECT FOR BOLT NUMBERS
    if col_bolt:
        bolt_options = sorted(df_line[col_bolt].dropna().unique().tolist())
        selected_bolts = st.multiselect("BOLT TORQUING NUMBER(S)", bolt_options)
    else:
        selected_bolts = []

    # TYPE OF BOLTING
    if col_type:
        type_options = sorted(df[col_type].dropna().unique().tolist())
        type_selected = st.selectbox("TYPE OF BOLTING", [""] + type_options)
    else:
        type_selected = ""

    # DATE INPUT
    date_selected = st.date_input("DATE", value=datetime.today().date())

    # SUPERVISOR
    if col_supervisor:
        sup_options = sorted(df[col_supervisor].dropna().unique().tolist())
        supervisor_selected = st.selectbox("SUPERVISOR", [""] + sup_options)
    else:
        supervisor_selected = ""

    # OTHER FIELDS
    torque_value = st.text_input("TORQUE VALUE", "")
    status_value = st.selectbox("STATUS", ["", "OK", "NOT OK", "PENDING"])
    remarks_value = st.text_area("REMARKS", "")

    # SAVE BUTTON
    if st.button("💾 Save Record"):
        if not selected_bolts:
            st.warning("Please select at least one BOLT TORQUING NUMBER.")
        else:
            new_rows = []
            for bolt in selected_bolts:
                new_row = {
                    col_line: selected_line,
                    col_testpack: testpacks[0] if col_testpack and testpacks else "",
                    col_bolt: bolt,
                    col_type: type_selected,
                    col_date: date_selected.strftime("%Y-%m-%d"),
                    col_supervisor: supervisor_selected,
                    col_torque: torque_value,
                    col_status: status_value,
                    col_remarks: remarks_value
                }
                new_rows.append(new_row)

            new_df = pd.DataFrame(new_rows)
            df_updated = pd.concat([df, new_df], ignore_index=True)
            save_data(df_updated)
            st.success(f"{len(selected_bolts)} record(s) saved successfully!")

            # Clear form (simulated)
            st.experimental_rerun()

st.markdown("---")
st.caption("© KGP BOLT TORQUING TRACKER — Admin Restricted.")
