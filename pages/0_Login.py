import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Login – PhysioForm", layout="wide")

# If already logged in, show simple page with logout & home link
if "user" in st.session_state and st.session_state.user is not None:
    st.success(f"You are already logged in as {st.session_state.user['email']}")
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()
    st.page_link("app.py", label="🏠 Go to Home")
    st.stop()

# ── Normal login / sign‑up ──
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

tab1, tab2 = st.tabs(["Login", "Sign Up"])

with tab1:
    st.subheader("Login to your account")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user = response.user
            if user:
                st.session_state.user = {"id": user.id, "email": user.email}
                st.success("Logged in successfully!")
                st.rerun()   # will show the "already logged in" view, then user can go home
        except Exception as e:
            st.error(f"Login failed: {e}")

with tab2:
    st.subheader("Create a new account")
    new_email = st.text_input("Email", key="signup_email")
    new_password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
    if st.button("Sign Up"):
        if new_password != confirm_password:
            st.error("Passwords do not match")
        elif len(new_password) < 6:
            st.error("Password must be at least 6 characters")
        else:
            try:
                response = supabase.auth.sign_up({"email": new_email, "password": new_password})
                user = response.user
                if user:
                    st.session_state.user = {"id": user.id, "email": user.email}
                    st.success("Account created and logged in!")
                    st.rerun()
            except Exception as e:
                st.error(f"Sign up failed: {e}")
