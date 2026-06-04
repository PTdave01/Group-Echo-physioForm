import streamlit as st

st.set_page_config(page_title="PhysioForm", page_icon="🩺", layout="wide")

# Define pages available when NOT logged in
if "user" not in st.session_state or st.session_state.user is None:
    pages = [
        st.Page("pages/0_Login.py", title="Login / Sign Up", icon="🔐"),
        st.Page("pages/2_Clinician.py", title="Clinician Dashboard", icon="👨‍⚕️"),
    ]
# Define pages available when logged in (Login page is hidden)
else:
    pages = [
        st.Page("pages/1_Patient.py", title="Start Exercise", icon="🧑‍⚕️"),
        st.Page("pages/2_Clinician.py", title="Clinician Dashboard", icon="👨‍⚕️"),
    ]

# Create the navigation – this replaces the default sidebar page list
nav = st.navigation(pages, position="sidebar")

# ── Welcome message & home content ─────────────────────────────────
if st.session_state.get("user") is None:
    st.title("Welcome to PhysioForm")
    st.markdown("### AI-Powered Home Physiotherapy")
    st.info("Please log in or sign up to start your exercise session.")
else:
    st.title(f"🩺 PhysioForm – Welcome, {st.session_state.user['email']}")
    st.markdown("Select an option from the sidebar to begin.")

# ── Logout button at the very bottom of the sidebar (logged in only) ──
if st.session_state.get("user") is not None:
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.rep_count = 0
        st.session_state.recognized_exercise = None
        st.rerun()
