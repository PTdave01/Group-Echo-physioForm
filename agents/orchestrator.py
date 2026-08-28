import cv2
import mediapipe as mp
import sys
import json
import os
from recognizer import recognize_exercise
from form_analyst import analyze_form
from coach import coach
from tracker import generate_report

mp_pose = mp.solutions.pose

def run_agentic(video_path):
    cap = cv2.VideoCapture(video_path)
    session = []
    with mp_pose.Pose() as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = pose.process(rgb)
            if res.pose_landmarks:
                lm = res.pose_landmarks.landmark
                rec = recognize_exercise(lm)
                analysis = analyze_form(lm, rec['exercise'])
                analysis['cue'] = coach(analysis['faults'])
                analysis['recognized'] = rec
                session.append(analysis)
                if len(session) > 120:
                    break
    cap.release()
    report = generate_report(session)
    os.makedirs("trajectories", exist_ok=True)
    with open("trajectories/session_log.json", "w") as f:
        json.dump({"frames": session[:20], "report": report}, f, indent=2)
    print(report['clinician_summary'])
    return report

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "test_videos/squat_good.mp4"
    run_agentic(path)
