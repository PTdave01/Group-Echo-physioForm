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

# ── Styling ────────────────────────────────────────────────────────
st.markdown("""
<style>
    .session-header { background: linear-gradient(135deg, #0066CC, #0084FF); padding: 2rem; border-radius: 10px; color: white; margin-bottom: 1.5rem; }
    .metric-card { background: white; padding: 1.5rem; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid #0066CC; margin-bottom: 1rem; }
    .metric-card h3 { margin: 0 0 0.5rem 0; color: #6B7280; font-size: 0.875rem; text-transform: uppercase; }
    .metric-card .value { font-size: 2.5rem; font-weight: 700; color: #0066CC; }
    .done-btn button { background: #059669 !important; border: none !important; font-size: 1.5rem !important; padding: 1.5rem 3rem !important; border-radius: 15px !important; transition: 0.2s; }
    .done-btn button:hover { background: #047857 !important; transform: scale(1.02); }
</style>
""", unsafe_allow_html=True)

st.title("🧑‍⚕️ Patient Exercise Session")

# ── Login check ───────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    if st.button("Go to Login", use_container_width=True, type="primary"):
        st.switch_page("pages/0_Login.py")
    st.stop()

patient_id = st.session_state.user["email"]

# ── Initialise persistent session variables ────────────────────────
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()
if "sets_completed" not in st.session_state:
    st.session_state.sets_completed = 0
if "last_auto_set_rep" not in st.session_state:
    st.session_state.last_auto_set_rep = 0
if "auto_save_message" not in st.session_state:
    st.session_state.auto_save_message = ""

st.markdown(f"""
<div class="session-header">
    <h1>🏋️ Exercise Session in Progress</h1>
    <p>Patient: <strong>{patient_id}</strong></p>
</div>
""", unsafe_allow_html=True)

exercise_choice = st.selectbox("Choose your exercise", ["Biceps Curl", "Squat"])

# ── Utils ─────────────────────────────────────────────────────────
pose_estimator = PoseEstimator()
analyzer = ExerciseAnalyzer()
session_manager = SessionManager()

# ── Auto‑set callback (runs in processor thread) ─────────────────
def on_set_completed(set_exercise, set_reps, avg_quality):
    """Called every 10 reps. Saves a set immediately."""
    session_manager.save_session(
        patient_id=patient_id,
        exercise=set_exercise,
        reps=set_reps,
        avg_form_quality=avg_quality,
        duration=0
    )
    st.session_state.sets_completed += 1
    st.session_state.last_auto_set_rep += set_reps
    st.session_state.auto_save_message = f"✅ Set {st.session_state.sets_completed} auto‑saved!"

# ── Video Processor ────────────────────────────────────────────────
class PhysioVideoProcessor(VideoProcessorBase):
    def __init__(self, on_set_callback):
        self.pose = pose_estimator
        self.analyzer = analyzer
        self.lock = threading.Lock()
        self.rep_state = {}
        self.rep_count = 0
        self.form_quality_history = []
        self.exercise = None
        self.feedback_text = ""
        self.on_set_callback = on_set_callback
        self.last_set_rep_count = 0

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
                    quality = self.analyzer.get_rep_quality(feedback)

                    if rep_done:
                        self.rep_count += 1
                        self.form_quality_history.append(quality)

                    # Draw skeleton & feedback on the video frame
                    img = self.pose.draw_skeleton(img, keypoints, color_guide)
                    img = self.analyzer.draw_feedback(img, feedback, self.rep_count, self.exercise)

                    # Auto‑set detection (every 10 new reps)
                    new_reps_since_save = self.rep_count - self.last_set_rep_count
                    if new_reps_since_save >= 10:
                        last_10_qualities = self.form_quality_history[-10:]
                        avg_q = np.mean(last_10_qualities) if last_10_qualities else 1.0
                        if self.on_set_callback:
                            self.on_set_callback(self.exercise, 10, avg_q)
                        self.last_set_rep_count = self.rep_count
                else:
                    img = self.pose.draw_text(img, "Position yourself in frame", (50, 50))

            return av.VideoFrame.from_ndarray(img, format="bgr24")
        except Exception:
            return frame

