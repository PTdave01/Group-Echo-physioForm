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

    STABILITY_FRAMES = 8   # ~0.5 sec hold at 15 fps

    def calc_angle(self, a, b, c):
        a = np.array(a[:2], dtype=np.float32)
        b = np.array(b[:2], dtype=np.float32)
        c = np.array(c[:2], dtype=np.float32)
        ba = a - b
        bc = c - b
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
        return angle

    def evaluate_form(self, exercise, keypoints, rep_state):
        if keypoints is None:
            return "No pose detected", {}, False
        if exercise == "Biceps Curl":
            return self._curl_form(keypoints, rep_state)
        elif exercise == "Squat":
            return self._squat_form(keypoints, rep_state)
        return "", {}, False

    def _is_visible(self, kp, idx):
        return kp[idx][0] > 1e-5 and kp[idx][1] > 1e-5

    def _curl_form(self, kp, s):
        s.setdefault("curl_state", "down")
        s.setdefault("stable", 0)
        s.setdefault("prev_zone", None)
        s.setdefault("shoulder_warn", 0)

        feedback = "Position arm in view"
        colors = {}
        rep_done = False
        DOWN = 145
        UP = 75

        for side in ("right", "left"):
            sh = self.KP[f"{side}_shoulder"]
            el = self.KP[f"{side}_elbow"]
            wr = self.KP[f"{side}_wrist"]
            if not all(self._is_visible(kp, i) for i in (sh, el, wr)):
                continue

            angle = self.calc_angle(kp[sh], kp[el], kp[wr])
            zone = "down" if angle > DOWN else "up" if angle < UP else "mid"

            if zone == s["prev_zone"]:
                s["stable"] += 1
            else:
                s["stable"] = 1
            s["prev_zone"] = zone

            if zone == "down" and s["stable"] >= self.STABILITY_FRAMES:
                if s["curl_state"] == "up":
                    rep_done = True
                s["curl_state"] = "down"
                feedback = f"{int(angle)}° – Now curl UP!"
            elif zone == "up" and s["stable"] >= self.STABILITY_FRAMES:
                s["curl_state"] = "up"
                feedback = f"{int(angle)}° – Lower back DOWN!"
            else:
                feedback = f"{int(angle)}° – Moving..."

            colors[(sh, el)] = (0, 255, 0)
            colors[(el, wr)] = (0, 255, 0)

            # Shoulder stability check
            hip_y = kp[self.KP[f"{side}_hip"]][1]
            shoulder_y = kp[sh][1]
            if shoulder_y - hip_y > 25:
                feedback += " | Keep shoulders steady!"
                colors[(sh, el)] = (0, 0, 255)
                s["shoulder_warn"] = 1
            else:
                s["shoulder_warn"] = 0

            break
        return feedback, colors, rep_done

    def _squat_form(self, kp, s):
        s.setdefault("squat_state", "up")
        s.setdefault("stable", 0)
        s.setdefault("prev_zone", None)
        s.setdefault("knee_warn", 0)
        s.setdefault("back_warn", 0)

        feedback = "Position legs in view"
        colors = {}
        rep_done = False
        STAND = 150
        DOWN = 100

        for side in ("right", "left"):
            hip = self.KP[f"{side}_hip"]
            knee = self.KP[f"{side}_knee"]
            ank = self.KP[f"{side}_ankle"]
            sh = self.KP[f"{side}_shoulder"]
            if not all(self._is_visible(kp, i) for i in (hip, knee, ank)):
                continue

            angle = self.calc_angle(kp[hip], kp[knee], kp[ank])
            zone = "up" if angle > STAND else "down" if angle < DOWN else "mid"

            if zone == s["prev_zone"]:
                s["stable"] += 1
            else:
                s["stable"] = 1
            s["prev_zone"] = zone

            if zone == "up" and s["stable"] >= self.STABILITY_FRAMES:
                if s["squat_state"] == "down":
                    rep_done = True
                s["squat_state"] = "up"
                feedback = f"{int(angle)}° – Squat DOWN!"
            elif zone == "down" and s["stable"] >= self.STABILITY_FRAMES:
                s["squat_state"] = "down"
                feedback = f"{int(angle)}° – Stand UP!"
            else:
                feedback = f"{int(angle)}° – Moving..."

            colors[(hip, knee)] = (0, 255, 0)
            colors[(knee, ank)] = (0, 255, 0)

            # Knee over toe check
            if kp[knee][0] - kp[ank][0] > 40:
                feedback += " | Knees too far forward!"
                colors[(knee, ank)] = (0, 0, 255)
                s["knee_warn"] = 1
            else:
                s["knee_warn"] = 0

            # Back angle check
            if self._is_visible(kp, sh):
                torso_angle = np.degrees(np.arctan2(kp[sh][0] - kp[hip][0], kp[sh][1] - kp[hip][1]))
                if abs(torso_angle) < 20:
                    feedback += " | Keep back straight!"
                    colors[(sh, hip)] = (0, 0, 255)
                    s["back_warn"] = 1
                else:
                    s["back_warn"] = 0
            break
        return feedback, colors, rep_done

    def get_rep_quality(self, last_feedback="", rep_state=None):
        """
        Returns a quality score 0.0–1.0 based on feedback and warning flags.
        """
        score = 1.0
        if last_feedback:
            if "Keep shoulders steady" in last_feedback:
                score -= 0.3
            if "Knees too far forward" in last_feedback:
                score -= 0.3
            if "Keep back straight" in last_feedback:
                score -= 0.3
        if rep_state:
            if rep_state.get("shoulder_warn"):
                score -= 0.3
            if rep_state.get("knee_warn"):
                score -= 0.3
            if rep_state.get("back_warn"):
                score -= 0.3
        return max(0.3, score)

    def draw_feedback(self, img, feedback, rep_count, exercise):
        cv2.putText(img, f"{exercise} | Reps: {rep_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(img, feedback, (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        return img
