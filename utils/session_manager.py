import streamlit as st
from supabase import create_client, Client
from datetime import datetime

class SessionManager:
    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.supabase: Client = create_client(self.url, self.key)

    def save_session(self, patient_id, exercise, reps, avg_form_quality, duration):
        data = {
            "patient_id": patient_id,
            "exercise": exercise,
            "reps": reps,
            "avg_form_quality": avg_form_quality,
            "duration": duration,
            "start_time": int(datetime.now().timestamp())
        }
        self.supabase.table("sessions").insert(data).execute()

    def load_all_sessions(self):
        response = self.supabase.table("sessions").select("*").order("id", desc=True).execute()
        return response.data if response.data else []
