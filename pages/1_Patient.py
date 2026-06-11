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

st.markdown("""
<style>
    .session-header { background: linear-gradient(135deg, #0066CC, #0084FF); padding: 2rem; border-radius: 10px; color: white; margin-bottom: 1.5rem; }
    .metric-card { background: white; padding: 1.5rem; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid #0066CC; margin-bottom: 1rem; }
    .metric-card h3 { margin: 0 0 0.5rem 0; color: #6B7280; font-size: 0.875rem; text-transform: uppercase; }
    .metric-card .value { font-size: 2.5rem; font-weight: 700; color: #0066CC; }
    .done-btn button { background: #059669 !important; border: none !important; font-size: 1.5rem !important; padding: 1.5rem 3rem !important; border-radius: 15px !important; }
    .done-btn button:hover { background: #047857 !important; }
    .confirm-box { background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 1.5rem; border-radius: 8px; margin: 1rem 0; }
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

# ── Main‑thread only session flags ─────────────────────────────────
if "pending_done" not in st.session_state:
    st.session_state.pending_done = False
if "session_ended" not in st.session_state:
    st.session_state.session_ended = False
# The following two are only updated via manual refresh (main thread)
if "display_sets" not in st.session_state:
    st.session_state.display_sets = 0
if "display_message" not in st.session_state:
    st.session_state.display_message = ""

# Reset session start time if not already set
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()

# If session already ended, show success screen
if st.session_state.session_ended:
    st.success("🎉 Your exercise session has been saved.")
    st.info("The camera has been stopped. You can start a new session below.")
    if st.button("🔄 Start New Session", use_container_width=True, type="primary"):
        for key in ["pending_done", "session_ended", "display_sets", "display_message", "session_start_time"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    st.stop()

# Header
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

# ── Video Processor (all state changes inside lock, NO st.session_state writes) ─
class PhysioVideoProcessor(VideoProcessorBase):
    def __init__(self, session_mgr, pat_id):
        self.pose = pose_estimator
        self.analyzer = analyzer
        self.lock = threading.Lock()
        self.rep_state = {}
        self.rep_count = 0
        self.form_quality_history = []
        self.exercise = None
        self.feedback_text = ""
        self.last_set_rep_count = 0
        # Auto‑save tracking (thread‑safe)
        self.sets_completed = 0
        self.auto_save_message = ""
        self.session_manager = session_mgr
        self.patient_id = pat_id

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
                    quality = self.analyzer.get_rep_quality(feedback, self.rep_state)

                    if rep_done:
                        self.rep_count += 1
                        self.form_quality_history.append(quality)

                    # Draw skeleton & feedback on the frame
                    img = self.pose.draw_skeleton(img, keypoints, color_guide)
                    img = self.analyzer.draw_feedback(img, feedback, self.rep_count, self.exercise)

                    # ---- AUTO‑SET DETECTION (inside lock, no st.session_state) ----
                    new_reps_since_save = self.rep_count - self.last_set_rep_count
                    if new_reps_since_save >= 10:
                        # Calculate average quality of the last 10 reps
                        last_10 = self.form_quality_history[-10:]
                        avg_q = np.mean(last_10) if last_10 else 1.0
                        # Save to Supabase directly (no callback)
                        self.session_manager.save_session(
                            patient_id=self.patient_id,
                            exercise=self.exercise,
                            reps=10,
                            avg_form_quality=avg_q,
                            duration=0
                        )
                        self.sets_completed += 1
                        self.auto_save_message = f"✅ Set {self.sets_completed} auto‑saved!"
                        self.last_set_rep_count = self.rep_count
                else:
                    img = self.pose.draw_text(img, "Position yourself in frame", (50, 50))

            return av.VideoFrame.from_ndarray(img, format="bgr24")
        except Exception:
            return frame

# Create the streamer (processor factory now receives session_manager and patient_id)
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
    video_processor_factory=lambda: PhysioVideoProcessor(session_manager, patient_id),
    async_processing=True,
)

# ═══ DONE BUTTON & CONFIRMATION (main thread only) ═══
st.markdown("<br>", unsafe_allow_html=True)

if not st.session_state.pending_done:
    if st.button("✅  DONE  –  Finish Exercise", use_container_width=True, key="done_btn"):
        st.session_state.pending_done = True
        st.rerun()
else:
    st.markdown('<div class="confirm-box">', unsafe_allow_html=True)
    st.warning("⚠️ Are you sure you want to end the session? All unsaved reps will be saved.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Yes, End Session", use_container_width=True, type="primary"):
            if webrtc_ctx.video_processor:
                processor = webrtc_ctx.video_processor
                with processor.lock:
                    # Save any remaining reps (<10) as a final partial set
                    remaining = processor.rep_count - processor.last_set_rep_count
                    if remaining > 0:
                        rem_qual = processor.form_quality_history[-remaining:] if processor.form_quality_history else []
                        avg_q = np.mean(rem_qual) if rem_qual else 1.0
                        processor.session_manager.save_session(
                            patient_id=patient_id,
                            exercise=processor.exercise or exercise_choice,
                            reps=remaining,
                            avg_form_quality=avg_q,
                            duration=0
                        )
                # No final total record – only sets & partial are saved
            st.session_state.session_ended = True
            st.session_state.pending_done = False
            st.rerun()
    with c2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.pending_done = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Live stats (manual refresh – reads from processor) ────────────
st.divider()
st.subheader("📊 Current Stats")
if st.button("🔄 Refresh Stats", use_container_width=True):
    # Pull latest values from the processor (thread‑safe)
    if webrtc_ctx.video_processor:
        proc = webrtc_ctx.video_processor
        with proc.lock:
            st.session_state.display_rep_count = proc.rep_count
            st.session_state.display_sets = proc.sets_completed
            st.session_state.display_quality = (
                np.mean(proc.form_quality_history) * 100 if proc.form_quality_history else 0.0
            )
            st.session_state.display_exercise = proc.exercise or exercise_choice
            st.session_state.display_message = proc.auto_save_message
            # Clear the processor's message after reading (so it doesn't persist)
            proc.auto_save_message = ""

# Retrieve values to display (use defaults if not yet refreshed)
rep_count = st.session_state.get("display_rep_count", 0)
sets = st.session_state.get("display_sets", 0)
avg_quality = st.session_state.get("display_quality", 0.0)
ex = st.session_state.get("display_exercise", exercise_choice)
message = st.session_state.get("display_message", "")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><h3>Reps</h3><div class="value">{rep_count}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><h3>Sets</h3><div class="value">{sets}</div></div>', unsafe_allow_html=True)
with col3:
    ind = "🟢 Excellent" if avg_quality >= 85 else "🟡 Good" if avg_quality >= 70 else "🔴 Needs Work"
    st.markdown(f'<div class="metric-card"><h3>Form Quality</h3><div class="value">{avg_quality:.0f}%</div><div>{ind}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><h3>Exercise</h3><div class="value" style="font-size:1.4rem;">{ex}</div></div>', unsafe_allow_html=True)

if message:
    st.success(message)

# ── Cancel session (double‑tap safety) ─────────────────────────────
st.divider()
if st.button("❌ Cancel Session", use_container_width=True):
    if st.session_state.get("pending_cancel", False):
        for key in ["pending_done", "session_ended", "display_sets", "display_message", "display_rep_count",
                    "display_quality", "display_exercise", "session_start_time", "pending_cancel"]:
            if key in st.session_state:
                del st.session_state[key]
        st.info("Session cancelled. No data was saved.")
        st.switch_page("app.py")
    else:
        st.session_state.pending_cancel = True
        st.warning("⚠️ Press again to confirm cancellation.")
        st.rerun()
else:
    if st.session_state.get("pending_cancel"):
        st.session_state.pending_cancel = False
