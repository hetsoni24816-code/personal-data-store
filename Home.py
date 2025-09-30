import streamlit as st

st.set_page_config(page_title="Personal Data Store", page_icon="🔒", layout="wide")

# ------- Custom Sidebar Styles --------------------------------------
st.markdown(
    """
    <style>
        /* Sidebar background */
        [data-testid="stSidebar"] {
            background-color: #0D2847; /* dark blue */
            color: white;
        }
        /* Sidebar text */
        [data-testid="stSidebar"] * {
            color: white !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ------- Page Content -----------------------------------------------
st.title("🔒 Personal Data Store Platform")

st.write("Welcome! Use the sidebar to navigate:")
st.markdown("""
- **Upload Data:** Add new datasets securely.
- **Manage Permissions:** Control who can access your data.
- **Consent Log:** View history of access and updates.
- **Org Requests:** Approve or deny requests from organisations.
""")
