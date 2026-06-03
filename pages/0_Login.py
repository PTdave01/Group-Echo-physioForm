import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Login – PhysioForm", layout="wide")

# Initialize Supabase client (using secrets)
url = st.secrets["https://wnwktjulzpvqojpakunr.supabase.co"]
key = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indud2t0anVsenB2cW9qcGFrdW5yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA0NzY2MzcsImV4cCI6MjA5NjA1MjYzN30.7yYPDJeULk5YCih--0alw6l4lLAYtS4lYsUJH7JaCeE"]
supabase: Client = create_client(url, key)

if "user" in st.session_state and st.session_state.user is not None:
    st.success(f"You are logged in as {st.session_state.user['email']}")
    st.page_link("pages/1_Patient.py", label="Go to Exercise Page")
    st.stop()

tab1, tab2 = st.tabs(["Login", "Sign Up"])

# ── Login tab ──
with tab1:
    st.subheader("Login to your account")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            # Extract user info
            user = response.user
            if user:
                st.session_state.user = {
                    "id": user.id,
                    "email": user.email
                }
                st.success("Logged in successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

# ── Sign Up tab ──
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
                    # Optionally, you can force email confirmation. For now, auto-confirm if email verification is off.
                    st.session_state.user = {
                        "id": user.id,
                        "email": user.email
                    }
                    st.success("Account created and logged in!")
                    st.rerun()
            except Exception as e:
                st.error(f"Sign up failed: {e}")
