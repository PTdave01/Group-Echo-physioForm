import streamlit as st
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode, RTCConfiguration
import numpy as np
import time
import threading
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.pose_estimator import PoseEstimator
from utils.exercise_analyzer import ExerciseAnalyzer
from utils.session_manager import SessionManager

st.set_page_config(page_title="Patient – PhysioForm", layout="wide")

# ── Styling (kept from your design) ───────────────────────────────
st.markdown("""
<style>
    .session-header {
        background: linear-gradient(135deg, #0066CC 0%, #0084FF 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-top: 4px solid #0066CC;
    }
    .metric-card h3 {
        margin: 0 0 0.5rem 0;
        color: #6B7280;
        font-size: 0.875rem;
        text-transform: uppercase;
    }
    .metric-card .value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0066CC;
    }
    .feedback-good {
        background: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .feedback-warning {
        background: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧑‍⚕️ Patient Exercise Session")

# ── Login check ───────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    if st.button("Go to Login", use_container_width=True, type="primary"):
        st.switch_page("pages/0_Login.py")
    st.stop()

# Initialise session variables
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()
if "rep_count" not in st.session_state:
    st.session_state.rep_count = 0
if "form_quality_history" not in st.session_state:
    st.session_state.form_quality_history = []
if "recognized_exercise" not in st.session_state:
    st.session_state.recognized_exercise = None

patient_id = st.session_state.user["email"]

st.markdown(f"""
<div class="session-header">
    <h1>🏋️ Exercise Session in Progress</h1>
    <p>Patient: <strong>{patient_id}</strong></p>
</div>
""", unsafe_allow_html=True)

# Exercise selection – only two exercises
exercise_choice = st.selectbox("Choose your exercise", ["Biceps Curl", "Squat"])

# Initialise utilities
pose_estimator = PoseEstimator()
analyzer = ExerciseAnalyzer()
session_manager = SessionManager()

# ── Video Processor ───────────────────────────────────────────────
class PhysioVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.pose = pose_estimator
        self.analyzer = analyzer
        self.lock = threading.Lock()
        self.rep_state = {}
        self.rep_count = 0
        self.form_quality_history = []
        self.exercise = None
        self.feedback_text = ""
        self.current_form_quality = 1.0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        try:
            img = frame.to_ndarray(format="bgr24")
            keypoints, _ = self.pose.get_keypoints(img)

            with self.lock:
                self.exercise = exercise_choice

                if self.exercise and keypoints is not None:
                    feedback, color_guide, rep_done = self.analyzer.evaluate_form(
                        self.exercise, keypoints, self.rep_state
                    )
                    self.feedback_text = feedback
                    self.current_form_quality = self.analyzer.get_rep_quality(feedback)

                    if rep_done:
                        self.rep_count += 1
                        self.form_quality_history.append(self.current_form_quality)

                    # Draw skeleton and feedback
                    img = self.pose.draw_skeleton(img, keypoints, color_guide)
                    img = self.analyzer.draw_feedback(
                        img, feedback, self.rep_count, self.exercise
                    )
                else:
                    img = self.pose.draw_text(img, "Position yourself in frame", (50, 50))

            return av.VideoFrame.from_ndarray(img, format="bgr24")

        except Exception:
            # If any frame crashes, skip it
            return frame

# ── WebRTC Configuration – extra TURN servers for mobile networks ──
webrtc_ctx = webrtc_streamer(
    key="physio-camera",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTCConfiguration(
        {"iceServers": [
            # Google STUN
            {"urls": ["stun:stun.l.google.com:19302"]},
            # freestun.net (TCP & UDP)
            {"urls": ["turn:freestun.net:3478?transport=tcp"],
             "username": "free", "credential": "free"},
            {"urls": ["turn:freestun.net:3478?transport=udp"],
             "username": "free", "credential": "free"},
            # Metered.ca TURN (TCP on 443, passes most firewalls)
            {"urls": ["turn:openrelay.metered.ca:443?transport=tcp"],
             "username": "openrelayproject",
             "credential": "openrelayproject"},
            # Twilio TURN (global, UDP only – needs credentials)
            {"urls": ["turn:global.turn.twilio.com:3478?transport=udp"],
             "username": "f4b4035eaa76f4a55de5f4351567653ee73a4e2b6bc7b6a5b8f5c5f5f5f5f5f5",
             "credential": "f4b4035eaa76f4a55de5f4351567653ee73a4e2b6bc7b6a5b8f5c5f5f5f5f5f5"}
        ]}
    ),
    media_stream_constraints={
        "video": {"width": 480, "height": 360, "frameRate": 15},
        "audio": False
    },
    video_processor_factory=PhysioVideoProcessor,
    async_processing=True,
)

st.divider()

# ── Live metrics (manual refresh – no fragment) ──────────────────
refresh_col, _ = st.columns([1, 3])
with refresh_col:
    if st.button("🔄 Refresh Stats", use_container_width=True):
        # Pull data from processor (if available)
        if webrtc_ctx.video_processor:
            with webrtc_ctx.video_processor.lock:
                st.session_state.rep_count = webrtc_ctx.video_processor.rep_count
                st.session_state.form_quality_history = list(
                    webrtc_ctx.video_processor.form_quality_history
                )
                st.session_state.recognized_exercise = webrtc_ctx.video_processor.exercise

# Display metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Reps Completed</h3>
        <div class="value">{st.session_state.rep_count}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if st.session_state.form_quality_history:
        avg_quality = np.mean(st.session_state.form_quality_history) * 100
        indicator = "🟢 Excellent" if avg_quality >= 85 else "🟡 Good" if avg_quality >= 70 else "🔴 Needs Work"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Form Quality</h3>
            <div class="value">{avg_quality:.0f}%</div>
            <div style="font-size:0.9rem;">{indicator}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <h3>Form Quality</h3>
            <div class="value">-</div>
        </div>
        """, unsafe_allow_html=True)

with col3:
    ex = st.session_state.recognized_exercise or exercise_choice
    st.markdown(f"""
    <div class="metric-card">
        <h3>Exercise</h3>
        <div class="value" style="font-size:1.3rem;">{ex}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Session controls ──────────────────────────────────────────────
st.divider()
col1, col2 = st.columns(2)

with col1:
    if st.button("⏹️ End Session & Save", use_container_width=True, type="primary"):
        if webrtc_ctx.video_processor:
            processor = webrtc_ctx.video_processor
            avg_quality = np.mean(processor.form_quality_history) if processor.form_quality_history else 0.0
            saved_exercise = processor.exercise or exercise_choice
            duration = time.time() - st.session_state.session_start_time

            session_manager.save_session(
                patient_id=patient_id,
                exercise=saved_exercise,
                reps=processor.rep_count,
                avg_form_quality=avg_quality,
                duration=duration
            )
            st.success("Session saved! Clinician can now view your progress.")
            # Reset state
            st.session_state.rep_count = 0
            st.session_state.form_quality_history = []
            st.session_state.recognized_exercise = None
            st.session_state.session_start_time = time.time()

with col2:
    if st.button("❌ Cancel Session", use_container_width=True):
        st.session_state.rep_count = 0
        st.session_state.form_quality_history = []
        st.session_state.recognized_exercise = None
        st.info("Session cancelled. No data was saved.")
