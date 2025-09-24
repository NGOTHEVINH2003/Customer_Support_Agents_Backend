import streamlit as st
import pandas as pd
import requests

api_url = "http://127.0.0.1:8000/get-metrics"

st.title("🚨 Escalation / Alerts")

df = pd.DataFrame()

try:
    respone = requests.post(api_url)
    if respone.status_code == 200:
        data = respone.json()
        metrics = data["metrics"]
        escalated_table = metrics["escalated_table"]
        df = pd.DataFrame(escalated_table)
    else:
        st.error("Lỗi khi lấy dữ liệu từ API.")
except Exception as e:
    st.error(f"Exception occurred: {str(e)}")

if df.empty:
    st.info("✅ Chưa có câu hỏi nào bị escalate.")
else:
    st.subheader("Danh sách câu hỏi đã escalate")
    st.table(df)
    