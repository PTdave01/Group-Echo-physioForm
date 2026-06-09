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

    STABILITY_FRAMES = 5 # lower = easier on phone

    def calc_angle(self, a, b, c):
        a = np.array(a[:2], dtype=np.float32)
        b = np.array(b[:2], dtype=np.float32)
        c = np.array(c[:2], dtype=np.float32)
        ba = a - b
        bc = c - b
        denom = np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6
        cosine = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
        return np.degrees(np.arccos(cosine))

    def evaluate_form(self, exercise, keypoints, rep_state):
        if exercise == "Biceps Curl":
            return self._curl_form(keypoints, rep_state)
        if exercise == "Squat":
            return self._squat_form(keypoints, rep_state)
        return "", {}, False

    def _curl_form(self, kp, s):
        s.setdefault("curl_state", "down")
        s.setdefault("stable_count", 0)
        s.setdefault("prev_zone", None)

        feedback, colors, rep_done = "", {}, False
        DOWN, UP = 160, 60

        for side in ("right", "left"):
            sh = self.KP[f"{side}_shoulder"]
            el = self.KP[f"{side}_elbow"]
            wr = self.KP[f"{side}_wrist"]
            hip = self.KP[f"{side}_hip"]
            if not all(kp[i][0] > 0 for i in (sh, el, wr, hip)):
                continue

            angle = self.calc_angle(kp[sh], kp[el], kp[wr])
            zone = "down" if angle > DOWN else "up" if angle < UP else "mid"

            s["stable_count"] = s["stable_count"] + 1 if zone == s["prev_zone"] else 1
            s["prev_zone"] = zone

            if zone == "down" and s["stable_count"] >= self.STABILITY_FRAMES:
                if s["curl_state"] == "up":
                    rep_done = True
                s["curl_state"] = "down"
            elif zone == "up" and s["stable_count"] >= self.STABILITY_FRAMES:
                s["curl_state"] = "up"

            col = (0, 255, 0)
            colors[(sh, el)] = col
            colors[(el, wr)] = col
            feedback = "Curl up" if s["curl_state"] == "down" else "Lower slowly"

            if kp[sh][1] > kp[hip][1] + 30:
                feedback += " | Keep shoulders down"
                colors[(sh, el)] = (0, 0, 255)
            break
        return feedback, colors, rep_done

    def _squat_form(self, kp, s):
        s.setdefault("squat_state", "up")
        s.setdefault("stable_count", 0)
        s.setdefault("prev_zone", None)

        feedback, colors, rep_done = "", {}, False
        STAND, DOWN = 160, 90

        for side in ("right", "left"):
            hip = self.KP[f"{side}_hip"]
            knee = self.KP[f"{side}_knee"]
            ank = self.KP[f"{side}_ankle"]
            if not all(kp[i][0] > 0 for i in (hip, knee, ank)):
                continue

            angle = self.calc_angle(kp[hip], kp[knee], kp[ank])
            zone = "up" if angle > STAND else "down" if angle < DOWN else "mid"

            s["stable_count"] = s["stable_count"] + 1 if zone == s["prev_zone"] else 1
            s["prev_zone"] = zone

            if zone == "up" and s["stable_count"] >= self.STABILITY_FRAMES:
                if s["squat_state"] == "down":
                    rep_done = True
                s["squat_state"] = "up"
            elif zone == "down" and s["stable_count"] >= self.STABILITY_FRAMES:
                s["squat_state"] = "down"

            col = (0, 255, 0)
            colors[(hip, knee)] = col
            colors[(knee, ank)] = col
            feedback = "Go down" if s["squat_state"] == "up" else "Stand up"

            if kp[knee][0] > kp[ank][0] + 35:
                feedback += " | Knees forward"
                colors[(knee, ank)] = (0, 0, 255)
            break
        return feedback, colors, rep_done

    def get_rep_quality(self, last_feedback=""):
        return 0.7 if ("Keep" in last_feedback or "forward" in last_feedback) else 1.0

    def draw_feedback(self, img, feedback, rep_count, exercise):
        import cv2
        cv2.putText(img, f"{exercise} | Reps: {rep_count}", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if feedback:
            cv2.putText(img, feedback.split("|")[0].strip()[:35], (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        return img
