import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

# ---------- Config ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"
LEFT_LOGO = "left_logo.png"
RIGHT_LOGO = "right_logo.png"

DEFAULT_ADMIN_PASSWORD = "Admin@1234"
ADMIN_PASSWORD = os.environ.get("BOLT_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

# ---------- Helpers ----------
def load_logo_as_base64(path: str, width: int = 80) -> str:
    if os.path.exists(path):
        with open(path, "rb") as f:
            b = f.read()
        b64 = base64.b64encode(b).decode()
        return f"<img src='data:image/png;base64,{b64}' width='{width}'/>"
    return ""

def read_data():
    """Reads and cleans CSV data, fixing column names and trimming values."""
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
        except Exception:
            df = pd.read_csv(CSV_FILE, engine="python")
    else:
        df = pd.DataFrame(columns=[
            "LINE NUMBER", "TEST PACK NUMBER", "BOLT TORQUING NUMBER",
            "TYPE OF BOLTING", "DATE", "SUPERVISOR",
            "TORQUE VALUE", "STATUS", "REMARKS"
        ])

    # --- Normalize column names ---
    df.columns = df.columns.str.strip().str.upper()

    # --- Trim string values ---
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

    return df

def save_data(df: pd.DataFrame):
    df.to_csv(CSV_FILE, index=False)

def ensure_cols(df: pd.DataFrame):
    expected = [
        "LINE NUMBER", "TEST PACK NUMBER", "BOLT TORQUING NUMBER",
        "TYPE OF BOLTING", "DATE", "SUPERVISOR",
        "TORQUE VALUE", "STATUS", "REMARKS"
    ]
    for c in expected:
        if c not in df.columns:
            df[c] = ""
    return df

# ---------- Page setup ----------
st.set_page_config(page_title="KGP BOLT TORQUING TRACKER", layout="wide")

# ---------- Header ----------
left_logo_html = load_logo_as_base64(LEFT_LOGO, 80)
right_logo_html = load_logo_as_base64(RIGHT_LOGO, 80)

header_html_template = """
<style>
.header-container {{
  background-color: #f2f6fa;
  padding: 14px;
  border-radius: 8px;
  margin-bottom: 14px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}}
.header-logo {{ width: 80px; }}
.header-title {{ font-size: 36px; font-weight:700; margin:0; color:#111; }}
@media (max-width: 768px) {{
  .header-container {{ flex-direction: column; align-items:center; }}
  .header-logo {{ width: 48px; margin-bottom:6px; }}
  .header-title {{ font-size:22px; }}
}}
</style>
<div class="header-container">
  <div style="flex:1; text-align:left;">{left}</div>
  <div style="flex:2; text-align:center;">
    <h1 class="header-title">KGP BOLT TORQUING TRACKER</h1>
  </div>
  <div style="flex:1; text-align:right;">{right}</div>
</div>
"""
st.markdown(
    header_html_template.format(
        left=left_logo_html.replace("<img", "<img class='header-logo'"),
        right=right_logo_html.replace("<img", "<img class='header-logo'")
    ),
    unsafe_allow_html=True
)

# ---------- Load data ----------
df = read_data()
df = ensure_cols(df)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Quick Actions")
    st.write("Records:", len(df))
    st.write("Unique Bolt Numbers:", df["BOLT TORQUING NUMBER"].nunique())

    st.markdown("---")
    st.write("🔐 Admin Login")
    admin_pass = st.text_input("Enter admin password", type="password")
    is_admin = admin_pass == ADMIN_PASSWORD
    if is_admin:
        st.success("✅ Admin mode enabled.")
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, "rb") as f:
                data_bytes = f.read()
            st.download_button(
                label="📥 Download CSV",
                data=data_bytes,
                file_name=os.path.basename(CSV_FILE),
                mime="text/csv"
            )
    elif admin_pass:
        st.error("Incorrect password")

# ---------- Fixed Admin Banner ----------
if is_admin:
    st.markdown("""
    <style>
    .fixed-banner {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #ffe6e6;
        border-bottom: 3px solid #e53935;
        color: #b71c1c;
        font-weight: 600;
        text-align: center;
        padding: 10px;
        z-index: 9999;
        font-size: 16px;
    }
    body { padding-top: 50px; }
    </style>
    <div class="fixed-banner">
        ⚠️ ADMIN MODE ACTIVE — Editing privileges are enabled. Proceed carefully.
    </div>
    """, unsafe_allow_html=True)

# ---------- Main Selection ----------
st.subheader("Select Line and Bolt Torquing Number(s)")

# Step 1 — LINE NUMBER dropdown
line_options = sorted(df["LINE NUMBER"].dropna().unique().tolist())
selected_line = st.selectbox("LINE NUMBER", [""] + line_options)

if not selected_line:
    st.info("Please select a LINE NUMBER to view related data.")
else:
    # Filter by selected line
    line_data = df[df["LINE NUMBER"].astype(str) == str(selected_line)]

    # Step 2 — Auto-fill TEST PACK, TYPE OF BOLTING, SUPERVISOR
    auto_test_pack = line_data["TEST PACK NUMBER"].dropna().astype(str).iloc[-1] if not line_data.empty else ""
    auto_bolting_type = line_data["TYPE OF BOLTING"].dropna().astype(str).iloc[-1] if not line_data.empty else ""
    auto_supervisor = line_data["SUPERVISOR"].dropna().astype(str).iloc[-1] if not line_data.empty else ""

    if is_admin:
        test_pack_input = st.text_input("TEST PACK NUMBER", value=auto_test_pack)
        type_of_bolting_input = st.text_input("TYPE OF BOLTING", value=auto_bolting_type)
        supervisor_input = st.text_input("SUPERVISOR", value=auto_supervisor)
    else:
        st.text_input("TEST PACK NUMBER (auto)", value=auto_test_pack, disabled=True)
        st.text_input("TYPE OF BOLTING (auto)", value=auto_bolting_type, disabled=True)
        st.text_input("SUPERVISOR (auto)", value=auto_supervisor, disabled=True)
        test_pack_input, type_of_bolting_input, supervisor_input = auto_test_pack, auto_bolting_type, auto_supervisor

    # Step 3 — BOLT TORQUING NUMBER dropdown
