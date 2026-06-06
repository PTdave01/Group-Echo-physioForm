import streamlit as st
from supabase import create_client, Client
import time

st.set_page_config(page_title="Login – PhysioForm", layout="centered")

st.markdown("""
<style>
    .login-container {
        max-width: 420px;
        margin: 2rem auto;
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-header h1 {
        color: #0066CC;
        margin: 0;
        font-size: 2rem;
    }
    .login-header p {
        color: #6B7280;
        margin: 0.5rem 0 0 0;
    }
    .input-label {
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.5rem;
        display: block;
    }
    .tab-content {
        padding: 1.5rem 0;
    }
    .success-message {
        background: #D1FAE5;
        color: #065F46;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #10B981;
        margin-bottom: 1rem;
    }
    .error-message {
        background: #FEE2E2;
        color: #7F1D1D;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #EF4444;
        margin-bottom: 1rem;
    }
    .info-message {
        background: #DBEAFE;
        color: #0C4A6E;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0066CC;
        margin-bottom: 1rem;
    }
    .divider-text {
        text-align: center;
        color: #9CA3AF;
        margin: 1.5rem 0;
        font-size: 0.875rem;
    }
    .footer-text {
        text-align: center;
        color: #6B7280;
        font-size: 0.875rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# If already logged in
if "user" in st.session_state and st.session_state.user is not None:
    st.markdown("""
    <div class="login-container">
        <div class="success-message">
            ✅ <strong>Already logged in</strong><br>
            You're signed in as: <strong>{}</strong>
        </div>
    </div>
    """.format(st.session_state.user['email']), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Go to Home", use_container_width=True, type="primary"):
            st.switch_page("app.py")
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    st.stop()

# ── Setup Supabase ──
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Header
st.markdown("""
<div class="login-container">
    <div class="login-header">
        <h1>🩺 PhysioForm</h1>
        <p>Sign in to your account</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2 = st.tabs(["Login", "Sign Up"])

with tab1:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    
    st.markdown('<label class="input-label">Email Address</label>', unsafe_allow_html=True)
    email = st.text_input("Email", key="login_email", label_visibility="collapsed", placeholder="you@example.com")
    
    st.markdown('<label class="input-label">Password</label>', unsafe_allow_html=True)
    password = st.text_input("Password", type="password", key="login_password", label_visibility="collapsed", placeholder="••••••••")
    
    if st.button("Sign In", use_container_width=True, type="primary"):
        if not email or not password:
            st.markdown("""
            <div class="error-message">
                ⚠️ <strong>Please enter both email and password</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            try:
                with st.spinner("🔐 Signing in..."):
                    response = supabase.auth.sign_in_with_password(
                        {"email": email, "password": password}
                    )
                    user = response.user
                    if user:
                        st.session_state.user = {"id": user.id, "email": user.email}
                        st.markdown("""
                        <div class="success-message">
                            ✅ <strong>Logged in successfully!</strong><br>
                            Redirecting...
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(1.5)
                        st.switch_page("app.py")
            except Exception as e:
                error_msg = str(e)
                if "Invalid login credentials" in error_msg:
                    error_msg = "Invalid email or password"
                elif "User not found" in error_msg:
                    error_msg = "No account found with this email"
                st.markdown(f"""
                <div class="error-message">
                    ❌ <strong>Login failed</strong><br>
                    {error_msg[:80]}
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer-text">
        Don't have an account? <strong>Sign up below</strong> ⬇️
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    
    st.markdown('<label class="input-label">Email Address</label>', unsafe_allow_html=True)
    new_email = st.text_input("Email", key="signup_email", label_visibility="collapsed", placeholder="you@example.com")
    
    st.markdown('<label class="input-label">Password</label>', unsafe_allow_html=True)
    new_password = st.text_input("Password", type="password", key="signup_password", label_visibility="collapsed", placeholder="••••••••")
    
    st.markdown('<label class="input-label">Confirm Password</label>', unsafe_allow_html=True)
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password", label_visibility="collapsed", placeholder="••••••••")
    
    # Password requirements info
    st.markdown("""
    <div class="info-message">
        <strong>Password requirements:</strong><br>
        • At least 6 characters<br>
        • Combination of letters and numbers recommended
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Create Account", use_container_width=True, type="primary"):
        # Validation
        if not new_email or not new_password:
            st.markdown("""
            <div class="error-message">
                ⚠️ <strong>Please fill in all fields</strong>
            </div>
            """, unsafe_allow_html=True)
        elif new_password != confirm_password:
            st.markdown("""
            <div class="error-message">
                ⚠️ <strong>Passwords do not match</strong><br>
                Please check and try again.
            </div>
            """, unsafe_allow_html=True)
        elif len(new_password) < 6:
            st.markdown("""
            <div class="error-message">
                ⚠️ <strong>Password too short</strong><br>
                Password must be at least 6 characters.
            </div>
            """, unsafe_allow_html=True)
        else:
            try:
                with st.spinner("📝 Creating account..."):
                    response = supabase.auth.sign_up(
                        {"email": new_email, "password": new_password}
                    )
                    user = response.user
                    if user:
                        st.session_state.user = {"id": user.id, "email": user.email}
                        st.markdown("""
                        <div class="success-message">
                            ✅ <strong>Account created successfully!</strong><br>
                            Redirecting to home page...
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(1.5)
                        st.switch_page("app.py")
            except Exception as e:
                error_msg = str(e)
                if "already registered" in error_msg.lower():
                    error_msg = "This email is already registered. Please login instead."
                elif "invalid email" in error_msg.lower():
                    error_msg = "Please enter a valid email address."
                st.markdown(f"""
                <div class="error-message">
                    ❌ <strong>Sign up failed</strong><br>
                    {error_msg[:80]}
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="footer-text">
        Already have an account? <strong>Sign in above</strong> ⬆️
    </div>
    """, unsafe_allow_html=True)
