import streamlit as st
import pandas as pd
import os

# ---------- APP CONFIG ----------
st.set_page_config(page_title="KGP Bolt Torquing Tracker", layout="wide")
st.title("KGP BOLT TORQUING TRACKER")

# ---------- CONSTANTS ----------
CSV_FILE = "BOLT TORQING TRACKING.csv"  # Must be in same folder as this script

# ---------- LOAD DATA ----------
if not os.path.exists(CSV_FILE):
    st.error(f"CSV file '{CSV_FILE}' not found in the current folder: {os.getcwd()}")
    st.stop()

try:
    df = pd.read_csv(CSV_FILE)
    df.columns = df.columns.str.strip().str.upper()  # Normalize column names

    # Auto-detect relevant columns
    line_col = next((c for c in df.columns if "LINE" in c and "NO" in c), None)
    bolt_col = next((c for c in df.columns if "BOLT" in c and ("TORQUE" in c or "NO" in c)), None)
    test_pack_col = next((c for c in df.columns if "TEST" in c and "PACK" in c), None)
    bolt_type_col = next((c for c in df.columns if "TYPE" in c and "BOLT" in c), None)
    supervisor_col = next((c for c in df.columns if "SUPERVISOR" in c), None)

    # Validate that key columns exist
    if line_col is None or bolt_col is None:
        st.error("Required columns not found. Ensure your CSV has headers like 'LINE NO' and 'BOLT TORQUING NO'.")
        st.stop()

    # ---------- LINE SELECTION ----------
    st.subheader("Select Line and Bolt Torquing Number(s)")

    line_options = sorted(df[line_col].dropna().unique())
    selected_line = st.selectbox("LINE NUMBER", line_options)

    if selected_line:
        filtered_df = df[df[line_col] == selected_line]

        # ---------- TEST PACK ----------
        if test_pack_col:
            test_pack_value = filtered_df[test_pack_col].iloc[0]
            st.markdown(f"**TEST PACK NUMBER:** {test_pack_value}")

        # ---------- MULTISELECT FOR BOLT NUMBERS ----------
        bolt_options = filtered_df[bolt_col].dropna().unique().tolist()
        selected_bolts = st.multiselect(
            "BOLT TORQUING NUMBER(S)",
            options=bolt_options,
            help="Select one or multiple bolt torquing numbers"
        )

        # ---------- TYPE OF BOLTING ----------
        if bolt_type_col:
            bolt_type_value = filtered_df[bolt_type_col].iloc[0]
            st.markdown(f"**TYPE OF BOLTING:** {bolt_type_value}")

        # ---------- DATE AND SUPERVISOR ----------
        st.date_input("DATE")

        if supervisor_col:
            supervisor_options = sorted(df[supervisor_col].dropna().unique())
            st.selectbox("SUPERVISOR", [""] + supervisor_options)

        # ---------- SHOW SELECTED RECORDS ----------
        if selected_bolts:
            record = filtered_df[filtered_df[bolt_col].isin(selected_bolts)]
            st.success("Record(s) loaded successfully.")
            st.dataframe(record)

except Exception as e:
    st.error(f"Error reading CSV file: {e}")
