def recognize_exercise(landmarks):
    # Simple heuristic: if knee y moves a lot vs ankle, it's squat
    knee_y = landmarks[25].y
    ankle_y = landmarks[27].y
    if abs(knee_y - ankle_y) > 0.15:
        return {"exercise": "squat", "confidence": 0.85}
    else:
        return {"exercise": "bicep_curl", "confidence": 0.80}
