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
    st.write("🔐 Admin")
    admin_pass = st.text_input("Enter admin password to download CSV", type="password")
    if admin_pass:
        if admin_pass == ADMIN_PASSWORD:
            st.success("Password OK — download below")
            if os.path.exists(CSV_FILE):
                with open(CSV_FILE, "rb") as f:
                    data_bytes = f.read()
                st.download_button(
                    label="📥 Download CSV",
                    data=data_bytes,
                    file_name=os.path.basename(CSV_FILE),
                    mime="text/csv"
                )
            else:
                st.warning("CSV file not found.")
        else:
            st.error("Incorrect password")

# ---------- Main selection ----------
st.subheader("Select Line and Bolt Torquing Number(s)")

# Step 1 — LINE NUMBER dropdown
line_options = df["LINE NUMBER"].dropna().astype(str).unique().tolist()
line_options.sort()
selected_line = st.selectbox("LINE NUMBER", [""] + line_options)

if not selected_line:
    st.info("Please select a LINE NUMBER to view related data.")
else:
    # Filter by selected line
    line_data = df[df["LINE NUMBER"].astype(str) == selected_line]

    # Step 2 — Auto-fill TEST PACK, TYPE OF BOLTING, SUPERVISOR
    auto_test_pack = line_data["TEST PACK NUMBER"].dropna().astype(str).iloc[-1] if not line_data.empty else ""
    auto_bolting_type = line_data["TYPE OF BOLTING"].dropna().astype(str).iloc[-1] if not line_data.empty else ""
    auto_supervisor = line_data["SUPERVISOR"].dropna().astype(str).iloc[-1] if not line_data.empty else ""

    st.text_input("TEST PACK NUMBER (auto)", value=auto_test_pack, disabled=True)
    st.text_input("TYPE OF BOLTING (auto)", value=auto_bolting_type, disabled=True)
    st.text_input("SUPERVISOR (auto)", value=auto_supervisor, disabled=True)

    # Step 3 — BOLT TORQUING NUMBER dropdown
    bolts_for_line = (
        line_data["BOLT TORQUING NUMBER"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    bolts_for_line.sort()
    selected_bolts = st.multiselect("BOLT TORQUING NUMBER (multiple allowed)", bolts_for_line)

    # Step 4 — Date input
    date_input = st.date_input("Date", value=datetime.today().date())

    # ---------- Display and Edit ----------
    if not selected_bolts:
        st.info("Choose one or more Bolt Torquing Numbers to view or edit records.")
    else:
        mask = (
            (df["LINE NUMBER"].astype(str) == selected_line)
            & (df["BOLT TORQUING NUMBER"].astype(str).isin(selected_bolts))
        )
        selected_rows = df.loc[mask].copy()
        if selected_rows.empty:
            st.warning("No rows found for selected bolt(s).")
        else:
            display_cols = [
                "LINE NUMBER", "TEST PACK NUMBER", "BOLT TORQUING NUMBER",
                "TYPE OF BOLTING", "DATE", "SUPERVISOR",
                "TORQUE VALUE", "STATUS", "REMARKS"
            ]
            st.markdown("### Matching Records")
            st.dataframe(selected_rows[display_cols].reset_index(drop=True), use_container_width=True)

            if len(selected_bolts) == 1:
                st.markdown("### Edit Selected Bolt Record")
                row_idx = selected_rows.index[0]
                row = selected_rows.iloc[0].copy()

                torque_value = st.text_input("Torque Value", value=str(row.get("TORQUE VALUE", "")))
                status = st.selectbox("Status", ["", "OK", "NOT OK", "PENDING"], index=0 if not row.get("STATUS") else (["", "OK", "NOT OK", "PENDING"].index(row.get("STATUS")) if row.get("STATUS") in ["OK","NOT OK","PENDING"] else 0))
                remarks = st.text_area("Remarks", value=str(row.get("REMARKS", "")))

                if st.button("Save Changes"):
                    df.at[row_idx, "DATE"] = date_input.strftime("%Y-%m-%d")
                    df.at[row_idx, "SUPERVISOR"] = auto_supervisor
                    df.at[row_idx, "TYPE OF BOLTING"] = auto_bolting_type
                    df.at[row_idx, "TEST PACK NUMBER"] = auto_test_pack
                    df.at[row_idx, "TORQUE VALUE"] = torque_value
                    df.at[row_idx, "STATUS"] = status
                    df.at[row_idx, "REMARKS"] = remarks
                    try:
                        save_data(df)
                        st.success("Changes saved successfully.")
                    except Exception as e:
                        st.error(f"Failed to save: {e}")
            else:
                st.info("Multiple selection: batch editing can be added later.")

# ---------- Footer ----------
st.markdown("---")
st.caption("KGP BOLT TORQUING TRACKER — View & Edit Existing Records Only.")
