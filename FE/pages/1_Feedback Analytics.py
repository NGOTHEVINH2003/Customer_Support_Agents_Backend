import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path

DB_PATH = Path(r"E:\Python\Customer_Support_Agents_Backend\BE\log.db")

# Lấy dữ liệu Negative Feedback theo ngày
def getNegativeFeedbackTrend():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT DATE(timestamp) as Day, SUM(Thumps_down) as Negative_Feedback
        FROM query_logs
        GROUP BY DATE(timestamp)
        ORDER BY Day
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.title("📉 Feedback Analytics")

# Lấy dữ liệu
df = getNegativeFeedbackTrend()

if df.empty:
    st.warning("⚠️ Chưa có dữ liệu Negative Feedback trong DB.")
else:
    fig = px.line(
        df,
        x="Day",
        y="Negative_Feedback",
        title="Trend Negative Feedback",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)

# Demo (làm sau) 
st.subheader("Top câu hỏi 'khó'")
st.table({
    "Câu hỏi": ["Làm sao tích hợp với SAP?", "Hỗ trợ tiếng Nhật không?"],
    "Số lượng hỏi": [15, 10],
    "Lần cuối hỏi": ["2025-09-09", "2025-09-08"],
    "Escalated": ["Yes", "No"]
})
