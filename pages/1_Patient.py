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

# Custom CSS for better styling
st.markdown("""
<style>
    .session-header {
        background: linear-gradient(135deg, #0066CC 0%, #0084FF 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .session-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .session-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
    }
    .rep-counter {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        font-size: 3rem;
        font-weight: 700;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
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
        letter-spacing: 0.5px;
    }
    .metric-card .value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0066CC;
    }
    .metric-card .subtext {
        font-size: 0.875rem;
        color: #6B7280;
        margin-top: 0.5rem;
    }
    .feedback-good {
        background: #D1FAE5;
        border-left: 4px solid #10B981;
        color: #065F46;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .feedback-warning {
        background: #FEF3C7;
        border-left: 4px solid #F59E0B;
        color: #92400E;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .feedback-bad {
        background: #FEE2E2;
        border-left: 4px solid #EF4444;
        color: #7F1D1D;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }
    .form-quality-bar {
        width: 100%;
        height: 10px;
        background: #E5E7EB;
        border-radius: 5px;
        margin: 0.75rem 0;
        overflow: hidden;
    }
    .form-quality-fill {
        height: 100%;
        background: linear-gradient(90deg, #10B981 0%, #059669 100%);
        border-radius: 5px;
        transition: width 0.3s ease;
    }
    .instruction-box {
        background: #DBEAFE;
        border-left: 4px solid #0066CC;
        color: #0C4A6E;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .session-summary {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .session-summary h3 {
        margin-top: 0;
        color: #10B981;
    }
    .summary-item {
        display: flex;
        justify-content: space-between;
        padding: 0.75rem 0;
        border-bottom: 1px solid #E5E7EB;
    }
    .summary-item:last-child {
        border-bottom: none;
    }
    .summary-item-label {
        color: #6B7280;
        font-weight: 500;
    }
    .summary-item-value {
        color: #0066CC;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧑‍⚕️ Patient Exercise Session (Live Stream)")

# ── Login check ─────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please log in first.")
    st.link_button("Go to Login", "pages/0_Login.py", use_container_width=True, type="primary")
    st.stop()

# Initialize session variables
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = time.time()
if "recognized_exercise" not in st.session_state:
    st.session_state.recognized_exercise = None
if "rep_count" not in st.session_state:
    st.session_state.rep_count = 0
if "form_quality_history" not in st.session_state:
    st.session_state.form_quality_history = []
if "session_saved" not in st.session_state:
    st.session_state.session_saved = False

patient_id = st.session_state.user["email"]

# User info banner
st.markdown(f"""
<div class="session-header">
    <h1>🏋️ Exercise Session in Progress</h1>
    <p>Patient: <strong>{patient_id}</strong></p>
</div>
""", unsafe_allow_html=True)

# Exercise selection
col1, col2 = st.columns([3, 1])
with col1:
    exercise_choice = st.selectbox(
        "Choose your exercise (or auto-detect)",
        ["Auto-detect", "Biceps Curl", "Squat", "Shoulder Press", "Leg Raise"],
        key="exercise_select"
    )
with col2:
    show_instructions = st.toggle("📋 Show Instructions", key="show_instructions")

# Show instructions if toggled
if show_instructions:
    st.markdown(f"""
    <div class="instruction-box">
        <strong>📋 {exercise_choice} - Proper Form Guide</strong><br>
        <br>
        Follow the visual guidance on the camera feed. The AI will detect your movement and provide real-time feedback on your form quality. Try to maintain proper posture throughout the exercise.
    </div>
    """, unsafe_allow_html=True)

# Initialize utilities
pose_estimator = PoseEstimator()
analyzer = ExerciseAnalyzer()
session_manager = SessionManager()

# Video Processor Class
class PhysioVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.pose = pose_estimator
        self.analyzer = analyzer
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.rep_state = {}
        self.rep_count = 0
        self.form_quality_history = []
        self.exercise = None
        self.feedback_text = ""
        self.angle_buffer = []
        self.current_form_quality = 0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        try:
            img = frame.to_ndarray(format="bgr24")
            keypoints, bbox = self.pose.get_keypoints(img)

            with self.lock:
                # Determine exercise
                if exercise_choice == "Auto-detect":
                    if self.exercise is None:
                        if len(self.angle_buffer) < 60:
                            if keypoints is not None:
                                angles = self.analyzer.calc_all_angles(keypoints)
                                self.angle_buffer.append(angles)
                        else:
                            self.exercise = self.analyzer.recognize_exercise(self.angle_buffer)
                            st.session_state.recognized_exercise = self.exercise
                            self.angle_buffer.clear()
                else:
                    self.exercise = exercise_choice
                    st.session_state.recognized_exercise = exercise_choice

                # Process form
                if self.exercise and keypoints is not None:
                    feedback, color_guide, rep_done = self.analyzer.evaluate_form(
                        self.exercise, keypoints, self.rep_state
                    )
                    self.feedback_text = feedback
                    self.current_form_quality = self.analyzer.get_rep_quality(feedback)
                    
                    if rep_done:
                        self.rep_count += 1
                        self.form_quality_history.append(self.current_form_quality)
                        st.session_state.rep_count = self.rep_count
                        st.session_state.form_quality_history = self.form_quality_history
                    
                    img = self.pose.draw_skeleton(img, keypoints, color_guide)
                    img = self.analyzer.draw_feedback(img, self.feedback_text, self.rep_count, self.exercise)
                else:
                    img = self.pose.draw_text(img, "Position yourself in frame", (50, 50))
                    if self.exercise is None and exercise_choice == "Auto-detect":
                        img = self.pose.draw_text(img, "Auto-detecting exercise...", (50, 90))

            return av.VideoFrame.from_ndarray(img, format="bgr24")
        except Exception as e:
            img = frame.to_ndarray(format="bgr24")
            img = self.pose.draw_text(img, f"Error: {str(e)[:50]}", (50, 50))
            return av.VideoFrame.from_ndarray(img, format="bgr24")

# WebRTC configuration
webrtc_ctx = webrtc_streamer(
    key="physio-camera",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTCConfiguration(
        {"iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["turn:freestun.net:3478"], "username": "free", "credential": "free"},
            {"urls": ["turn:openrelay.metered.ca:443?transport=tcp"],
             "username": "openrelayproject", "credential": "openrelayproject"},
        ]}
    ),
    media_stream_constraints={
        "video": {"width": 640, "height": 480, "frameRate": 20},
        "audio": False
    },
    video_processor_factory=PhysioVideoProcessor,
    async_processing=True,
)

st.divider()

# Main metrics display
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
        quality_indicator = "🟢 Excellent" if avg_quality >= 85 else "🟡 Good" if avg_quality >= 70 else "🔴 Needs Work"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Form Quality</h3>
            <div class="value">{avg_quality:.0f}%</div>
            <div class="subtext">{quality_indicator}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <h3>Form Quality</h3>
            <div class="value">-</div>
            <div class="subtext">No data yet</div>
        </div>
        """, unsafe_allow_html=True)

