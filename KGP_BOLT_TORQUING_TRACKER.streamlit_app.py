import io
import zipfile

# ---------- Sidebar ----------
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
                # Encrypt with password (works with zipfile library in Python 3.11+)
                zf.setpassword(bytes(ADMIN_PASSWORD, "utf-8"))
                zf.writestr("BOLT TORQING TRACKING.csv", df.to_csv(index=False))
            zip_buffer.seek(0)

            st.download_button(
                "📥 Download Protected CSV (ZIP)",
                data=zip_buffer,
                file_name="BOLT_TORQUING_TRACKING_PROTECTED.zip",
                mime="application/zip",
            )

        else:
            st.error("Incorrect password ❌")
