import streamlit as st

st.title("📂 Ingestion / Data Status")

st.subheader("📜 Lịch sử ingest docs")
st.table({
    "Nguồn": ["PDF", "Google Docs", "Notion"],
    "Ngày": ["2025-09-07", "2025-09-08", "2025-09-09"],
    "Trạng thái": ["Thành công", "Thất bại", "Thành công"]
})

st.subheader("⚙️ Cron Job Status")
st.table({
    "Job": ["Job 1", "Job 2", "Job 3"],
    "Kết quả": ["Thành công", "Thất bại", "Thành công"]
})
