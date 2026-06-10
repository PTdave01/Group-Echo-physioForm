import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from utils.session_manager import SessionManager

st.set_page_config(page_title="My Progress – PhysioForm", layout="wide")

# ── Custom Styles ───────────────────────────────────────────────────
st.markdown("""
<style>
    .progress-header {
        background: linear-gradient(135deg, #10B981, #059669);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-top: 4px solid #10B981;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
    }
    .stat-card h3 {
        margin: 0 0 0.5rem 0;
        color: #6B7280;
        font-size: 0.875rem;
        text-transform: uppercase;
    }
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #10B981;
    }
    .achievement-card {
        background: linear-gradient(135deg, #FBBF24, #F59E0B);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(245,158,11,0.3);
    }
    .achievement-card h4 {
        margin: 0 0 0.5rem 0;
        font-size: 1.5rem;
    }
    .exercise-summary {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #0066CC;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .goal-progress {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .progress-bar {
        width: 100%;
        height: 12px;
        background: #E5E7EB;
        border-radius: 6px;
        margin: 0.75rem 0;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #10B981, #059669);
        border-radius: 6px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# ── Authentication ──────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.link_button("Go to Login", "pages/0_Login.py", use_container_width=True, type="primary")
    st.stop()

patient_id = st.session_state.user["email"]
display_name = patient_id.split('@')[0]

# ── Load patient’s data ─────────────────────────────────────────────
session_manager = SessionManager()
all_sessions = session_manager.load_all_sessions()
patient_sessions = [s for s in all_sessions if s['patient_id'] == patient_id]

if not patient_sessions:
    st.markdown(f"""
    <div class="progress-header">
        <h1>Welcome, {display_name}! 👋</h1>
        <p>No sessions completed yet. Start your first exercise session!</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.link_button("🏃 Start Exercise Session", "pages/1_Patient.py", use_container_width=True, type="primary")
    with c2:
        st.link_button("🏠 Back to Home", "app.py", use_container_width=True)
    st.stop()

# Prepare DataFrame
df = pd.DataFrame(patient_sessions)
df['timestamp'] = pd.to_datetime(df['start_time'], unit='s')
df['date'] = df['timestamp'].dt.date
df['quality_pct'] = df['avg_form_quality'] * 100
df['duration_min'] = df['duration'] / 60

# ── Header ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class="progress-header">
    <h1>Great job, {display_name}! 🎉</h1>
    <p>Your physiotherapy exercise progress</p>
</div>
""", unsafe_allow_html=True)

# ── Quick Stats ─────────────────────────────────────────────────────
st.subheader("📊 Your Stats")
col1, col2, col3, col4 = st.columns(4)

total_sessions = len(df)
total_reps = int(df['reps'].sum())
avg_quality = df['quality_pct'].mean()
total_minutes = int(df['duration_min'].sum())

with col1:
    st.markdown(f'<div class="stat-card"><h3>Sessions</h3><div class="stat-value">{total_sessions}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-card"><h3>Total Reps</h3><div class="stat-value">{total_reps}</div></div>', unsafe_allow_html=True)
with col3:
    trend = "↑" if avg_quality >= 80 else "→" if avg_quality >= 60 else "↓"
    st.markdown(f'<div class="stat-card"><h3>Avg Form Quality</h3><div class="stat-value">{avg_quality:.0f}%</div><div class="stat-change">{trend} Quality</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="stat-card"><h3>Total Time</h3><div class="stat-value">{total_minutes}</div><div class="stat-change">⏱️ min</div></div>', unsafe_allow_html=True)

st.divider()

# ── Achievements ────────────────────────────────────────────────────
st.subheader("🏆 Your Achievements")
col1, col2, col3 = st.columns(3)

with col1:
    if total_sessions >= 1:
        st.markdown('<div class="achievement-card"><h4>🎯 First Session!</h4><p>Great start</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:#F3F4F6;padding:1.5rem;border-radius:10px;color:#9CA3AF;text-align:center;"><h4>🎯</h4><p>Complete 1 session</p></div>', unsafe_allow_html=True)

with col2:
    if total_sessions >= 5:
        st.markdown('<div class="achievement-card"><h4>⭐ 5 Sessions</h4><p>Consistency is key</p></div>', unsafe_allow_html=True)
    else:
        progress = min(100, (total_sessions / 5) * 100)
        st.markdown(f'<div style="background:#F3F4F6;padding:1.5rem;border-radius:10px;color:#9CA3AF;text-align:center;"><h4>⭐</h4><p>{total_sessions}/5 sessions ({progress:.0f}%)</p></div>', unsafe_allow_html=True)

with col3:
    if avg_quality >= 85:
        st.markdown('<div class="achievement-card"><h4>💎 Excellent Form</h4><p>Perfect execution!</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background:#F3F4F6;padding:1.5rem;border-radius:10px;color:#9CA3AF;text-align:center;"><h4>💎</h4><p>Reach 85% quality ({avg_quality:.0f}%)</p></div>', unsafe_allow_html=True)

st.divider()

# ── Charts ──────────────────────────────────────────────────────────
st.subheader("📈 Your Progress")
col1, col2 = st.columns(2)

with col1:
    reps_by_date = df.groupby('date')['reps'].sum().reset_index()
    fig1 = px.bar(reps_by_date, x='date', y='reps', title='Daily Rep Count', color='reps', color_continuous_scale='Greens')
    fig1.update_layout(height=350, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    quality_by_date = df.groupby('date')['quality_pct'].mean().reset_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=quality_by_date['date'], y=quality_by_date['quality_pct'],
                              mode='lines+markers', line=dict(color='#10B981', width=3),
                              marker=dict(size=10), fill='tozeroy', fillcolor='rgba(16,185,129,0.2)'))
    fig2.update_yaxes(range=[0, 100])
    fig2.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Exercise Breakdown ──────────────────────────────────────────────
st.subheader("💪 Exercise Breakdown")
exercise_summary = df.groupby('exercise').agg(
    total_reps=('reps', 'sum'),
    avg_reps=('reps', 'mean'),
    avg_quality=('quality_pct', 'mean'),
    sessions=('reps', 'count')
).reset_index().sort_values('sessions', ascending=False)

for _, row in exercise_summary.iterrows():
    st.markdown(f"""
    <div class="exercise-summary">
        <h4>{row['exercise']}</h4>
        <div style="display:flex; justify-content:space-between; padding:0.5rem 0;"><span>Sessions</span><strong>{int(row['sessions'])}</strong></div>
        <div style="display:flex; justify-content:space-between; padding:0.5rem 0;"><span>Total Reps</span><strong>{int(row['total_reps'])}</strong></div>
        <div style="display:flex; justify-content:space-between; padding:0.5rem 0;"><span>Avg Reps/Session</span><strong>{row['avg_reps']:.1f}</strong></div>
        <div style="display:flex; justify-content:space-between; padding:0.5rem 0;"><span>Form Quality</span><strong>{row['avg_quality']:.0f}%</strong></div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Goals ───────────────────────────────────────────────────────────
st.subheader("🎯 Your Goals")
col1, col2 = st.columns(2)

with col1:
    week_start = datetime.now().date() - timedelta(days=7)
    sessions_this_week = len(df[df['date'] >= week_start])
    weekly_progress = min(100, (sessions_this_week / 3) * 100)
    st.markdown(f"""
    <div class="goal-progress">
        <h4 style="color:#0066CC;">Weekly Sessions</h4>
        <p style="color:#6B7280;">Target: 3 sessions</p>
        <div class="progress-bar"><div class="progress-fill" style="width:{weekly_progress}%;"></div></div>
        <p style="text-align:center; color:#6B7280;">{sessions_this_week}/3 sessions ({weekly_progress:.0f}%)</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    quality_progress = min(100, avg_quality)
    st.markdown(f"""
    <div class="goal-progress">
        <h4 style="color:#0066CC;">Form Quality</h4>
        <p style="color:#6B7280;">Target: 85%</p>
        <div class="progress-bar"><div class="progress-fill" style="width:{quality_progress}%;"></div></div>
        <p style="text-align:center; color:#6B7280;">{avg_quality:.0f}% quality ({quality_progress:.0f}%)</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Session History ─────────────────────────────────────────────────
st.subheader("📋 Session History")
log = df[['timestamp', 'exercise', 'reps', 'quality_pct', 'duration_min']].copy()
log['date'] = log['timestamp'].dt.date
log['time'] = log['timestamp'].dt.strftime('%I:%M %p')
log['duration_min'] = log['duration_min'].round(1)
log['quality_pct'] = log['quality_pct'].round(1)
log = log.rename(columns={
    'exercise': 'Exercise',
    'reps': 'Reps',
    'quality_pct': 'Quality (%)',
    'duration_min': 'Duration (min)',
    'date': 'Date',
    'time': 'Time'
})
log = log[['Exercise', 'Reps', 'Quality (%)', 'Duration (min)', 'Date', 'Time']].sort_values('Date', ascending=False)
st.dataframe(log, use_container_width=True, hide_index=True)

st.divider()

# ── Navigation buttons ─────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    if st.button("🏃 Start New Session", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Patient.py")
with col2:
    if st.button("🏠 Back to Home", use_container_width=True):
        st.switch_page("app.py")
