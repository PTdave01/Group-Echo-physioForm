import streamlit as st

def set_page_style():
    st.markdown("""
    <style>
    /* ── Full‑screen background image (clinical physiotherapy scene) ── */
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1576091160550-2173dba999e5?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* ── Dark overlay to keep text readable ── */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 60, 80, 0.4);   /* teal‑blue tint */
        z-index: 0;
        pointer-events: none;
    }

    /* ── Main content container – clean white card ── */
    .block-container {
        position: relative;
        z-index: 1;
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(12px);
        border-radius: 24px;
        padding: 2rem 3rem;
        margin-top: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }

    /* ── Headers – clinical teal ── */
    h1, h2, h3 {
        color: #0a5c6e;
    }

    /* ── Buttons – warm teal ── */
    .stButton > button {
        background-color: #0b6477;
        color: white;
        border-radius: 12px;
        padding: 0.5rem 1.5rem;
        border: none;
        font-weight: 600;
        transition: 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #0a5c6e;
        transform: scale(1.02);
    }

    /* ── Metric cards – subtle teal border ── */
    [data-testid="stMetric"] {
        background: rgba(11, 100, 119, 0.06);
        border-left: 4px solid #0b6477;
        padding: 0.5rem 1rem;
        border-radius: 8px;
    }

    /* ── Sidebar – clean white ── */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e2e8f0;
    }

    /* ── Make text inside cards crisp ── */
    p, label, span {
        color: #1a202c;
    }
    </style>
    """, unsafe_allow_html=True)
