import streamlit as st
import pandas as pd
import plotly.express as px
from api_client import get_negative_feedback_trend, show_hard_questions

st.title("📊 Feedback Analytics")

df_trend = pd.DataFrame(get_negative_feedback_trend())
df_hard = pd.DataFrame(show_hard_questions())

# ====== Negative Feedback Trend ======
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

# ====== Hard Questions ======
st.subheader("Top câu hỏi 'khó'")
if df_hard.empty:
    st.warning("⚠️ Chưa có câu hỏi 'khó' trong DB.")
else:
    st.dataframe(df_hard, use_container_width=True)
