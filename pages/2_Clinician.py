import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.session_manager import SessionManager
from datetime import datetime, timedelta

st.set_page_config(page_title="Clinician Dashboard – PhysioForm", layout="wide")

# Custom CSS for professional look
st.markdown("""
<style>
    .dashboard-header {
        background: linear-gradient(135deg, #0066CC 0%, #0084FF 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .dashboard-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .dashboard-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
    }
    .kpi-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-top: 4px solid #0066CC;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .kpi-card h3 {
        margin: 0 0 0.5rem 0;
        color: #6B7280;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0066CC;
    }
    .kpi-change {
        font-size: 0.875rem;
        color: #10B981;
        margin-top: 0.5rem;
    }
    .patient-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #0066CC;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: transform 0.2s;
    }
    .patient-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    .patient-card h4 {
        margin: 0 0 0.5rem 0;
        color: #111827;
        font-weight: 600;
    }
    .patient-card p {
        margin: 0.25rem 0;
        color: #6B7280;
        font-size: 0.875rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .status-active {
        background: #D1FAE5;
        color: #065F46;
    }
    .status-inactive {
        background: #F3F4F6;
        color: #374151;
    }
    .status-alert {
        background: #FEE2E2;
        color: #7F1D1D;
    }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin-top: 1rem;
    }
    .metric-item {
        padding: 0.75rem 0;
        border-bottom: 1px solid #E5E7EB;
    }
    .metric-item:last-child {
        border-bottom: none;
    }
    .metric-label {
        color: #6B7280;
        font-weight: 500;
        font-size: 0.875rem;
    }
    .metric-value {
        color: #0066CC;
        font-weight: 700;
        font-size: 1.1rem;
    }
    .login-container {
        max-width: 400px;
        margin: 3rem auto;
        text-align: center;
    }
    .login-header {
        background: linear-gradient(135deg, #0066CC 0%, #0084FF 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .login-header h1 {
        margin: 0;
        font-size: 2rem;
    }
    .login-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
    }
</style>
""", unsafe_allow_html=True)

# ─── Authentication ─────────────────────────────────────────────────
if "clinician_auth" not in st.session_state:
    st.session_state.clinician_auth = False

if not st.session_state.clinician_auth:
    # Centered login view
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("""
        <div class="login-header">
            <h1>🩺 PhysioForm</h1>
            <p>Clinician Portal</p>
        </div>
        """, unsafe_allow_html=True)
        
        password = st.text_input("Enter clinician password", type="password", label_visibility="collapsed", placeholder="••••••••")
        
        if st.button("🔓 Access Dashboard", use_container_width=True, type="primary"):
            correct_password = st.secrets.get("CLINICIAN_PASSWORD", "admin")
            if password == correct_password:
                st.session_state.clinician_auth = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
    st.stop()

# ─── Dashboard ─────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
    <h1>👨‍⚕️ Clinician Dashboard</h1>
    <p>Patient progress monitoring and analysis</p>
