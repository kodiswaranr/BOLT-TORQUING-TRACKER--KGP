# KGP_BOLT_TORQUING_TRACKER.py
import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
import io
import zipfile

# ---------- Config ----------
TODAY = datetime.today().strftime("%Y-%m-%d")
CSV_FILE = f"BOLT_TORQING_TRACKING_{TODAY}.csv"  # Daily file
LEFT_LOGO = "left_logo.png"
RIGHT_LOGO = "right_logo.png"
EXPORT_PASSWORD = "KGP@2025"  # Hidden fixed password for ZIP export

# ---------- Helpers ----------
def load_logo_as_base64(path: str, width: int = 80) -> str:
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"<img src='data:image/png;base64,{b64}' width='{width}'/>"
    return ""

def read_or_create_today_file():
    """Read today's CSV file or create a new one if missing."""
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df.columns = df.columns.str.strip().str.upper()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        return df
    else:
        columns = [
            "LINE NUMBER", "TEST PACK NUMBER", "BOLT TORQUING NUMBER",
            "TYPE OF BOLTING", "DATE", "SUPERVISOR",
            "TORQUE VALUE", "STATUS", "REMARKS"
        ]
        df = pd.DataFrame(columns=columns)
        df.to_csv(CSV_FILE, index=False)
        return df

def save_today(df: pd.DataFrame):
    """Save current day's file."""
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
df = read_or_create_today_file()

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

# ---------- Entry Form ----------
st.subheader("Bolt Torquing Entry Form")

with st.form("bolt_form", clear_on_submit=True):
    line_options = sorted(df[col_line].dropna().unique().tolist()) if col_line else []
    selected_line = st.selectbox("LINE NUMBER", line_options, key="line")

    testpack_value = ""
    if col_testpack and selected_line:
        df_line = df[df[col_line] == selected_line]
        testpacks = sorted(df_line[col_testpack].dropna().unique().tolist())
        if testpacks:
            testpack_value = testpacks[0]
            st.write(f"**TEST PACK NUMBER:** {testpack_value}")

    bolt_options = sorted(df[col_bolt].dropna().unique().tolist()) if col_bolt else []
    selected_bolts = st.multiselect("BOLT TORQUING NUMBER(S)", bolt_options, key="bolts")

    type_options = sorted(df[col_type].dropna().unique().tolist()) if col_type else []
    type_selected = st.selectbox("TYPE OF BOLTING", [""] + type_options, key="type")

    date_selected = st.date_input("DATE", value=datetime.today().date(), key="date")

    sup_options = sorted(df[col_supervisor].dropna().unique().tolist()) if col_supervisor else []
    supervisor_selected = st.selectbox("SUPERVISOR", [""] + sup_options, key="supervisor")

    torque_value = st.text_input("TORQUE VALUE", "", key="torque")
    status_value = st.selectbox("STATUS", ["", "OK", "NOT OK", "PENDING"], key="status")
    remarks_value = st.text_area("REMARKS", "", key="remarks")

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
        save_today(df2)
        st.session_state["recent_added"] = new_df
        st.success(f"✅ {len(selected_bolts)} record(s) saved successfully!")
        st.rerun()

# ---------- Recently Added ----------
if "recent_added" in st.session_state and not st.session_state["recent_added"].empty:
    st.markdown("### 🆕 Recently Added Records")
    st.dataframe(st.session_state["recent_added"], use_container_width=True)

# ---------- Show Today’s Data ----------
st.markdown(f"### 📋 All Records for {TODAY}")
st.dataframe(df, use_container_width=True, height=400)

# ---------- Secure Download (All Days) ----------
st.markdown("### 🔐 Secure Export of All Daily Records")

csv_files = [f for f in os.listdir(".") if f.startswith("BOLT_TORQING_TRACKING_") and f.endswith(".csv")]

if csv_files:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.setpassword(bytes(EXPORT_PASSWORD, "utf-8"))
        for file in csv_files:
            with open(file, "r", encoding="utf-8") as f:
                zf.writestr(file, f.read())
    zip_buffer.seek(0)

    st.download_button(
        "⬇️ Download All Records (Password Protected ZIP)",
        data=zip_buffer,
        file_name="KGP_BOLT_TORQUING_ALL_DAYS.zip",
        mime="application/zip",
    )
else:
    st.info("No records available for export yet.")

st.markdown("---")
st.caption("© 2025 KGP BOLT TORQUING TRACKER — Daily Records Auto-Saved, Secure Export Enabled")
