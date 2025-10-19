import streamlit as st
import pandas as pd
import os

# ---------- APP TITLE ----------
st.set_page_config(page_title="KGP Bolt Torquing Tracker", layout="wide")
st.title("KGP BOLT TORQUING TRACKER")

# ---------- FILE UPLOAD ----------
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Read and clean up the CSV
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.upper()  # Normalize headers
        
        # Auto-detect columns
        line_col = next((c for c in df.columns if "LINE" in c and "NO" in c), None)
        bolt_col = next((c for c in df.columns if "BOLT" in c and ("TORQUE" in c or "NO" in c)), None)
        test_pack_col = next((c for c in df.columns if "TEST" in c and "PACK" in c), None)
        bolt_type_col = next((c for c in df.columns if "TYPE" in c and "BOLT" in c), None)

        # Validate column presence
        if line_col is None or bolt_col is None:
            st.error("Required columns not found. Ensure CSV includes 'LINE NO' and 'BOLT TORQUING NO' or similar headers.")
        else:
            # ---------- LINE SELECTION ----------
            st.subheader("Select Line and Bolt Torquing Number(s)")
            line_options = sorted(df[line_col].dropna().unique())
            selected_line = st.selectbox("LINE NUMBER", line_options)

            if selected_line:
                # Filter for selected line
                filtered_df = df[df[line_col] == selected_line]

                # ---------- SHOW TEST PACK ----------
                if test_pack_col:
                    test_pack_value = filtered_df[test_pack_col].iloc[0]
                    st.markdown(f"**TEST PACK NUMBER:** {test_pack_value}")

                # ---------- MULTISELECT FOR BOLT TORQUING NUMBERS ----------
                bolt_options = filtered_df[bolt_col].dropna().unique().tolist()
                selected_bolts = st.multiselect(
                    "BOLT TORQUING NUMBER(S)",
                    options=bolt_options,
                    help="Select one or multiple bolt torquing numbers"
                )

                # ---------- TYPE OF BOLTING ----------
                if bolt_type_col:
                    bolt_type = filtered_df[bolt_type_col].iloc[0]
                    st.markdown(f"**TYPE OF BOLTING:** {bolt_type}")

                # ---------- SHOW SELECTED RECORDS ----------
                if selected_bolts:
                    record = filtered_df[filtered_df[bolt_col].isin(selected_bolts)]
                    st.success("Record(s) loaded successfully.")
                    st.dataframe(record)

    except Exception as e:
        st.error(f"Error reading file: {e}")

else:
    st.info("Please upload a CSV file to begin.")
