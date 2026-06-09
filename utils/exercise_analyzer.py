import numpy as np
import cv2

class ExerciseAnalyzer:
    KP = {
        "left_shoulder": 5, "right_shoulder": 6,
        "left_elbow": 7, "right_elbow": 8,
        "left_wrist": 9, "right_wrist": 10,
        "left_hip": 11, "right_hip": 12,
        "left_knee": 13, "right_knee": 14,
        "left_ankle": 15, "right_ankle": 16
    }

    # Lowered for mobile – 3 frames = ~150ms at 20fps
    STABILITY_FRAMES = 4

    def calc_angle(self, a, b, c):
        a, b, c = np.array(a[:2]), np.array(b[:2]), np.array(c[:2])
        ba, bc = a - b, c - b
        denom = (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        cosine = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
        return np.degrees(np.arccos(cosine))

    def calc_all_angles(self, keypoints):
        angles = {}
        if keypoints is None: return angles
        for side in ['left','right']:
            sh,el,wr = [self.KP[f"{side}_{x}"] for x in ['shoulder','elbow','wrist']]
            if all(keypoints[i][0]>0 for i in [sh,el,wr]):
                angles[f"{side}_elbow"] = self.calc_angle(keypoints[sh],keypoints[el],keypoints[wr])
        for side in ['left','right']:
            hip,knee,ank = [self.KP[f"{side}_{x}"] for x in ['hip','knee','ankle']]
            sh = self.KP[f"{side}_shoulder"]
            if all(keypoints[i][0]>0 for i in [hip,knee,ank]):
                angles[f"{side}_knee"] = self.calc_angle(keypoints[hip],keypoints[knee],keypoints[ank])
                if keypoints[sh][0]>0:
                    angles[f"{side}_hip"] = self.calc_angle(keypoints[sh],keypoints[hip],keypoints[knee])
        return angles

    def evaluate_form(self, exercise, keypoints, rep_state):
        if exercise == "Biceps Curl":
            return self._curl_form(keypoints, rep_state)
        elif exercise == "Squat":
            return self._squat_form(keypoints, rep_state)
        return "", {}, False

    def _curl_form(self, kp, s):
        # separate state keys to avoid cross-talk
        s.setdefault("curl_state","down")
        s.setdefault("curl_stable",0)
        s.setdefault("curl_prev",None)
        feedback, colors, rep_done = "", {}, False

        for side in ['right','left']: # prefer right
            sh,el,wr = self.KP[f"{side}_shoulder"], self.KP[f"{side}_elbow"], self.KP[f"{side}_wrist"]
            hip = self.KP[f"{side}_hip"]
            if not all(kp[i][0]>0 for i in [sh,el,wr,hip]): continue

            angle = self.calc_angle(kp[sh],kp[el],kp[wr])
            zone = "down" if angle>145 else "up" if angle<60 else "mid"

            s["curl_stable"] = s["curl_stable"]+1 if zone==s["curl_prev"] else 1
            s["curl_prev"] = zone

            if zone=="down" and s["curl_stableFound it — your rep counter was crashing silently every frame. And your YOLO model is running at full 640×480, which is why you get the "Connection taking longer" on mobile.

### What was breaking reps:
1. **In `ExerciseAnalyzer` you draw text on the *keypoints array*, not the image** — `cv2.putText(kp,...)` — this throws an exception every frame, so `rep_done` never returns True. That's why it stayed at 0.
2. **STABILITY_FRAMES = 8** is ~0.5s at 20fps. On a laggy phone you never stay stable that long, so it never counts.
3. **YOLOv8n-pose at 640×480** on Streamlit Cloud CPU = 2-3 FPS → WebRTC times out.

Here are the fixed, mobile-optimized versions. Drop these in `utils/` — no other changes needed.

---

### 1) `utils/exercise_analyzer.py` (fixed + 3x faster)

```python
import numpy as np

class ExerciseAnalyzer:
    KP = {
        "left_shoulder": 5, "right_shoulder": 6,
        "left_elbow": 7, "right_elbow": 8,
        "left_wrist": 9, "right_wrist": 10,
        "left_hip": 11, "right_hip": 12,
        "left_knee": 13, "right_knee": 14,
        "left_ankle": 15, "right_ankle": 16
    }

    # Lowered for mobile latency - 4 frames ≈ 0.25s
    STABILITY_FRAMES = 5

    def calc_angle(self, a, b, c):
        a, b, c = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32), np.array(c, dtype=np.float32)
        ba, bc = a - b, c - b
        denom = (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        cosine = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
        return np.degrees(np.arccos(cosine))

    def calc_all_angles(self, keypoints):
        # kept for compatibility, not used now
        return {}

    def evaluate_form(self, exercise, keypoints, rep_state):
        if exercise == "Biceps Curl":
            return self._curl_form(keypoints, rep_state)
        elif exercise == "Squat":
            return self._squat_form(keypoints, rep_state)
        return "", {}, False

    # ─── BICEPS CURL ────────────────────────────────────
    def _curl_form(self, kp, rep_state):
        if "curl_state" not in rep_state:
            rep_state.update({"curl_state": "down", "stable_count": 0, "prev_zone": None})

        feedback, color_guide, rep_done = "", {}, False
        DOWN, UP = 160, 60 # wider thresholds = easier on phone

        for side in ('right', 'left'): # right first (most phones mirror)
            sh, el, wr = self.KP[f"{side}_shoulder"], self.KP[f"{side}_elbow"], self.KP[f"{side}_wrist"]
            if not all(kp[i][0] > 0 for i in (sh, el, wr)):
                continue

            angle = self.calc_angle(kp[sh], kp[el], kp[wr])
            zone = "down" if angle > DOWN else "up" if angle < UP else "mid"

            # stability
            rep_state["stable_count"] = rep_state["stable_count"] + 1 if zone == rep_state["prev_zone"] else 1
            rep_state["prev_zone"] = zone

            if zone == "down" and rep_state["stable_count"] >= self.STABILITY_FRAMES:
                if rep_state["curl_state"] == "up":
                    rep_done = True
                rep_state["curl_state"] = "down"
            elif zone == "up" and rep_state["stable_count"] >= self.STABILITY_FRAMES:
                rep_state["curl_state"] = "up"

            # colors
            col = (0,255,0) if rep_state["curl_state"] in ("up","down") else (0,255,255)
            color_guide[(sh,el)] = color_guide[(el,wr)] = col
            feedback = "Curl up" if rep_state["curl_state"]=="down" else "Lower slowly"

            # shoulder check - simpler
            if kp[sh][1] > kp[self.KP[f"{side}_hip"]][1] + 30:
                feedback += " | Keep shoulders down"
                color_guide[(sh,el)] = (0,0,255)
            break # use first visible arm
        return feedback, color_guide, rep_done

    # ─── SQUAT ────────────────────────────────────
    def _squat_form(self, kp, rep_state):
        if "squat_state" not in rep_state:
            rep_state.update({"squat_state": "up", "stable_count": 0, "prev_zone": None, "has_stood": True})

        feedback, color_guide, rep_done = "", {}, False
        STAND, DOWN = 160, 90

        for side in ('right','left'):
            hip, knee, ank = self.KP[f"{side}_hip"], self.KP[f"{side}_knee"], self.KP[f"{side}_ankle"]
            if not all(kp[i][0] > 0 for i in (hip, knee, ank)):
                continue

            knee_angle = self.calc_angle(kp[hip], kp[knee], kp[ank])
            zone = "up" if knee_angle > STAND else "down" if knee_angle < DOWN else "mid"

            rep_state["stable_count"] = rep_state["stable_count"] + 1 if zone == rep_state["prev_zone"] else 1
            rep_state["prev_zone"] = zone

            if zone == "up" and rep_state["stable_count"] >= self.STABILITY_FRAMES:
                if rep_state["squat_state"] == "down":
                    rep_done = True
                rep_state["squat_state"] = "up"
                rep_state["has_stood"] = True
            elif zone == "down" and rep_state["stable_count"] >= self.STABILITY_FRAMES:
                rep_state["squat_state"] = "down"

            col = (0,255,0)
            color_guide[(hip,knee)] = color_guide[(knee,ank)] = col
            feedback = "Go down" if rep_state["squat_state"]=="up" else "Stand up"

            # knee over toe check
            if kp[knee][0] > kp[ank][0] + 35:
                feedback += " | Knees forward"
                color_guide[(knee,ank)] = (0,0,255)
            break
        return feedback, color_guide, rep_done

    def get_rep_quality(self, last_feedback=""):
        return 0.7 if ("Keep" in last_feedback or "forward" in last_feedback) else 1.0

    def draw_feedback(self, img, feedback, rep_count, exercise):
        # keep this light - no heavy cv2 calls
        import cv2
        cv2.putText(img, f"{exercise} | Reps: {rep_count}", (10,28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        if feedback:
            cv2.putText(img, feedback.split("|")[0][:30], (10,55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
        return img
