import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

# ---------- Config ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"   # file must be in same folder
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
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
        except Exception:
            df = pd.read_csv(CSV_FILE, engine="python")
    else:
        df = pd.DataFrame(columns=[
            "LINE NUMBER", "TEST PACK NUMBER", "BOLT TORQUING NUMBER",
            "TYPE OF BOLTING", "DATE", "SUPERVISOR", "TORQUE VALUE", "STATUS", "REMARKS"
        ])
    return df

def save_data(df: pd.DataFrame):
    df.to_csv(CSV_FILE, index=False)

def ensure_cols(df: pd.DataFrame):
    expected = [
        "LINE NUMBER", "TEST PACK NUMBER", "BOLT TORQUING NUMBER",
        "TYPE OF BOLTING", "DATE", "SUPERVISOR", "TORQUE VALUE", "STATUS", "REMARKS"
    ]
    for c in expected:
        if c not in df.columns:
            df[c] = ""
    return df

# ---------- Page setup ----------
st.set_page_config(page_title="KGP BOLT TORQUING TRACKER", layout="wide")

# ---------- Header (responsive) ----------
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

# ---------- Load & prepare data ----------
df = read_data()
df = ensure_cols(df)

# ---------- Sidebar: quick stats & admin ----------
with st.sidebar:
    st.header("Quick Actions")
    st.write("Records:", len(df))
    st.write("Unique Bolt Numbers:", df["BOLT TORQUING NUMBER"].nunique())

    st.markdown("---")
    st.write("🔐 Admin")
    admin_pass = st.text_input("Enter admin password to download CSV", type="password")
