import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.session_manager import SessionManager
from datetime import datetime, timedelta

st.set_page_config(page_title="Clinician Dashboard – PhysioForm", layout="wide")

# ── Custom CSS ──────────────────────────────────────────────────────
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

# ─── Authentication ─────────────────────────────────────────────────
if "clinician_auth" not in st.session_state:
    st.session_state.clinician_auth = False

if not st.session_state.clinician_auth:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="dashboard-header"><h1>🩺 PhysioForm</h1><p>Clinician Portal</p></div>', unsafe_allow_html=True)
        password = st.text_input("Enter clinician password", type="password")
        if st.button("🔓 Access Dashboard", use_container_width=True, type="primary"):
            if password == st.secrets.get("CLINICIAN_PASSWORD", "admin"):
                st.session_state.clinician_auth = True
                st.rerun()
            else:
                st.error("❌ Incorrect password.")
    st.stop()

# ─── Sidebar logout ─────────────────────────────────────────────────
if st.sidebar.button("🔓 Logout", use_container_width=True):
    st.session_state.clinician_auth = False
    st.rerun()

# ─── Load data ──────────────────────────────────────────────────────
session_manager = SessionManager()
sessions = session_manager.load_all_sessions()

if not sessions:
    st.info("📋 No sessions recorded yet. Patients will appear after their first exercise.")
    st.stop()

df = pd.DataFrame(sessions)
df['timestamp'] = pd.to_datetime(df['start_time'], unit='s')
df['date'] = df['timestamp'].dt.date
df['week'] = df['timestamp'].dt.isocalendar().week
df['avg_form_quality_pct'] = df['avg_form_quality'] * 100

# ─── Sidebar filters ────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
patients = sorted(df['patient_id'].unique())
selected_patient = st.sidebar.selectbox("Patient", ["All Patients"] + patients)
exercises = sorted(df['exercise'].unique())
selected_exercise = st.sidebar.selectbox("Exercise", ["All Exercises"] + exercises)
date_min = df['date'].min()
date_max = df['date'].max()
date_range = st.sidebar.slider("Date Range", min_value=date_min, max_value=date_max, value=(date_min, date_max))

# Apply filters
mask = pd.Series(True, index=df.index)
if selected_patient != "All Patients":
    mask &= df['patient_id'] == selected_patient
if selected_exercise != "All Exercises":
    mask &= df['exercise'] == selected_exercise
mask &= (df['date'] >= date_range[0]) & (df['date'] <= date_range[1])
filtered_df = df[mask]

# ─── Header ─────────────────────────────────────────────────────────
st.markdown('<div class="dashboard-header"><h1>👨‍⚕️ Clinician Dashboard</h1><p>Patient progress monitoring</p></div>', unsafe_allow_html=True)

