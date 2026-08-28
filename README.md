# PhysioForm – AI-Powered Home Physiotherapy

Real‑time exercise tracking using **YOLOv8 pose estimation** (COCO keypoints) and **Streamlit**.  
Designed for patients and clinicians to monitor biceps curls and squats from any smartphone browser.

## 📸 What It Does
- **Live webcam / camera processing** – works with both WebRTC streaming (Wi‑Fi) and simple photo‑based mode (mobile data).
- **Auto‑detection** of Biceps Curls and Squats (or manual selection).
- **Rep counting** with real‑time form correction (shoulder stability, knee tracking, back angle).
- **Colour‑coded skeleton overlay** – green for correct, yellow for marginal, red for error.
- **Clinician dashboard** – view all patient sessions, average form quality, reps, and adherence trends.

## 🚀 Live App
Access the app directly from your phone’s browser:  
'https://ptdave-physioform-ez35tc4j6tcjuqsppglqfc.streamlit.app'

## ⚙️ How to Use (Patient)
1. Open the app and tap **Patient – Start Exercise** (live stream) or **Patient (Simple)** (photo mode).
2. Enter your Patient ID (e.g., “patient_001”).
3. Choose an exercise or leave on **Auto‑detect**.
4. Allow camera access and position yourself so your full body is visible.
5. Start moving – the skeleton appears, angles are shown, and reps count automatically.
6. When finished, tap **End Session & Save** – your data is stored for the clinician.

## 🧑‍⚕️ Clinician Dashboard
1. From the home page, tap **Clinician – View Dashboard**.
2. View all sessions, filter by patient, see charts of form quality over time.

## 🧰 Tech Stack
- **YOLOv8n‑pose** (Ultralytics) – real‑time 17‑keypoint COCO skeleton
- **OpenCV** – angle calculation, drawing overlays
- **Streamlit** + **streamlit‑webrtc** – frontend and WebRTC integration
- **NumPy, Pandas** – data processing
- **JSON** – lightweight file‑based session storage

## 🖥️ Running Locally (for developers)
1. Clone the repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/physioform.git
   cd physioform
```

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run app.py
   ```
3. Open http://localhost:8501 in your browser.

📁 Project Structure

```
physioform/
├── app.py                  # Home page
├── pages/
│   ├── 1_Patient.py        # Live WebRTC exercise session
│   ├── 1_Patient_Simple.py # Photo‑based fallback for mobile data
│   └── 2_Clinician.py      # Clinician dashboard
├── utils/
│   ├── __init__.py
│   ├── pose_estimator.py   # YOLO pose model loader & skeleton drawing
│   ├── exercise_analyzer.py # Angle, rep, form logic
│   └── session_manager.py  # JSON session storage
├── requirements.txt
├── packages.txt            # System dependencies for Streamlit Cloud
└── README.md
```
# PhysioForm - Agentic Workflows

## Problem: Who has this problem?
Home physio patients do exercises wrong, physios have no objective data.

## Baseline
Simple angle check: GOOD/BAD only. Result: 4/6 correct, no explanation.

## Agentic Workflow
1. Recognizer Agent - identifies squat vs curl
2. Form Analyst Agent - measures angles + symmetry + faults
3. Coach Agent - translates faults to human cue
4. Tracker Agent - generates clinician report

## Improvement Changelog
- **Baseline:** 4/6 accuracy, no why.
- **Iteration 1:** Added Recognizer. Why: Baseline confused exercises. Evidence: 6/6 exercise ID now. Kept.
- **Iteration 2:** Added symmetry check for knees_caving_in. Why: Baseline called caving GOOD. Evidence: Now flags fault. Kept.
- **Iteration 3:** Added Coach. Why: JSON not patient friendly. Evidence: User comprehension 90%. Kept.
- **Iteration 4:** Tried tempo detection - failed due to MediaPipe jitter. Removed. Documented as failure mode.

## Final Eval (same 6 videos)
Baseline: 4/6, no explanation, 5min therapist review
Final: 6/6, explains why, 20sec review, ~$0.02/session

## How to reproduce
pip install -r requirements.txt
python baseline/simple_angle_check.py test_videos/squat_good.mp4
python agents/orchestrator.py test_videos/squat_mistake.mp4
