import streamlit as st
import plotly.express as px
import pandas as pd
from pathlib import Path
import sqlite3
import datetime
from io import BytesIO

DB_PATH = Path(r"E:\Python\Customer_Support_Agents_Backend\FE\log.db")

def GetMetrics():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.datetime.now()

    # Today's questions
    today = now.date().isoformat()
    cur.execute("SELECT COUNT(*) FROM query_logs WHERE DATE(timestamp) = ?", (today,))
    today_count = cur.fetchone()[0]

    # This week's questions
    startWeek = (now - datetime.timedelta(days=now.weekday())).date().isoformat()
    cur.execute("SELECT COUNT(*) FROM query_logs WHERE DATE(timestamp) >= ?", (startWeek,))
    week_count = cur.fetchone()[0]

    # This month's questions
    startMonth = now.replace(day=1).date().isoformat()
    cur.execute("SELECT COUNT(*) FROM query_logs WHERE DATE(timestamp) >= ?", (startMonth,))
    month_count = cur.fetchone()[0]

    conn.close()
    return today_count, week_count, month_count

def getAIVsEscalated():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM query_logs")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM query_logs WHERE flagged=1")
    escalated = cur.fetchone()[0]

    conn.close()
    ai_answered = total - escalated
    return ai_answered, escalated

def exportExcel(today_count, week_count, month_count, answered, escalated):
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        metrics_df = pd.DataFrame({
            "Today": [today_count],
            "This Week": [week_count],
            "This Month": [month_count],
            "AI Answered": [answered],
            "Escalated": [escalated]
        })
        metrics_df.to_excel(writer, sheet_name="Metrics", index=False)
    
    output.seek(0)
    return output.getvalue()

st.set_page_config(
    page_title="AI Agent Monitor Dashboard", 
    layout="wide"
)

st.title("📊 Overview")

todayQuestions, thisWeekQuestions, thisMonthQuestions = st.columns(3, border=True)
today_count, week_count, month_count = GetMetrics()

with todayQuestions:
    st.metric("Số câu hỏi hôm nay", today_count)
with thisWeekQuestions:
    st.metric("Số câu hỏi tuần này", week_count)
with thisMonthQuestions:
    st.metric("Số câu hỏi tháng này", month_count)

answered, escalated = getAIVsEscalated()

df = pd.DataFrame({
    "name": ["AI answered", "Escalated"],
    "value": [answered, escalated]
    })

rating_dist = pd.DataFrame({
    "rating": ["1★", "2★", "3★", "4★", "5★"],
    "count": [40, 65, 180, 310, 325]
})

aiVSEscalatedPie = st.columns(1, border=True)[0]

with aiVSEscalatedPie:
    st.subheader("AI Answered vs Escalated")
    fig =  px.pie(df, names="name", values="value", hole=0.5,
                     color="name", color_discrete_map={"AI answered":"#22c55e","Escalated":"#ef4444"})
    st.plotly_chart(fig, use_container_width=True, theme=None)

excel_file = exportExcel(today_count, week_count, month_count, answered, escalated)
st.download_button(
    label="📥 Tải dữ liệu Excel",
    data=excel_file,
    file_name="dashboard_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)