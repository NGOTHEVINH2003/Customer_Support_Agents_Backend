import requests
import streamlit as st

backend_url = "http://localhost:8000/"

# ===================== GET METRIC API =====================
def get_metrics():
    try:
        response = requests.get(f"{backend_url}get-metrics")
        if response.status_code == 200:
            return response.json().get("metrics", {})
        else:
            st.error(f"Error fetching metrics: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        st.error(f"Exception occurred: {str(e)}")
        return {}
    
# ===================== FEEDBACK API =====================
def get_negative_feedback_trend():
    try:
        response = requests.get(f"{backend_url}get-negative-feedback-trend")
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            st.error(f"Error fetching negative feedback trend: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"Exception occurred: {str(e)}")
        return []
    
def show_hard_questions():
    try:
        response = requests.get(f"{backend_url}show-hard-questions")
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            st.error(f"Error fetching hard questions: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"Exception occurred: {str(e)}")
        return []

# ===================== INGESTION =====================
def ingest_local_files(files):
    """
    Upload nhiều file local để ingest.
    files: list of streamlit UploadedFile
    """
    results = []
    for file in files:
        try:
            files_param = {"files": (file.name, file, file.type)}
            response = requests.post(f"{backend_url}ingest_local", files=files_param)
            response.raise_for_status()
            results.append({
                "file": file.name,
                "status": "success",
                "response": response.json()
            })
        except Exception as e:
            st.error(f"❌ Error ingesting {file.name}: {str(e)}")
            results.append({
                "file": file.name,
                "status": "failed",
                "error": str(e)
            })
    return results


def get_ingestion_history():
    """
    Lấy lịch sử ingestion từ backend    
    """
    try:
        response = requests.get(f"{backend_url}get-ingestion-history")
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        st.error(f"❌ Error fetching ingestion history: {str(e)}")
        return []
