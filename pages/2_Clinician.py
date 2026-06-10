import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.session_manager import SessionManager
from datetime import datetime, timedelta

st.set_page_config(page_title="Clinician Dashboard – PhysioForm", layout="wide")

st.markdown("""
<style>
    .dashboard-header { background: linear-gradient(135deg, #0066CC, #0084FF); padding: 2rem; border-radius: 10px; color: white; margin-bottom: 2rem; }
    .kpi-card { background: white; padding: 1.5rem; border-radius: 10px; border-top: 4px solid #0066CC; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .kpi-card h3 { margin: 0 0 0.5rem 0; color: #6B7280; font-size: 0.875rem; text-transform: uppercase; }
    .kpi-value { font-size: 2rem; font-weight: 700; color: #0066CC; }
    .kpi-change { font-size: 0.875rem; color: #10B981; margin-top: 0.5rem; }
    .patient-card { background: white; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #0066CC; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .patient-card h4 { margin: 0 0 0.5rem 0; color: #111827; font-weight: 600; }
    .status-badge { display: inline-block; padding: 0.35rem 0.85rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .status-active { background: #D1FAE5; color: #065F46; }
    .status-inactive { background: #F3F4F6; color: #374151; }
    .status-alert { background: #FEE2E2; color: #7F1D1D; }
</style>
""", unsafe_allow_html=True)

# Auth
if "clinician_auth" not in st.session_state:
    st.session_state.clinician_auth = False
if not st.session_state.clinician_auth:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="dashboard-header"><h1>🩺 PhysioForm</h1><p>Clinician Portal</p></div>', unsafe_allow_html=True)
        password = st.text_input("Password", type="password")
        if st.button("Access Dashboard", use_container_width=True, type="primary"):
            if password == st.secrets.get("CLINICIAN_PASSWORD", "admin"):
                st.session_state.clinician_auth = True
                st.rerun()
            else:
                st.error("Incorrect password")
    st.stop()

if st.sidebar.button("🔓 Logout", use_container_width=True):
    st.session_state.clinician_auth = False
    st.rerun()

# Load data
session_manager = SessionManager()
sessions = session_manager.load_all_sessions()
if not sessions:
    st.info("No sessions yet.")
    st.stop()

df = pd.DataFrame(sessions)
df['timestamp'] = pd.to_datetime(df['start_time'], unit='s')
df['date'] = df['timestamp'].dt.date
df['week'] = df['timestamp'].dt.isocalendar().week
df['quality_pct'] = df['avg_form_quality'] * 100

# Filters
st.sidebar.header("Filters")
patients = sorted(df['patient_id'].unique())
selected_patient = st.sidebar.selectbox("Patient", ["All"] + patients)
exercises = sorted(df['exercise'].unique())
selected_exercise = st.sidebar.selectbox("Exercise", ["All"] + exercises)
date_min = df['date'].min()
date_max = df['date'].max()
date_range = st.sidebar.slider("Date Range", min_value=date_min, max_value=date_max, value=(date_min, date_max))

mask = pd.Series(True, index=df.index)
if selected_patient != "All":
    mask &= df['patient_id'] == selected_patient
if selected_exercise != "All":
    mask &= df['exercise'] == selected_exercise
mask &= (df['date'] >= date_range[0]) & (df['date'] <= date_range[1])
filtered_df = df[mask]

# Header
st.markdown('<div class="dashboard-header"><h1>👨‍⚕️ Clinician Dashboard</h1></div>', unsafe_allow_html=True)

# KPIs
total_sessions = len(filtered_df)
week_ago = datetime.now().date() - timedelta(days=7)
week_sessions = len(filtered_df[filtered_df['date'] >= week_ago])
avg_reps = filtered_df['reps'].mean() if not filtered_df.empty else 0
avg_quality = filtered_df['quality_pct'].mean() if not filtered_df.empty else 0
unique_patients = filtered_df['patient_id'].nunique()
active_week = len(filtered_df[filtered_df['date'] >= week_ago]['patient_id'].unique())

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f'<div class="kpi-card"><h3>Sessions</h3><div class="kpi-value">{total_sessions}</div><div class="kpi-change">{week_sessions} this week</div></div>', unsafe_allow_html=True)
col2.markdown(f'<div class="kpi-card"><h3>Avg Reps/Session</h3><div class="kpi-value">{avg_reps:.1f}</div></div>', unsafe_allow_html=True)
col3.markdown(f'<div class="kpi-card"><h3>Avg Quality</h3><div class="kpi-value">{avg_quality:.1f}%</div></div>', unsafe_allow_html=True)
col4.markdown(f'<div class="kpi-card"><h3>Active Patients</h3><div class="kpi-value">{unique_patients}</div><div class="kpi-change">{active_week} this week</div></div>', unsafe_allow_html=True)

