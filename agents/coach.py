FAULT_TO_CUE = {
    "knees_caving_in": "Push your knees out over your toes — keep them aligned!",
    "back_rounding": "Chest up, straighten your back to protect your spine.",
    "not_deep_enough": "Go a little deeper — aim for thighs parallel to floor.",
    "too_deep_risky": "Don't go too low, stop at 90 degrees.",
    "shoulder_swinging": "Keep your elbows pinned to your sides, no swinging!",
    "over_curling": "Control the top, don't over-squeeze.",
}

def coach(faults):
    if not faults:
        return "Perfect form! Keep it up!"
    return " | ".join([FAULT_TO_CUE.get(f, f) for f in faults])
