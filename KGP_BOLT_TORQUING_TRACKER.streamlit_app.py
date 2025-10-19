import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="KGP Bolt Torquing Tracker", layout="wide")

# ---------- Page Header ----------
st.markdown(
    "<h1 style='text-align:center; color:#1E3A8A;'>KGP BOLT TORQUING TRACKER</h1>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ---------- Load Data ----------
@st.cache_data
def load_data(file_path="BOLT TORQING TRACKING.csv"):
    df = pd.read_csv(file_path)

    # Normalize column names (case and spaces)
    df.columns = df.columns.str.strip().str.upper()

    # Normalize string data (remove leading/trailing spaces)
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading CSV: {e}")
    st.stop()

# ---------- Admin Login ----------
st.sidebar.markdown("### 🔒 Admin Login")
password_input = st.sidebar.text_input("Enter admin password", type="password")
is_admin = password_input == "admin123"

if is_admin:
    st.sidebar.success("✅ Admin Mode Active")
else:
    st.sidebar.info("Enter password to edit data")

# ---------- Quick Stats ----------
st.sidebar.markdown("### 📊 Quick Actions")
st.sidebar.write(f"Records: {len(df)}")
if "BOLT TORQUING NUMBER" in df.columns:
    st.sidebar.write(f"Unique Bolt Numbers: {df['BOLT TORQUING NUMBER'].nunique()}")

st.markdown("### Select Line and Bolt Torquing Number(s)")

# ---------- Line Number Selection ----------
if "LINE NUMBER" not in df.columns:
    st.error("Column 'LINE NUMBER' not found in CSV. Check your header names.")
    st.stop()

line_numbers = sorted(df["LINE NUMBER"].dropna().unique())

if not line_numbers:
    st.warning("No valid 'LINE NUMBER' entries found in your CSV.")
    st.stop()

line_number = st.selectbox("LINE NUMBER", line_numbers)

# ---------- Auto-select Test Number(s) ----------
filtered_df = df[df["LINE NUMBER"] == line_number]

if "TEST NUMBER" in filtered_df.columns:
    test_numbers = sorted(filtered_df["TEST NUMBER"].dropna().unique())
else:
    test_numbers = []

if test_numbers:
    selected_tests = st.multiselect("TEST NUMBER(s)", test_numbers)
else:
    st.warning("No TEST NUMBERs found for this LINE NUMBER.")
    selected_tests = []

# ---------- Bolt Torquing Number Selection ----------
if "BOLT TORQUING NUMBER" in filtered_df.columns:
    bolt_options = sorted(filtered_df["BOLT TORQUING NUMBER"].dropna().unique())
    selected_bolts = st.multiselect("BOLT TORQUING NUMBER(s)", bolt_options)
else:
    st.warning("No BOLT TORQUING NUMBER column found in CSV.")
    selected_bolts = []

# ---------- Type of Bolting Selection ----------
if "TYPE OF BOLTING" in df.columns:
    bolting_types = sorted(df["TYPE OF BOLTING"].dropna().unique())
    selected_type = st.selectbox("TYPE OF BOLTING", bolting_types)
else:
    selected_type = st.text_input("TYPE OF BOLTING (Manual Entry)")

# ---------- Date and Supervisor Selection ----------
today = datetime.today().strftime("%Y-%m-%d")
date_input = st.date_input("DATE", value=pd.to_datetime(today))

if "SUPERVISOR" in df.columns:
    supervisors = sorted(df["SUPERVISOR"].dropna().unique())
    selected_supervisor = st.selectbox("SUPERVISOR", supervisors)
else:
    selected_supervisor = st.text_input("SUPERVISOR (Manual Entry)")

# ---------- View/Edit Existing Record ----------
st.markdown("---")
st.subheader("View / Edit Existing Record")

if selected_bolts:
    record = df[df["BOLT TORQUING NUMBER"].isin(selected_bolts)]
    st.dataframe(record)

    if is_admin:
        st.success("Admin Mode: You can edit and save data.")

        # Editable fields for each selected record
        for i, row in record.iterrows():
            st.markdown(f"#### Edit Record: {row['BOLT TORQUING NUMBER']}")
            col1, col2, col3 = st.columns(3)

            new_torque = col1.text_input("TORQUE VALUE", row.get("TORQUE VALUE", ""), key=f"torque_{i}")
            new_status = col2.selectbox(
                "STATUS", ["OK", "NOT OK"], index=0 if row.get("STATUS") == "OK" else 1, key=f"status_{i}"
            )
            new_remark = col3.text_input("REMARK", row.get("REMARK", ""), key=f"remark_{i}")

            # Save button per record
            if st.button(f"💾 Save Changes to {row['BOLT TORQUING NUMBER']}", key=f"save_{i}"):
                df.at[i, "TORQUE VALUE"] = new_torque
                df.at[i, "STATUS"] = new_status
                df.at[i, "REMARK"] = new_remark
                df.to_csv("BOLT TORQING TRACKING.csv", index=False)
                st.success(f"Changes saved for {row['BOLT TORQUING NUMBER']}")

else:
    st.info("Select at least one BOLT TORQUING NUMBER to view/edit record.")

# ---------- Footer ----------
st.markdown("---")
st.caption("KGP BOLT TORQUING TRACKER — View & Edit (Admin Restricted).")
