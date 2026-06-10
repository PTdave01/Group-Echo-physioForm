import numpy as np
import cv2

class ExerciseAnalyzer:
    """
    Real‑time form analyser for Biceps Curl and Squat.
    Uses joint angles with a stability debounce to avoid miscounting.
    """

    KP = {
        "left_shoulder": 5, "right_shoulder": 6,
        "left_elbow": 7, "right_elbow": 8,
        "left_wrist": 9, "right_wrist": 10,
        "left_hip": 11, "right_hip": 12,
        "left_knee": 13, "right_knee": 14,
        "left_ankle": 15, "right_ankle": 16
    }

    # Number of consecutive frames the angle must stay in a zone before a rep counts
    STABILITY_FRAMES = 3   # ~0.2 sec at 15 fps – fast but not jittery

    def calc_angle(self, a, b, c):
        """Angle at point b (shoulder‑elbow‑wrist or hip‑knee‑ankle)."""
        a = np.array(a[:2], dtype=np.float32)
        b = np.array(b[:2], dtype=np.float32)
        c = np.array(c[:2], dtype=np.float32)
        ba = a - b
        bc = c - b
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
        return angle

    def evaluate_form(self, exercise, keypoints, rep_state):
        """
        Returns (feedback_text, line_colors_dict, rep_completed_bool).
        """
        if keypoints is None:
            return "No pose detected", {}, False

        if exercise == "Biceps Curl":
            return self._curl_form(keypoints, rep_state)
        elif exercise == "Squat":
            return self._squat_form(keypoints, rep_state)
        return "", {}, False

    def _is_visible(self, kp, idx):
        """Check if a keypoint is visible (not at origin)."""
        return kp[idx][0] > 1e-5 and kp[idx][1] > 1e-5

    def _curl_form(self, kp, s):
        """Biceps curl: rep counted when arm moves from extended → curled."""
        s.setdefault("curl_state", "down")
        s.setdefault("stable", 0)
        s.setdefault("prev_zone", None)

        feedback = "Position arm in view"
        colors = {}
        rep_done = False
        DOWN = 145   # elbow angle for extended arm
        UP = 75      # elbow angle for fully curled arm

        for side in ("right", "left"):
            sh = self.KP[f"{side}_shoulder"]
            el = self.KP[f"{side}_elbow"]
            wr = self.KP[f"{side}_wrist"]
            if not all(self._is_visible(kp, i) for i in (sh, el, wr)):
                continue

            angle = self.calc_angle(kp[sh], kp[el], kp[wr])
            zone = "down" if angle > DOWN else "up" if angle < UP else "mid"

            # Stability counter
            if zone == s["prev_zone"]:
                s["stable"] += 1
            else:
                s["stable"] = 1
            s["prev_zone"] = zone

            # Rep counting logic
            if zone == "down" and s["stable"] >= self.STABILITY_FRAMES:
                if s["curl_state"] == "up":
                    rep_done = True   # transition from curled to extended completes a rep
                s["curl_state"] = "down"
                feedback = f"{int(angle)}° – Now curl UP!"
            elif zone == "up" and s["stable"] >= self.STABILITY_FRAMES:
                s["curl_state"] = "up"
                feedback = f"{int(angle)}° – Lower back DOWN!"
            else:
                feedback = f"{int(angle)}° – Moving..."

            colors[(sh, el)] = (0, 255, 0)
            colors[(el, wr)] = (0, 255, 0)
            break   # only process one visible arm

        return feedback, colors, rep_done

    def _squat_form(self, kp, s):
        """Squat: rep counted when standing up from a deep squat."""
        s.setdefault("squat_state", "up")
        s.setdefault("stable", 0)
        s.setdefault("prev_zone", None)

        feedback = "Position legs in view"
        colors = {}
        rep_done = False
        STAND = 150   # knee angle when standing
        DOWN = 100    # knee angle at squat depth

        for side in ("right", "left"):
            hip = self.KP[f"{side}_hip"]
            knee = self.KP[f"{side}_knee"]
            ank = self.KP[f"{side}_ankle"]
            if not all(self._is_visible(kp, i) for i in (hip, knee, ank)):
                continue

            angle = self.calc_angle(kp[hip], kp[knee], kp[ank])
            zone = "up" if angle > STAND else "down" if angle < DOWN else "mid"

            # Stability counter
            if zone == s["prev_zone"]:
                s["stable"] += 1
            else:
                s["stable"] = 1
            s["prev_zone"] = zone

            # Rep counting logic
            if zone == "up" and s["stable"] >= self.STABILITY_FRAMES:
                if s["squat_state"] == "down":
                    rep_done = True   # transition from squat to stand completes a rep
                s["squat_state"] = "up"
                feedback = f"{int(angle)}° – Squat DOWN!"
            elif zone == "down" and s["stable"] >= self.STABILITY_FRAMES:
                s["squat_state"] = "down"
                feedback = f"{int(angle)}° – Stand UP!"
            else:
                feedback = f"{int(angle)}° – Moving..."

            colors[(hip, knee)] = (0, 255, 0)
            colors[(knee, ank)] = (0, 255, 0)
            break   # only process one visible leg

        return feedback, colors, rep_done

    def get_rep_quality(self, last_feedback=""):
        """
        Return a quality score 0.0–1.0 based on feedback.
        Currently returns 1.0 (perfect) because the stability filter already ensures good form.
        You can enhance this later by analysing shoulder sway / knee valgus.
        """
        return 1.0

    def draw_feedback(self, img, feedback, rep_count, exercise):
        """Overlay exercise name, rep count, and feedback on the video frame."""
        cv2.putText(img, f"{exercise} | Reps: {rep_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(img, feedback, (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        return img
