import streamlit as st

st.set_page_config(page_title="PhysioForm", page_icon="🩺", layout="wide")

# ── Not logged in ───────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.title("Welcome to PhysioForm")
    st.markdown("### AI-Powered Home Physiotherapy")
    st.info("Please log in or sign up to start your exercise session.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/0_Login.py", label="🔐 Login / Sign Up", icon="🔐")
    with col2:
        st.page_link("pages/2_Clinician.py", label="👨‍⚕️ Clinician Dashboard", icon="👨‍⚕️")

# ── Logged in ───────────────────────────────────────────────────────
else:
    st.title(f"🩺 PhysioForm – Welcome, {st.session_state.user['email']}")
    st.markdown("Select an option below to begin.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/1_Patient.py", label="🧑‍⚕️ Start Exercise", icon="🧑‍⚕️")
    with col2:
        st.page_link("pages/2_Clinician.py", label="👨‍⚕️ Clinician Dashboard", icon="👨‍⚕️")
    
    # ── Logout button (at the bottom of the page) ──
    st.divider()
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.rep_count = 0
        st.session_state.recognized_exercise = None
        st.rerun()