# ─── KPI cards ──────────────────────────────────────────────────────
st.subheader("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

total_sessions = len(filtered_df)
week_ago = datetime.now().date() - timedelta(days=7)
week_sessions = len(filtered_df[filtered_df['date'] >= week_ago])
col1.markdown(f'<div class="kpi-card"><h3>Total Sessions</h3><div class="kpi-value">{total_sessions}</div><div class="kpi-change">📈 {week_sessions} this week</div></div>', unsafe_allow_html=True)

avg_reps = filtered_df['reps'].mean() if not filtered_df.empty else 0
col2.markdown(f'<div class="kpi-card"><h3>Avg Reps / Session</h3><div class="kpi-value">{avg_reps:.1f}</div><div class="kpi-change">Target: 10</div></div>', unsafe_allow_html=True)

avg_quality = filtered_df['avg_form_quality_pct'].mean() if not filtered_df.empty else 0
quality_status = "Excellent" if avg_quality >= 85 else "Good" if avg_quality >= 70 else "Needs Work"
col3.markdown(f'<div class="kpi-card"><h3>Avg Form Quality</h3><div class="kpi-value">{avg_quality:.1f}%</div><div class="kpi-change">{quality_status}</div></div>', unsafe_allow_html=True)

unique_patients = filtered_df['patient_id'].nunique()
active_this_week = len(filtered_df[filtered_df['date'] >= week_ago]['patient_id'].unique())
col4.markdown(f'<div class="kpi-card"><h3>Active Patients</h3><div class="kpi-value">{unique_patients}</div><div class="kpi-change">👥 {active_this_week} this week</div></div>', unsafe_allow_html=True)

st.divider()

if not filtered_df.empty:
    # ─── Charts ────────────────────────────────────────────────────────
    st.subheader("📈 Progress Over Time")
    col1, col2 = st.columns(2)

    with col1:
        quality_daily = filtered_df.groupby('date')['avg_form_quality_pct'].mean().reset_index()
        fig = px.line(quality_daily, x='date', y='avg_form_quality_pct', title='Avg Form Quality (%)', markers=True)
        fig.update_yaxes(range=[0, 100])
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        reps_daily = filtered_df.groupby('date')['reps'].sum().reset_index()
        fig = px.bar(reps_daily, x='date', y='reps', title='Total Reps per Day', color='reps', color_continuous_scale='Blues')
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("💪 Exercise Breakdown")
    col1, col2 = st.columns(2)

    with col1:
        qual_ex = filtered_df.groupby('exercise')['avg_form_quality_pct'].mean().reset_index()
        fig = px.bar(qual_ex, x='exercise', y='avg_form_quality_pct', color='exercise', title='Quality by Exercise', text_auto='.1f')
        fig.update_yaxes(range=[0, 100])
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Show sets completed over time (10‑rep chunks)
        # We treat any record where reps == 10 as a set, but also accumulate from final summaries
        sets_over_time = filtered_df.groupby('date').apply(lambda x: (x['reps'] // 10).sum() + (1 if any(x['reps'] % 10 > 0) else 0)).reset_index(name='sets')
        fig = px.bar(sets_over_time, x='date', y='sets', title='Sets Completed per Day', color='sets', color_continuous_scale='greens')
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ─── Patient Roster ────────────────────────────────────────────────
    st.subheader("👥 Patient Roster")
    patient_summary = filtered_df.groupby('patient_id').agg(
        total_reps=('reps', 'sum'),
        avg_reps_per_session=('reps', 'mean'),
        avg_form_quality=('avg_form_quality_pct', 'mean'),
        last_session=('timestamp', 'max'),
        sessions_count=('reps', 'count'),
        total_sets=('reps', lambda x: (x // 10).sum() + (1 if any(x % 10 > 0) else 0))
    ).reset_index()

    def status(last_date):
        days = (datetime.now() - last_date).days
        return 'Active' if days < 7 else ('At Risk' if days < 30 else 'Inactive')

    patient_summary['status'] = patient_summary['last_session'].apply(status)
    patient_summary = patient_summary.sort_values('last_session', ascending=False)

    for _, row in patient_summary.iterrows():
        status_class = 'status-active' if row['status'] == 'Active' else 'status-alert' if row['status'] == 'At Risk' else 'status-inactive'
        display_name = row['patient_id'].split('@')[0]
        st.markdown(f"""
        <div class="patient-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <h4>{display_name}</h4>
                    <p>{row['patient_id']}</p>
                    <p style="font-size:0.8rem; color:#9CA3AF;">Last session: {row['last_session'].strftime('%b %d, %Y %I:%M %p')}</p>
                </div>
                <div style="text-align:right;">
                    <span class="status-badge {status_class}">{row['status']}</span>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; margin-top:0.75rem;">
                        <div><small>Sessions</small><br><strong>{row['sessions_count']}</strong></div>
                        <div><small>Total Sets</small><br><strong>{row['total_sets']}</strong></div>
                        <div><small>Avg Reps</small><br><strong>{row['avg_reps_per_session']:.1f}</strong></div>
                        <div><small>Form Quality</small><br><strong>{row['avg_form_quality']:.0f}%</strong></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ─── Session Log ──────────────────────────────────────────────────
    st.subheader("📋 Detailed Session Log")
    log_df = filtered_df[['patient_id', 'exercise', 'reps', 'avg_form_quality_pct', 'duration', 'date', 'timestamp']].copy()
    log_df['duration_min'] = (log_df['duration'] / 60).round(1)
    log_df['time'] = log_df['timestamp'].dt.strftime('%I:%M %p')
    log_df['sets'] = log_df['reps'] // 10  # whole sets from this record
    log_df = log_df.rename(columns={
        'patient_id': 'Patient', 'exercise': 'Exercise', 'reps': 'Reps',
        'avg_form_quality_pct': 'Quality (%)', 'duration_min': 'Duration (min)',
        'date': 'Date', 'time': 'Time', 'sets': 'Sets'
    })
    log_df = log_df[['Patient', 'Exercise', 'Reps', 'Sets', 'Quality (%)', 'Duration (min)', 'Date', 'Time']].sort_values('Date', ascending=False)
    st.dataframe(log_df, use_container_width=True, hide_index=True)

    # ─── Export ───────────────────────────────────────────────────────
    st.subheader("📥 Export Data")
    csv = log_df.to_csv(index=False)
    st.download_button("📥 Download as CSV", csv, f"physioform_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")
else:
    st.warning("No data matches the selected filters.")