st.divider()

if not filtered_df.empty:
    # Charts
    st.subheader("📈 Trends")
    c1, c2 = st.columns(2)
    with c1:
        qual_daily = filtered_df.groupby('date')['quality_pct'].mean().reset_index()
        fig = px.line(qual_daily, x='date', y='quality_pct', title='Avg Form Quality', markers=True)
        fig.update_yaxes(range=[0, 100])
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        reps_daily = filtered_df.groupby('date')['reps'].sum().reset_index()
        fig = px.bar(reps_daily, x='date', y='reps', title='Total Reps per Day', color='reps', color_continuous_scale='Blues')
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("💪 Exercise Analysis")
    c1, c2 = st.columns(2)
    with c1:
        qual_ex = filtered_df.groupby('exercise')['quality_pct'].mean().reset_index()
        fig = px.bar(qual_ex, x='exercise', y='quality_pct', color='exercise', title='Quality by Exercise', text_auto='.1f')
        fig.update_yaxes(range=[0, 100])
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        # Sets = number of records where reps == 10 (auto-sets)
        sets_daily = filtered_df[filtered_df['reps'] == 10].groupby('date').size().reset_index(name='sets')
        fig = px.bar(sets_daily, x='date', y='sets', title='Full Sets per Day', color='sets', color_continuous_scale='greens')
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    # Patient roster
    st.subheader("👥 Patient Roster")
    patient_df = filtered_df.groupby('patient_id').agg(
        total_reps=('reps', 'sum'),
        full_sets=('reps', lambda x: (x == 10).sum()),
        avg_quality=('quality_pct', 'mean'),
        sessions=('reps', 'count'),
        last_session=('timestamp', 'max')
    ).reset_index()

    def status(last):
        days = (datetime.now() - last).days
        return 'Active' if days < 7 else ('At Risk' if days < 30 else 'Inactive')

    patient_df['status'] = patient_df['last_session'].apply(status)
    patient_df = patient_df.sort_values('last_session', ascending=False)

    for _, row in patient_df.iterrows():
        sc = 'status-active' if row['status'] == 'Active' else 'status-alert' if row['status'] == 'At Risk' else 'status-inactive'
        display_name = row['patient_id'].split('@')[0]
        st.markdown(f"""
        <div class="patient-card">
            <div style="display:flex; justify-content:space-between;">
                <div><h4>{display_name}</h4><p>{row['patient_id']}</p><p style="font-size:0.8rem;">Last: {row['last_session'].strftime('%b %d, %Y %I:%M %p')}</p></div>
                <div style="text-align:right;">
                    <span class="status-badge {sc}">{row['status']}</span>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; margin-top:0.5rem;">
                        <div><small>Sessions</small><br><strong>{row['sessions']}</strong></div>
                        <div><small>Full Sets</small><br><strong>{row['full_sets']}</strong></div>
                        <div><small>Total Reps</small><br><strong>{int(row['total_reps'])}</strong></div>
                        <div><small>Avg Quality</small><br><strong>{row['avg_quality']:.0f}%</strong></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Session log
    st.subheader("📋 Session Log")
    log = filtered_df[['patient_id', 'exercise', 'reps', 'quality_pct', 'duration', 'date', 'timestamp']].copy()
    log['duration_min'] = (log['duration'] / 60).round(1)
    log['time'] = log['timestamp'].dt.strftime('%I:%M %p')
    # Sets column: only if reps == 10
    log['full_sets'] = (log['reps'] == 10).astype(int)
    log = log.rename(columns={'patient_id': 'Patient', 'exercise': 'Exercise', 'reps': 'Reps',
                               'quality_pct': 'Quality (%)', 'duration_min': 'Duration (min)',
                               'date': 'Date', 'time': 'Time', 'full_sets': 'Full Sets'})
    log = log[['Patient', 'Exercise', 'Reps', 'Full Sets', 'Quality (%)', 'Duration (min)', 'Date', 'Time']].sort_values('Date', ascending=False)
    st.dataframe(log, use_container_width=True, hide_index=True)

    # Export
    csv = log.to_csv(index=False)
    st.download_button("📥 Download CSV", csv, f"physioform_export_{datetime.now():%Y%m%d_%H%M%S}.csv", "text/csv")
else:
    st.warning("No data with current filters.")
