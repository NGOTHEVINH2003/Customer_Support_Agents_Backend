import streamlit as st
import pandas as pd
import plotly.express as px
import requests

api_url = "http://127.0.0.1:8000/get-negative-feedback-trend"

try:
    response = requests.post(api_url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["data"])
    else:
        st.error("Lỗi khi lấy dữ liệu từ API.")
except Exception as e:
    st.error(f"Exception occurred: {str(e)}")
    df = pd.DataFrame()

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
