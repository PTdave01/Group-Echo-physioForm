import streamlit as st

st.set_page_config(
    page_title="PhysioForm", 
    page_icon="🩺", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS for better styling ──
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
    }
    .welcome-header {
        background: linear-gradient(135deg, #0066CC 0%, #0084FF 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .welcome-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .welcome-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.95;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #0066CC;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    .feature-card h3 {
        margin-top: 0;
        color: #0066CC;
    }
    .button-container {
        display: flex;
        gap: 1rem;
        margin-top: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-top: 4px solid #10B981;
    }
    .metric-card h3 {
        margin: 0 0 0.5rem 0;
        color: #6B7280;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0066CC;
    }
</style>
""", unsafe_allow_html=True)

# ── Not logged in ───────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    # Hero Section
    st.markdown("""
    <div class="welcome-header">
        <h1>🩺 PhysioForm</h1>
        <p>AI-Powered Home Physiotherapy Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Why Choose PhysioForm?")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🤖 AI-Powered Form Detection</h3>
            Real-time analysis of your exercise form with instant feedback.
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Clinician Oversight</h3>
            Professional tracking and progress monitoring by your therapist.
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📱 Home-Based Care</h3>
            Complete your physiotherapy exercises from anywhere.
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### Get Started")
    
    col1, col2 = st.columns(2)
    with col1:
        st.link_button(
            "🔐 Login / Sign Up",
            "pages/0_Login.py",
            use_container_width=True,
            type="primary"
        )
    with col2:
        st.link_button(
            "👨‍⚕️ Clinician Dashboard",
            "pages/2_Clinician.py",
            use_container_width=True
        )

# ── Logged in ───────────────────────────────────────────────────────
else:
    user_first_name = st.session_state.user['email'].split('@')[0]
    
    st.markdown(f"""
    <div class="welcome-header">
        <h1>Welcome back, {user_first_name}! 👋</h1>
        <p>Let's continue your therapy journey</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.link_button(
            "🏃 Start Exercise Session",
            "pages/1_Patient.py",
            use_container_width=True,
            type="primary"
        )
    with col2:
        st.link_button(
            "📊 View Your Progress",
            "pages/3_Progress.py",
            use_container_width=True
        )
    
    st.divider()
    
    # Quick stats for logged-in users
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Sessions Completed</h3>
            <div class="value">4</div>
            <p style="margin: 0.5rem 0 0 0; color: #10B981; font-size: 0.875rem;">+1 this week</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>Current Streak</h3>
            <div class="value">3</div>
            <p style="margin: 0.5rem 0 0 0; color: #F59E0B; font-size: 0.875rem;">🔥 days</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>Form Quality</h3>
            <div class="value">94%</div>
            <p style="margin: 0.5rem 0 0 0; color: #10B981; font-size: 0.875rem;">↑ 2%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.rep_count = 0
        st.session_state.recognized_exercise = None
        st.rerun()
