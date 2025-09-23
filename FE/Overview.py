import streamlit as st
import plotly.express as px
import pandas as pd
from pathlib import Path
import sqlite3
import datetime
from io import BytesIO
import requests

api_url = "http://127.0.0.1:8000/get-metrics"

st.set_page_config(
    page_title="AI Agent Monitor Dashboard", 
    layout="wide"
)

try: 
    respone = requests.post(api_url)
    if respone.status_code == 200:
        data = respone.json()
        metrics = data["metrics"]
        today_count = metrics["today_count"]
        week_count = metrics["week_count"]
        month_count = metrics["month_count"]
        answered = metrics["ai_answered"]
        escalated = metrics["escalated"]
    else:
        st.error(f"Error fetching metrics: {respone.status_code} - {respone.text}")
        today_count, week_count, month_count = 0, 0, 0
except Exception as e:
    st.error(f"Exception occurred: {str(e)}")
    today_count, week_count, month_count = 0, 0, 0

st.title("📊 Overview")

todayQuestions, thisWeekQuestions, thisMonthQuestions = st.columns(3, border=True)

with todayQuestions:
    st.metric("Số câu hỏi hôm nay", today_count)
with thisWeekQuestions:
    st.metric("Số câu hỏi tuần này", week_count)
with thisMonthQuestions:
    st.metric("Số câu hỏi tháng này", month_count)

df = pd.DataFrame({
    "name": ["AI answered", "Escalated"],
    "value": [answered, escalated]
    })

aiVSEscalatedPie = st.columns(1, border=True)[0]

with aiVSEscalatedPie:
    st.subheader("AI Answered vs Escalated")
    fig =  px.pie(df, names="name", values="value", hole=0.5,
                     color="name", color_discrete_map={"AI answered":"#22c55e","Escalated":"#ef4444"})
    st.plotly_chart(fig, use_container_width=True, theme=None)