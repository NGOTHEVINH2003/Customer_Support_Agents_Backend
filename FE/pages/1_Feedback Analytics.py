import streamlit as st

st.title("📉 Feedback Analytics")

st.subheader("Trend Negative Feedback")
st.line_chart({"negative": [2, 5, 3, 6, 4, 7]})  # demo trend

st.subheader("Top câu hỏi 'khó'")
st.table({
    "Câu hỏi": ["Làm sao tích hợp với SAP?", "Hỗ trợ tiếng Nhật không?"],
    "Số lượng hỏi": [15, 10],
    "Lần cuối hỏi": ["2025-09-09", "2025-09-08"],
    "Escalated": ["Yes", "No"]
})
