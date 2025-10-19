# KGP_BOLT_TORQUING_TRACKER.py
import streamlit as st
import pandas as pd
import os
import base64
import re
from datetime import datetime

# ---------- Config ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"
LEFT_LOGO = "left_logo.png"
RIGHT_LOGO = "right_logo.png"

# ---------- Helpers ----------
def load_logo_as_base64(path, width=80):
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"<img src='data:image/png;base64,{b64}' width='{width}'/>"
    return ""

def ensure_csv_exists():
    """Create CSV with headers if missing so app doesn't crash on first run."""
    if not os.path.exists(CSV_FILE):
        cols = [
            "LINE NO", "TEST PACK NO", "BOLT TORQUING NUMBER(S)",
            "TYPE OF BOLTING", "DATE", "SUPERVISOR", "STATUS", "REMARKS"
        ]
        pd.DataFrame(columns=cols).to_csv(CSV_FILE, index=False)

def read_data():
    ensure_csv_exists()
    df = pd.read_csv(CSV_FILE, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip().str.upper()
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    return df

def save_data(df):
    os.makedirs(os.path.dirname(os.path.abspath(CSV_FILE)), exist_ok=True)
    df.to_csv(CSV_FILE, index=False)

def natural_sort_key(s):
    """Split text into numeric and non-numeric parts for natural sort (J1,J2,...J10)."""
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

# ---------- Column Detection ----------
def find_col(possible):
    for name in possible:
        if name in df.columns:
            return name
    return None

col_line = find_col(["LINE NO", "LINE NUMBER", "LINE"])
col_testpack = find_col(["TEST PACK NO", "TEST PACK NUMBER", "PACK NO"])
col_type = find_col(["TYPE OF BOLTING", "BOLTING TYPE"])
col_date = find_col(["DATE"])
col_supervisor = find_col(["SUPERVISOR"])
col_status = find_col(["STATUS"])
col_remarks = find_col(["REMARKS"])

# ---------- Session State Initialization ----------
if "new_records" not in st.session_state:
    st.session_state.new_records = pd.DataFrame()

# Provide safe defaults for form-managed keys if not present
for key in [
    "selected_line", "selected_testpack",
    "form_bolts", "form_type", "form_date",
    "form_supervisor", "form_status", "form_remarks"
]:
    if key not in st.session_state:
        # sensible defaults
        if key == "form_date":
            st.session_state[key] = datetime.today().date()
        elif key == "form_status":
            st.session_state[key] = "OK"
        elif key == "form_bolts":
            st.session_state[key] = []
        else:
            st.session_state[key] = ""

# ---------- UI ----------
st.subheader("Bolt Torquing Entry Form")

# LINE NUMBER Dropdown (no blank option)
if not col_line:
    st.error("CSV does not contain a LINE column (e.g. 'LINE NO' or 'LINE NUMBER').")
    st.stop()

line_options = sorted([v for v in df[col_line].unique() if str(v).strip()], key=natural_sort_key)
if not line_options:
    st.error("No LINE values found in CSV. Add some LINE / TEST PACK data first or create CSV with headers.")
    st.stop()

# Ensure selected_line default is valid
if not st.session_state.get("selected_line") or st.session_state.selected_line not in line_options:
    st.session_state.selected_line = line_options[0]

line_choice = st.selectbox(
    "LINE NUMBER",
    options=line_options,
    index=line_options.index(st.session_state.selected_line),
    key="selected_line",
)

# TEST PACK NO options filtered by selected line (no blank option)
testpack_options = []
if col_testpack:
    df_line = df[df[col_line] == line_choice]
    testpack_options = sorted([v for v in df_line[col_testpack].unique() if str(v).strip()], key=natural_sort_key)

# If there are testpacks, set default; otherwise keep empty string
if testpack_options:
    if not st.session_state.get("selected_testpack") or st.session_state.selected_testpack not in testpack_options:
        st.session_state.selected_testpack = testpack_options[0]
    selected_testpack = st.selectbox(
        "TEST PACK NO",
        options=testpack_options,
        index=testpack_options.index(st.session_state.selected_testpack),
        key="selected_testpack"
    )
else:
    selected_testpack = ""
    st.warning("No TEST PACK NO values found for this LINE in CSV.")

# ---------- Data Entry Form ----------
with st.form("entry_form", clear_on_submit=True):
    # BOLT TORQUING NUMBER(S) - fixed J1..J200
    bolt_options = [f"J{i}" for i in range(1, 201)]
    selected_bolts = st.multiselect(
        "BOLT TORQUING NUMBER(S)",
        options=sorted(bolt_options, key=natural_sort_key),
        default=st.session_state.get("form_bolts", []),
        key="form_bolts"
    )

    # TYPE OF BOLTING: if CSV contains values show selectbox else allow text input
    type_options = sorted([v for v in df[col_type].dropna().unique() if str(v).strip()], key=str) if col_type else []
    if type_options:
        type_choice = st.selectbox("TYPE OF BOLTING", options=type_options, index=0, key="form_type")
    else:
        type_choice = st.text_input("TYPE OF BOLTING", value="", key="form_type_text")

    # DATE
    date_choice = st.date_input("DATE", value=st.session_state.get("form_date", datetime.today().date()), key="form_date")

    # SUPERVISOR: select if options exist otherwise text input
    supervisor_options = sorted([v for v in df[col_supervisor].dropna().unique() if str(v).strip()], key=str) if col_supervisor else []
    if supervisor_options:
        supervisor_choice = st.selectbox("SUPERVISOR", options=supervisor_options, index=0, key="form_supervisor")
    else:
        supervisor_choice = st.text_input("SUPERVISOR", value="", key="form_supervisor_text")

    # STATUS and REMARKS
    status_choices = ["OK", "NOT OK", "PENDING"]
    status_choice = st.selectbox("STATUS", status_choices, index=0, key="form_status")
    remarks_choice = st.text_area("REMARKS", value="", key="form_remarks")

    save_clicked = st.form_submit_button("💾 Save Record")

# ---------- Save Handler ----------
if save_clicked:
    # Collect actual values (handle cases where we used text_input fallbacks)
    type_val = st.session_state.get("form_type")
    if not type_val:
        # fallback to text input key if available
        type_val = st.session_state.get("form_type_text", "")

    supervisor_val = st.session_state.get("form_supervisor")
    if not supervisor_val:
        supervisor_val = st.session_state.get("form_supervisor_text", "")

    errors = []
    if not line_choice:
        errors.append("Please select LINE NUMBER.")
    if not selected_bolts:
        errors.append("Please select at least one BOLT TORQUING NUMBER.")
    if col_testpack and not selected_testpack:
        errors.append("Please select TEST PACK NO.")

    if errors:
        for e in errors:
            st.warning(e)
    else:
        # Build rows — one row per bolt
        new_rows = []
        for bolt in selected_bolts:
            row = {}
            row[col_line] = line_choice
            if col_testpack:
                row[col_testpack] = selected_testpack
            # store bolt under a consistent header
            row["BOLT TORQUING NUMBER(S)"] = bolt
            # type / supervisor fallback keys
            row[col_type or "TYPE OF BOLTING"] = type_val
            row[col_date or "DATE"] = date_choice.strftime("%Y-%m-%d")
            row[col_supervisor or "SUPERVISOR"] = supervisor_val
            row[col_status or "STATUS"] = status_choice
            row[col_remarks or "REMARKS"] = remarks_choice
            new_rows.append(row)

        new_df = pd.DataFrame(new_rows)

        # Append to master df and save
        # ensure df has consistent columns union
        df_all = pd.concat([df, new_df], ignore_index=True, sort=False).fillna("")
        save_data(df_all)

        # show success and remember recently added
        st.session_state.new_records = new_df
        st.success(f"✅ {len(new_df)} record(s) saved successfully.")

        # Reset form state to defaults safely:
        # - selected_line: keep current or reset to first option
        st.session_state.selected_line = line_options[0] if line_options else ""
        # - update testpack options for the (possibly same) selected_line
        if testpack_options:
            st.session_state.selected_testpack = testpack_options[0]
        else:
            st.session_state.selected_testpack = ""
        # - reset form widget values (these keys exist as widget keys)
        st.session_state.form_bolts = []
        st.session_state.form_type = ""
        st.session_state.form_type_text = ""
        st.session_state.form_date = datetime.today().date()
        st.session_state.form_supervisor = ""
        st.session_state.form_supervisor_text = ""
        st.session_state.form_status = "OK"
        st.session_state.form_remarks = ""

        # Refresh UI so cleared values are reflected
        st.rerun()

# ---------- Recently Added ----------
if not st.session_state.new_records.empty:
    st.markdown("### 🆕 Recently Added Records")
    st.dataframe(st.session_state.new_records, use_container_width=True)
else:
    st.info("No recently added records in this session.")

# ---------- Full History ----------
with st.expander("📋 All Records (Full History)", expanded=False):
    # hide dataframe download in toolbar if Streamlit shows it
    st.markdown("<style>button[data-testid='stBaseButton-download']{display:none;}</style>", unsafe_allow_html=True)
    df_all = read_data()
    if col_date and col_date in df_all.columns:
        df_all[col_date] = pd.to_datetime(df_all[col_date], errors="coerce")
        df_all = df_all.sort_values(by=col_date, ascending=False)
    else:
        df_all = df_all.iloc[::-1]
    st.dataframe(df_all, use_container_width=True)

st.caption("© 2025 KGP BOLT TORQUING TRACKING")