# ── WebRTC streamer ────────────────────────────────────────────────
webrtc_ctx = webrtc_streamer(
    key="physio-camera",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTCConfiguration(
        {"iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["turn:freestun.net:3478?transport=tcp"], "username": "free", "credential": "free"},
            {"urls": ["turn:freestun.net:3478?transport=udp"], "username": "free", "credential": "free"},
            {"urls": ["turn:openrelay.metered.ca:443?transport=tcp"], "username": "openrelayproject", "credential": "openrelayproject"},
            {"urls": ["turn:global.turn.twilio.com:3478?transport=udp"],
             "username": "f4b4035eaa76f4a55de5f4351567653ee73a4e2b6bc7b6a5b8f5c5f5f5f5f5f5",
             "credential": "f4b4035eaa76f4a55de5f4351567653ee73a4e2b6bc7b6a5b8f5c5f5f5f5f5f5"}
        ]}
    ),
    media_stream_constraints={"video": {"width": 480, "height": 360, "frameRate": 15}, "audio": False},
    video_processor_factory=lambda: PhysioVideoProcessor(on_set_callback=on_set_completed),
    async_processing=True,
)

# ═══ BIG "DONE" BUTTON – right below the video ═══
st.markdown("<br>", unsafe_allow_html=True)
if st.button("✅  DONE  –  Finish Exercise", use_container_width=True, key="done_btn"):
    if webrtc_ctx.video_processor:
        processor = webrtc_ctx.video_processor
        with processor.lock:
            # Save any remaining reps as a final (possibly incomplete) set
            remaining = processor.rep_count - processor.last_set_rep_count
            if remaining > 0:
                remaining_qualities = processor.form_quality_history[-remaining:] if processor.form_quality_history else []
                avg_q = np.mean(remaining_qualities) if remaining_qualities else 1.0
                session_manager.save_session(
                    patient_id=patient_id,
                    exercise=processor.exercise or exercise_choice,
                    reps=remaining,
                    avg_form_quality=avg_q,
                    duration=0
                )
            total_reps = processor.rep_count
            avg_all = np.mean(processor.form_quality_history) if processor.form_quality_history else 0.0
        # Final session summary
        session_manager.save_session(
            patient_id=patient_id,
            exercise=exercise_choice,
            reps=total_reps,
            avg_form_quality=avg_all,
            duration=time.time() - st.session_state.session_start_time
        )
        st.success("🎉 Session saved! Your clinician can now review your progress.")
        # Clean up session state
        for key in ["sets_completed", "last_auto_set_rep", "auto_save_message", "session_start_time"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

st.caption("Press **DONE** when you finish your exercise, even if you haven’t completed a full set of 10 reps.")

# ── Manual Refresh Stats button ────────────────────────────────────
st.divider()
st.subheader("📊 Current Session Stats (tap to refresh)")

col_refresh, _ = st.columns([1, 3])
with col_refresh:
    refresh_clicked = st.button("🔄 Refresh Stats", use_container_width=True)

# Gather stats from processor (if available)
rep_count = 0
avg_quality = 0.0
sets = st.session_state.get("sets_completed", 0)
exercise = exercise_choice

if webrtc_ctx.video_processor:
    processor = webrtc_ctx.video_processor
    with processor.lock:
        rep_count = processor.rep_count
        if processor.form_quality_history:
            avg_quality = np.mean(processor.form_quality_history) * 100
        exercise = processor.exercise or exercise_choice

# Display the four metric cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Reps</h3>
        <div class="value">{rep_count}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Sets</h3>
        <div class="value">{sets}</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    indicator = "🟢 Excellent" if avg_quality >= 85 else "🟡 Good" if avg_quality >= 70 else "🔴 Needs Work"
    st.markdown(f"""
    <div class="metric-card">
        <h3>Form Quality</h3>
        <div class="value">{avg_quality:.0f}%</div>
        <div style="font-size:0.9rem;">{indicator}</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Exercise</h3>
        <div class="value" style="font-size:1.4rem;">{exercise}</div>
    </div>
    """, unsafe_allow_html=True)

# Show auto‑save message if any
if st.session_state.auto_save_message:
    st.success(st.session_state.auto_save_message)
    st.session_state.auto_save_message = ""

# ── Cancel session ─────────────────────────────────────────────────
st.divider()
if st.button("❌ Cancel Session", use_container_width=True):
    for key in ["sets_completed", "last_auto_set_rep", "auto_save_message", "session_start_time"]:
        if key in st.session_state:
            del st.session_state[key]
    st.info("Session cancelled. No data was saved.")
    st.switch_page("app.py")
