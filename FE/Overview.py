import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(
    page_title="AI Agent Monitor Dashboard", 
    layout="wide"
)

st.title("📊 Overview")

todayQuestions, thisWeekQuestions, thisMonthQuestions, escalationRate = st.columns(4, border=True)
with todayQuestions:
    st.metric("Số câu hỏi hôm nay", 124)
with thisWeekQuestions:
    st.metric("Số câu hỏi tuần này", 850)
with thisMonthQuestions:
    st.metric("Số câu hỏi tháng này", 3200)
with escalationRate:
    st.metric("Escalation rate", "8%")

ai_vs_escalated = pd.DataFrame({
    "name": ["AI answered", "Escalated"],
    "value": [3000, 200]
})

rating_dist = pd.DataFrame({
    "rating": ["1★", "2★", "3★", "4★", "5★"],
    "count": [40, 65, 180, 310, 325]
})

aiVSEscalatedPie, ratingDistBar = st.columns([1,1], border=True)
with aiVSEscalatedPie:
    st.subheader("AI Answered vs Escalated")
    fig =  px.pie(ai_vs_escalated, names="name", values="value", hole=0.5,
                     color="name", color_discrete_map={"AI answered":"#22c55e","Escalated":"#ef4444"})
    st.plotly_chart(fig, use_container_width=True, theme=None)
with ratingDistBar:
    st.subheader("Distribution Rating (⭐)")
    fig2 = px.bar(rating_dist, x="rating", y="count", labels={"count":"Feedback","rating":"Rating"}, color="rating")
    st.plotly_chart(fig2, use_container_width=True, theme=None)