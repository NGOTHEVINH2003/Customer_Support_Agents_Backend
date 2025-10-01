import streamlit as st
import pandas as pd
import requests
from api_client import get_metrics


st.title("🚨 Escalation / Alerts")

df = pd.DataFrame(get_metrics().get("escalated_table", []))

if df.empty:
    st.info("✅ Chưa có câu hỏi nào bị escalate.")
else:
    st.subheader("Danh sách câu hỏi đã escalate")
    st.dataframe(df)
    