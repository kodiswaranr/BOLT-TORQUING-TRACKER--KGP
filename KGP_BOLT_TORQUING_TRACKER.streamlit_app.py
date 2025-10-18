# KGP_BOLT_TORQUING_TRACKER.py
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
            # try with engine fallback
            df = pd.read_csv(CSV_FILE, engine="python")
    else:
        # create empty dataframe with common columns as fallback
        df = pd.DataFrame(columns=[
            "LINE NUMBER", "TEST PACK NUMBER", "BOLT TORQUING NUMBER",
            "DATE", "TORQUE VALUE", "STATUS", "REMARKS"
        ])
    return df

def save_data(df: pd.DataFrame):
    df.to_csv(CSV_FILE, index=False)

def ensure_cols(df: pd.DataFrame):
    expected = ["LINE NUMBER", "TEST PACK NUMBER", "BOLT TORQUING NUMBER", "DATE", "TORQUE VALUE", "STATUS", "REMARKS"]
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
/* Desktop */
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

/* Mobile */
@media (max-width: 768px) {{
  .header-container {{
    flex-direction: column;
    align-items:center;
  }}
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

st.write("")  # small spacer

# ---------- Load & prepare data ----------
df = read_data()
df = ensure_cols(df)

# Convert DATE column to datetime where possible (for display)
def parse_date_col(s):
    try:
        return pd.to_datetime(s).dt.date
    except Exception:
        return s

# ---------- Sidebar: quick stats & admin ----------
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
                st.warning("CSV file not found to download.")
        else:
            st.error("Incorrect password")

# ---------- Main: selection & display ----------
st.subheader("Select Bolt Torquing Number(s)")

bolt_options = df["BOLT TORQUING NUMBER"].dropna().astype(str).unique().tolist()
bolt_options.sort()
selected = st.multiselect("BOLT TORQUING NUMBER (multiple allowed)", bolt_options, default=None)

if not selected:
    st.info("Choose one or more Bolt Torquing Numbers from the dropdown to view or edit records.")
else:
    # Filter rows matching selected bolt numbers
    mask = df["BOLT TORQUING NUMBER"].astype(str).isin([str(x) for x in selected])
    selected_rows = df.loc[mask].copy()
    if selected_rows.empty:
        st.warning("No rows found for selected bolt number(s).")
    else:
        # Show basic columns including TEST PACK NUMBER and LINE NUMBER
        display_cols = ["BOLT TORQUING NUMBER", "TEST PACK NUMBER", "LINE NUMBER", "DATE", "TORQUE VALUE", "STATUS", "REMARKS"]
        to_display = selected_rows[display_cols].reset_index(drop=True)
        st.markdown("### Matching records")
        st.dataframe(to_display, use_container_width=True)

        # If user selected exactly one bolt number, show the single-edit form
        if len(selected) == 1:
            st.markdown("### Edit selected bolt record")
            row_idx = selected_rows.index[0]
            row = selected_rows.iloc[0].copy()

            c1, c2 = st.columns([1,1])
            with c1:
                st.text_input("BOLT TORQUING NUMBER", value=str(row.get("BOLT TORQUING NUMBER", "")), disabled=True)
                st.text_input("TEST PACK NUMBER", value=str(row.get("TEST PACK NUMBER", "")), disabled=True)
                st.text_input("LINE NUMBER", value=str(row.get("LINE NUMBER", "")), disabled=True)
            with c2:
                date_val = row.get("DATE", "")
                try:
                    # parse with pandas; if invalid, fallback to empty
                    date_parsed = pd.to_datetime(date_val).date() if pd.notna(date_val) and date_val != "" else None
                except Exception:
                    date_parsed = None
                date_input = st.date_input("Date", value=date_parsed)
                torque_value = st.text_input("Torque Value", value=str(row.get("TORQUE VALUE", "")))
                status = st.selectbox("Status", options=["", "OK", "NOT OK", "PENDING"], index=0 if not row.get("STATUS") else (["", "OK", "NOT OK", "PENDING"].index(row.get("STATUS")) if row.get("STATUS") in ["OK","NOT OK","PENDING"] else 0))
                remarks = st.text_area("Remarks", value=str(row.get("REMARKS", "")))
            st.markdown("")
            if st.button("Save changes for selected bolt"):
                # write into main df
                df.at[row_idx, "DATE"] = date_input.strftime("%Y-%m-%d") if date_input else ""
                df.at[row_idx, "TORQUE VALUE"] = torque_value
                df.at[row_idx, "STATUS"] = status
                df.at[row_idx, "REMARKS"] = remarks
                try:
                    save_data(df)
                    st.success("Saved changes to CSV.")
                except Exception as e:
                    st.error(f"Failed to save CSV: {e}")

        else:
            # Multiple selection: offer batch update
            st.markdown("### Batch update for selected bolt numbers")
            st.info("Set a value below to apply to all selected bolt rows.")
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                batch_status = st.selectbox("Set Status for all selected", options=["", "OK", "NOT OK", "PENDING"], index=0)
            with bcol2:
                batch_remarks = st.text_input("Set Remarks for all selected")
            if st.button("Apply batch update to selected rows"):
                # apply update to all matched rows
                df.loc[mask, "STATUS"] = batch_status if batch_status != "" else df.loc[mask, "STATUS"]
                if batch_remarks != "":
                    df.loc[mask, "REMARKS"] = batch_remarks
                try:
                    save_data(df)
                    st.success("Batch update applied and saved.")
                except Exception as e:
                    st.error(f"Failed to save CSV: {e}")

# ---------- Add new record form ----------
st.markdown("---")
st.subheader("Add New Bolt Torquing Record")

with st.form("add_record_form", clear_on_submit=True):
    new_line = st.text_input("LINE NUMBER", "")
    new_test_pack = st.text_input("TEST PACK NUMBER", "")
    new_bolt_no = st.text_input("BOLT TORQUING NUMBER", "")
    new_date = st.date_input("Date", value=datetime.today().date())
    new_torque = st.text_input("Torque Value", "")
    new_status = st.selectbox("Status", options=["", "OK", "NOT OK", "PENDING"])
    new_remarks = st.text_area("Remarks", "")
    submit_new = st.form_submit_button("Add record")
    if submit_new:
        if not new_bolt_no:
            st.error("BOLT TORQUING NUMBER is required.")
        else:
            new_row = {
                "LINE NUMBER": new_line,
                "TEST PACK NUMBER": new_test_pack,
                "BOLT TORQUING NUMBER": new_bolt_no,
                "DATE": new_date.strftime("%Y-%m-%d") if new_date else "",
                "TORQUE VALUE": new_torque,
                "STATUS": new_status,
                "REMARKS": new_remarks
            }
            df2 = read_data()
            df2 = ensure_cols(df2)
            df2 = pd.concat([df2, pd.DataFrame([new_row])], ignore_index=True, sort=False)
            try:
                save_data(df2)
                st.success("New record added and saved.")
            except Exception as e:
                st.error(f"Failed to save new record: {e}")

# ---------- Footer / help ----------
st.markdown("---")
st.caption("Tip: Add 'BOLT TORQING TRACKING.csv' (with headers) to the app folder. Set BOLT_ADMIN_PASSWORD env var to change admin password.")


