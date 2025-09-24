import streamlit as st
import pandas as pd
import plotly.express as px
import requests

api_url_trend = "http://127.0.0.1:8000/get-negative-feedback-trend"
api_url_hard = "http://127.0.0.1:8000/show-hard-questions"

df_trend = pd.DataFrame()
df_hard = pd.DataFrame()

try:
    response = requests.post(api_url_trend)
    if response.status_code == 200:
        data = response.json()
        df_trend = pd.DataFrame(data["data"])
    else:
        st.error("Lỗi khi lấy dữ liệu từ API.")
except Exception as e:
    st.error(f"Exception occurred: {str(e)}")

try:
    response = requests.post(api_url_hard)
    if response.status_code == 200:
        data = response.json()
        df_hard = pd.DataFrame(data["data"])
    else:
        st.error("Lỗi khi lấy dữ liệu từ API.")
except Exception as e:
    st.error(f"Exception occurred: {str(e)}")
    
st.title("📊 Feedback Analytics")

if df_trend.empty:
    st.warning("⚠️ Chưa có dữ liệu Negative Feedback trong DB.")
else:
    fig = px.line(
        df_trend,
        x="Day",
        y="Negative_Feedback",
        title="Trend Negative Feedback",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)

# Demo (làm sau) 
st.subheader("Top câu hỏi 'khó'")
if df_hard.empty:
    st.warning("⚠️ Chưa có câu hỏi 'khó' trong DB.")
else:
    st.dataframe(df_hard, use_container_width=True)
