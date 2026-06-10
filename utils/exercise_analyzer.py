import numpy as np
import cv2

class ExerciseAnalyzer:
“””
Analyzes exercise form using pose keypoints.
Supports: Biceps Curl, Squat
“””

```
KP = {
    "left_shoulder": 5, "right_shoulder": 6,
    "left_elbow": 7, "right_elbow": 8,
    "left_wrist": 9, "right_wrist": 10,
    "left_hip": 11, "right_hip": 12,
    "left_knee": 13, "right_knee": 14,
    "left_ankle": 15, "right_ankle": 16
}

# Reduced for faster rep counting
STABILITY_FRAMES = 1

def calc_angle(self, a, b, c):
    """Calculate angle at point b between points a and c"""
    a = np.array(a[:2], dtype=np.float32)
    b = np.array(b[:2], dtype=np.float32)
    c = np.array(c[:2], dtype=np.float32)
    ba = a - b
    bc = c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6
    cosine = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return np.degrees(np.arccos(cosine))

def evaluate_form(self, exercise, keypoints, rep_state):
    """
    Evaluate exercise form and detect reps in real-time.
    
    Returns:
        feedback (str): Text feedback for user
        colors (dict): Colors for skeleton visualization
        rep_done (bool): Whether a rep was just completed
    """
    if exercise == "Biceps Curl":
        return self._curl_form(keypoints, rep_state)
    if exercise == "Squat":
        return self._squat_form(keypoints, rep_state)
    return "", {}, False

def _curl_form(self, kp, s):
    """Analyze Biceps Curl form - real-time rep detection"""
    s.setdefault("curl_state", "down")
    s.setdefault("stable", 0)
    s.setdefault("prev", None)
    s.setdefault("last_rep_time", 0)

    feedback = "Position arm in view"
    colors = {}
    rep_done = False
    DOWN = 145  # Fully extended arm angle
    UP = 75     # Fully curled arm angle

    for side in ("right", "left"):
        sh = self.KP[f"{side}_shoulder"]
        el = self.KP[f"{side}_elbow"]
        wr = self.KP[f"{side}_wrist"]
        
        # Check if keypoints are visible
        if not all(kp[i][0] > 0 for i in (sh, el, wr)):
            continue

        angle = self.calc_angle(kp[sh], kp[el], kp[wr])
        zone = "down" if angle > DOWN else "up" if angle < UP else "mid"

        # Stability detection for smoother transitions
        if zone == s["prev"]:
            s["stable"] += 1
        else:
            s["stable"] = 1
        s["prev"] = zone

        # REAL-TIME rep counting logic
        if zone == "down" and s["stable"] >= self.STABILITY_FRAMES:
            if s["curl_state"] == "up":
                # Rep completed: from UP position to DOWN position
                rep_done = True
            s["curl_state"] = "down"
            feedback = f"{int(angle)}° - Now curl UP!"
        elif zone == "up" and s["stable"] >= self.STABILITY_FRAMES:
            s["curl_state"] = "up"
            feedback = f"{int(angle)}° - Lower back DOWN!"
        else:
            feedback = f"{int(angle)}° - Moving..."

        # Highlight working joints in green
        colors[(sh, el)] = (0, 255, 0)
        colors[(el, wr)] = (0, 255, 0)
        break

    return feedback, colors, rep_done

def _squat_form(self, kp, s):
    """Analyze Squat form - real-time rep detection"""
    s.setdefault("squat_state", "up")
    s.setdefault("stable", 0)
    s.setdefault("prev", None)
    s.setdefault("last_rep_time", 0)

    feedback = "Position legs in view"
    colors = {}
    rep_done = False
    STAND = 150  # Standing leg angle
    DOWN = 100   # Fully squatted leg angle

    for side in ("right", "left"):
        hip = self.KP[f"{side}_hip"]
        knee = self.KP[f"{side}_knee"]
        ank = self.KP[f"{side}_ankle"]
        
        # Check if keypoints are visible
        if not all(kp[i][0] > 0 for i in (hip, knee, ank)):
            continue

        angle = self.calc_angle(kp[hip], kp[knee], kp[ank])
        zone = "up" if angle > STAND else "down" if angle < DOWN else "mid"

        # Stability detection for smoother transitions
        if zone == s["prev"]:
            s["stable"] += 1
        else:
            s["stable"] = 1
        s["prev"] = zone

        # REAL-TIME rep counting logic
        if zone == "up" and s["stable"] >= self.STABILITY_FRAMES:
            if s["squat_state"] == "down":
                # Rep completed: from DOWN position to UP position
                rep_done = True
            s["squat_state"] = "up"
            feedback = f"{int(angle)}° - Squat DOWN!"
        elif zone == "down" and s["stable"] >= self.STABILITY_FRAMES:
            s["squat_state"] = "down"
            feedback = f"{int(angle)}° - Stand UP!"
        else:
            feedback = f"{int(angle)}° - Moving..."

        # Highlight working joints in green
        colors[(hip, knee)] = (0, 255, 0)
        colors[(knee, ank)] = (0, 255, 0)
        break

    return feedback, colors, rep_done

def get_rep_quality(self, last_feedback=""):
    """
    Calculate form quality (0.0 to 1.0).
    Returns high quality for now; can be enhanced with detailed analysis.
    """
    return 1.0

def draw_feedback(self, img, feedback, rep_count, exercise):
    """Draw rep count and feedback on frame"""
    # Draw exercise name and rep count at top
    cv2.putText(img, f"{exercise} | Reps: {rep_count}", (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Draw feedback with larger font
    cv2.putText(img, feedback, (10, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    return img
```