</div>
""", unsafe_allow_html=True)

# Logout button in sidebar
if st.sidebar.button("🔓 Logout", key="logout_btn", use_container_width=True):
    st.session_state.clinician_auth = False
    st.rerun()

# Load data
session_manager = SessionManager()
sessions = session_manager.load_all_sessions()

if not sessions:
    st.info("📋 No sessions recorded yet. Patients will appear here once they complete their first exercise session.")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(sessions)
df['timestamp'] = pd.to_datetime(df['start_time'], unit='s')
df['date'] = df['timestamp'].dt.date
df['week'] = df['timestamp'].dt.isocalendar().week
df['avg_form_quality_pct'] = df['avg_form_quality'] * 100

# ---- Sidebar filters ----
st.sidebar.header("🔍 Filters & Settings")

patients = df['patient_id'].unique()
selected_patient = st.sidebar.selectbox(
    "Select Patient",
    ["All Patients"] + sorted(list(patients)),
    key="patient_filter"
)

exercise_types = sorted(df['exercise'].unique())
selected_exercise = st.sidebar.selectbox(
    "Select Exercise",
    ["All Exercises"] + list(exercise_types),
    key="exercise_filter"
)

# Date range filter
date_range = st.sidebar.slider(
    "Date Range",
    min_value=df['date'].min(),
    max_value=df['date'].max(),
    value=(df['date'].min(), df['date'].max()),
    key="date_range"
)

# Apply filters
mask = pd.Series(True, index=df.index)
if selected_patient != "All Patients":
    mask &= df['patient_id'] == selected_patient
if selected_exercise != "All Exercises":
    mask &= df['exercise'] == selected_exercise
mask &= (df['date'] >= date_range[0]) & (df['date'] <= date_range[1])

filtered_df = df[mask]

# ---- Top KPI cards ----
st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sessions = len(filtered_df)
    week_start = datetime.now().date() - timedelta(days=7)
    week_sessions = len(filtered_df[filtered_df['date'] >= week_start])
    st.markdown(f"""
    <div class="kpi-card">
        <h3>Total Sessions</h3>
        <div class="kpi-value">{total_sessions}</div>
        <div class="kpi-change">📈 {week_sessions} this week</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    avg_reps = filtered_df['reps'].mean() if not filtered_df.empty else 0
    target_reps = 10
    reps_status = "↑ On track" if avg_reps >= target_reps else "↓ Below target"
    st.markdown(f"""
    <div class="kpi-card">
        <h3>Avg Reps / Session</h3>
        <div class="kpi-value">{avg_reps:.1f}</div>
        <div class="kpi-change">{reps_status} (Target: {target_reps})</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    avg_quality = filtered_df['avg_form_quality_pct'].mean() if not filtered_df.empty else 0
    quality_trend = "↑" if avg_quality > 80 else "↓" if avg_quality < 60 else "→"
    quality_status = 'Excellent' if avg_quality > 85 else 'Good' if avg_quality > 70 else 'Needs Work'
    st.markdown(f"""
    <div class="kpi-card">
        <h3>Avg Form Quality</h3>
        <div class="kpi-value">{avg_quality:.1f}%</div>
        <div class="kpi-change">{quality_trend} {quality_status}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    unique_patients = filtered_df['patient_id'].nunique()
    active_patients = len(filtered_df[filtered_df['date'] >= week_start]['patient_id'].unique())
    st.markdown(f"""
    <div class="kpi-card">
        <h3>Active Patients</h3>
        <div class="kpi-value">{unique_patients}</div>
        <div class="kpi-change">👥 {active_patients} this week</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ---- Main Charts ----
if not filtered_df.empty:
    
    # Row 1: Quality & Reps Trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Form Quality Trend")
        quality_over_time = filtered_df.groupby('date')['avg_form_quality_pct'].agg(['mean', 'std']).reset_index()
        quality_over_time['std'] = quality_over_time['std'].fillna(0)
        
        fig1 = go.Figure()
        
        # Main line
        fig1.add_trace(go.Scatter(
            x=quality_over_time['date'],
            y=quality_over_time['mean'],
            mode='lines+markers',
            name='Average Quality',
            line=dict(color='#0066CC', width=2),
            marker=dict(size=8)
        ))
        
        # Upper bound
        fig1.add_trace(go.Scatter(
            x=quality_over_time['date'],
            y=quality_over_time['mean'] + quality_over_time['std'],
            fill=None,
            mode='lines',
            line_color='rgba(0,0,0,0)',
            showlegend=False,
            name='Upper Bound'
        ))
        
        # Lower bound
        fig1.add_trace(go.Scatter(
            x=quality_over_time['date'],
            y=quality_over_time['mean'] - quality_over_time['std'],
            fill='tonexty',
            mode='lines',
            line_color='rgba(0,0,0,0)',
            name='Confidence Band',
            fillcolor='rgba(0, 102, 204, 0.2)'
        ))
        
        fig1.update_yaxes(range=[0, 100])
        fig1.update_layout(
            height=400,
            hovermode='x unified',
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("💪 Reps Per Session")
        reps_over_time = filtered_df.groupby('date')['reps'].sum().reset_index()
        
        fig2 = px.bar(
            reps_over_time,
            x='date',
            y='reps',
            color='reps',
            color_continuous_scale='Blues',
            labels={'reps': 'Total Reps', 'date': 'Date'}
        )
        fig2.update_layout(
            height=400,
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    st.divider()
    
    # Row 2: Exercise Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💪 Form Quality by Exercise")
        quality_by_exercise = filtered_df.groupby('exercise')['avg_form_quality_pct'].mean().reset_index()
        quality_by_exercise = quality_by_exercise.sort_values('avg_form_quality_pct', ascending=True)
        
        fig3 = px.bar(
            quality_by_exercise,
            x='avg_form_quality_pct',
            y='exercise',
            color='avg_form_quality_pct',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100],
            labels={'avg_form_quality_pct': 'Quality (%)', 'exercise': 'Exercise'},
            text='avg_form_quality_pct'
        )
        fig3.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
        fig3.update_xaxes(range=[0, 100])
        fig3.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        st.subheader("📊 Reps by Exercise")
        reps_by_exercise = filtered_df.groupby('exercise')['reps'].mean().reset_index()
        reps_by_exercise = reps_by_exercise.sort_values('reps', ascending=True)
        
        fig4 = px.bar(
            reps_by_exercise,
            x='reps',
            y='exercise',
            color='reps',
            color_continuous_scale='Blues',
            labels={'reps': 'Avg Reps', 'exercise': 'Exercise'},
            text='reps'
        )
        fig4.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig4.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    st.divider()
    
    # Patient roster with detailed cards
    st.subheader("👥 Patient Roster")
    
    patient_summary = filtered_df.groupby('patient_id').agg({
        'reps': ['sum', 'mean'],
        'avg_form_quality_pct': 'mean',
        'timestamp': 'max'
    }).reset_index()
    
    patient_summary.columns = ['patient_id', 'total_reps', 'avg_reps_per_session', 'avg_form_quality', 'last_session']
    patient_summary['sessions_count'] = filtered_df.groupby('patient_id').size().values
    
    # Determine status
    def get_patient_status(last_session_date):
        days_ago = (datetime.now() - last_session_date).days
        if days_ago < 7:
            return 'Active'
        elif days_ago < 30:
            return 'Inactive'
        else:
            return 'At Risk'
    
    patient_summary['status'] = patient_summary['last_session'].apply(get_patient_status)
    patient_summary = patient_summary.sort_values('last_session', ascending=False)
    
    # Display patient cards
    for idx, row in patient_summary.iterrows():
        status_class = 'status-active' if row['status'] == 'Active' else ('status-alert' if row['status'] == 'At Risk' else 'status-inactive')
        patient_display_name = row['patient_id'].split('@')[0]
        
        st.markdown(f"""
        <div class="patient-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <h4>{patient_display_name}</h4>
                    <p>{row['patient_id']}</p>
                    <p style="margin-top: 0.5rem; color: #9CA3AF; font-size: 0.8rem;">Last session: {row['last_session'].strftime('%b %d, %Y at %I:%M %p')}</p>
                </div>
                <div style="text-align: right;">
                    <div class="status-badge {status_class}">{row['status']}</div>
                    <div class="metric-grid">
                        <div class="metric-item">
                            <span class="metric-label">Sessions</span>
                            <div class="metric-value">{row['sessions_count']}</div>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Avg Reps</span>
                            <div class="metric-value">{row['avg_reps_per_session']:.1f}</div>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Form Quality</span>
                            <div class="metric-value">{row['avg_form_quality']:.0f}%</div>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Total Reps</span>
                            <div class="metric-value">{int(row['total_reps'])}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Detailed Session Log
    st.subheader("📋 Detailed Session Log")
    
    display_cols = ['patient_id', 'exercise', 'reps', 'avg_form_quality_pct', 'duration', 'date', 'timestamp']
    display_df = filtered_df[display_cols].copy()
    display_df['duration_min'] = (display_df['duration'] / 60).round(1)
    display_df['time'] = display_df['timestamp'].dt.strftime('%I:%M %p')
    display_df['avg_form_quality_pct'] = display_df['avg_form_quality_pct'].round(1)
    
    display_df = display_df.rename(columns={
        'patient_id': 'Patient',
        'exercise': 'Exercise',
        'reps': 'Reps',
        'avg_form_quality_pct': 'Quality (%)',
        'duration_min': 'Duration (min)',
        'date': 'Date',
        'time': 'Time'
    })
    
    display_df = display_df[['Patient', 'Exercise', 'Reps', 'Quality (%)', 'Duration (min)', 'Date', 'Time']]
    display_df = display_df.sort_values('Date', ascending=False)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Export functionality
    st.subheader("📥 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"physioform_sessions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Generate PDF summary (optional - requires reportlab)
        st.info("💡 Export data regularly for your clinical records and patient follow-ups.")
else:
    st.warning("No data matches your current filters. Try adjusting the selection.")