with col3:
    if st.session_state.recognized_exercise:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Exercise</h3>
            <div class="value" style="font-size: 1.3rem;">{st.session_state.recognized_exercise}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <h3>Exercise</h3>
            <div class="value" style="font-size: 1.2rem;">Detecting...</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Session duration
session_duration = int((time.time() - st.session_state.session_start_time) / 60)
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"**Session Duration:** {session_duration} minutes")
with col2:
    if st.button("⟲ Reset Session", key="reset_btn"):
        st.session_state.rep_count = 0
        st.session_state.recognized_exercise = None
        st.session_state.form_quality_history = []
        st.session_state.session_start_time = time.time()
        st.rerun()

st.divider()

# Session controls
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("⏹️ End Session & Save", use_container_width=True, type="primary", key="end_session_btn"):
        if webrtc_ctx.video_processor:
            processor = webrtc_ctx.video_processor
            avg_quality = np.mean(processor.form_quality_history) if processor.form_quality_history else 0.0
            saved_exercise = processor.exercise or st.session_state.recognized_exercise or "unknown"
            session_duration = time.time() - st.session_state.session_start_time
            
            # Session summary
            st.markdown("""
            <div class="session-summary">
                <h3>✅ Session Completed!</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                    <div class="summary-item">
                        <span class="summary-item-label">Exercise</span>
                        <span class="summary-item-value">{saved_exercise}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-item-label">Reps Completed</span>
                        <span class="summary-item-value">{processor.rep_count}</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-item-label">Duration</span>
                        <span class="summary-item-value">{int(session_duration / 60)} min</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_s2:
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                    <div style="text-align: center;">
                        <h4 style="margin: 0 0 0.5rem 0; color: #0066CC;">Form Quality</h4>
                        <div style="font-size: 2rem; font-weight: 700; color: #10B981;">{avg_quality*100:.1f}%</div>
                        <div style="margin-top: 0.5rem; color: #6B7280; font-size: 0.875rem;">
                            {'🟢 Excellent' if avg_quality >= 0.85 else '🟡 Good' if avg_quality >= 0.70 else '🔴 Keep improving'}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.success("📊 Your clinician will review this session shortly.")
            
            # Save to database
            session_manager.save_session(
                patient_id=patient_id,
                exercise=saved_exercise,
                reps=processor.rep_count,
                avg_form_quality=avg_quality,
                duration=session_duration
            )
            
            st.session_state.rep_count = 0
            st.session_state.recognized_exercise = None
            st.session_state.form_quality_history = []
            st.session_state.session_saved = True
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏠 Back to Home", use_container_width=True):
                    st.switch_page("app.py")
            with col2:
                if st.button("🔄 Start New Session", use_container_width=True):
                    st.session_state.session_start_time = time.time()
                    st.session_state.session_saved = False
                    st.rerun()

with col2:
    if st.button("❌ Cancel Session", use_container_width=True):
        if st.session_state.session_saved == False:
            st.session_state.rep_count = 0
            st.session_state.recognized_exercise = None
            st.session_state.form_quality_history = []
            st.info("Session cancelled. No data was saved.")
            if st.button("↩️ Go Back", use_container_width=True):
                st.switch_page("app.py")
