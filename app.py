import streamlit as st

st.set_page_config(page_title="PhysioForm", page_icon="🩺", layout="wide")

# ── Build the list of pages based on login state ──
if "user" not in st.session_state or st.session_state.user is None:
    pages = [
        st.Page("pages/0_Login.py", title="Login / Sign Up", icon="🔐"),
        st.Page("pages/2_Clinician.py", title="Clinician Dashboard", icon="👨‍⚕️"),
    ]
else:
    pages = [
        st.Page("pages/1_Patient.py", title="Start Exercise", icon="🧑‍⚕️"),
        st.Page("pages/2_Clinician.py", title="Clinician Dashboard", icon="👨‍⚕️"),
    ]

# Create the navigation (sidebar)
nav = st.navigation(pages, position="sidebar")

# ── Home page content ──
if st.session_state.get("user") is None:
    st.title("Welcome to PhysioForm")
    st.markdown("### AI-Powered Home Physiotherapy")
    st.info("Please log in or sign up to start your exercise session.")
    # Direct login button (visible even if sidebar is collapsed on mobile)
    if st.button("🔐 Go to Login / Sign Up"):
        st.switch_page("pages/0_Login.py")
else:
    st.title(f"🩺 PhysioForm – Welcome, {st.session_state.user['email']}")
    st.markdown("Select an option from the sidebar or below to begin.")
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/1_Patient.py", label="🧑‍⚕️ Start Exercise", icon="🧑‍⚕️")
    with col2:
        st.page_link("pages/2_Clinician.py", label="👨‍⚕️ Clinician Dashboard", icon="👨‍⚕️")

# ── Sidebar logout button (only when logged in) – placed below the page links ──
if st.session_state.get("user") is not None:
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.rep_count = 0
        st.session_state.recognized_exercise = None
        st.rerun()
