import streamlit as st

# Require login before page loads
if not st.session_state.get("uid"):
    st.warning("Please log in first (see **Login / Sign Up** page).")
    st.stop()
