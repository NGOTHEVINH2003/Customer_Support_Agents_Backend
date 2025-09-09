import streamlit as st

st.title("📉 Feedback Analytics")

st.subheader("Trend Negative Feedback")
st.line_chart({"negative": [2, 5, 3, 6, 4, 7]})  # demo trend

st.subheader("Top câu hỏi khó (AI chưa trả lời)")
st.table({
    "Câu hỏi": ["Làm sao tích hợp với SAP?", "Hỗ trợ tiếng Nhật không?"],
    "Số lần thất bại": [12, 7]
})
