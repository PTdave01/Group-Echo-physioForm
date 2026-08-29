import math

def calculate_angle(a, b, c):
    ang = math.degrees(math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0]))
    ang = abs(ang)
    return 360-ang if ang>180 else ang

def analyze_form(landmarks, exercise="squat"):
    faults = []
    scores = {}
    if exercise == "squat":
        hip = [landmarks[23].x, landmarks[23].y]
        knee = [landmarks[25].x, landmarks[25].y]
        ankle = [landmarks[27].x, landmarks[27].y]
        shoulder = [landmarks[11].x, landmarks[11].y]
        knee_angle = calculate_angle(hip, knee, ankle)
        back_angle = calculate_angle(shoulder, hip, knee)
        scores['knee_angle'] = round(knee_angle,1)
        scores['back_angle'] = round(back_angle,1)
        if knee_angle > 110: faults.append("not_deep_enough")
        if knee_angle < 60: faults.append("too_deep_risky")
        if abs(landmarks[25].x - landmarks[27].x) > 0.08: faults.append("knees_caving_in")
        if back_angle < 150: faults.append("back_rounding")
    else:
        shoulder = [landmarks[11].x, landmarks[11].y]
        elbow = [landmarks[13].x, landmarks[13].y]
        wrist = [landmarks[15].x, landmarks[15].y]
        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        scores['elbow_angle'] = round(elbow_angle,1)
        if abs(landmarks[11].y - landmarks[12].y) > 0.05: faults.append("shoulder_swinging")
    quality = max(0, 10 - len(faults)*2.5)
    return {"exercise": exercise, "scores": scores, "faults": faults, "quality_score": quality}
