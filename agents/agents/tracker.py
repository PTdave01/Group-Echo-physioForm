def generate_report(session_data):
    if not session_data:
        return {"clinician_summary": "No reps detected"}
    avg_quality = sum([r['quality_score'] for r in session_data]) / len(session_data)
    all_faults = [f for r in session_data for f in r['faults']]
    summary = f"Session: {len(session_data)} reps, Avg Quality {avg_quality:.1f}/10, Adherence 100%.\n"
    if all_faults:
        most_common = max(set(all_faults), key=all_faults.count)
        summary += f"Main issue: {most_common} ({all_faults.count(most_common)}x). Recommendation: Focus on glute activation and control depth."
    else:
        summary += "No major faults. Ready to progress."
    return {"avg_quality": round(avg_quality,1), "total_reps": len(session_data), "faults": all_faults, "clinician_summary": summary}
