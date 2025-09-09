import streamlit as st

st.title("🚨 Escalation / Alerts")

st.subheader("Danh sách câu hỏi đã escalate")
st.table({
    "Câu hỏi": ["Khách hàng hỏi giá custom", "Tích hợp Salesforce"],
    "Trạng thái": ["Đang xử lý", "Chờ phản hồi"]
})

st.subheader("Người chịu trách nhiệm")
st.table({
    "Người": ["Anh A", "Chị B"],
    "Công việc": ["Trả lời khách", "Cập nhật tài liệu"]
})
