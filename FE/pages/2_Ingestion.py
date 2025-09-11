import streamlit as st
import pandas as pd

st.title("📂 Ingestion / Data Status")

st.subheader("Upload file to ingest")
uploaded_files = st.file_uploader(
    "Upload data", accept_multiple_files=True, type="txt"
)
for uploaded_file in uploaded_files:
    df = pd.read_csv(uploaded_file)
    st.write(df)

st.subheader("📜 Lịch sử ingest docs")
st.table({
    "Tên tài liệu": ["Doc1", "Doc2", "Doc3"],
    "Nguồn": ["PDF", "Google Docs", "Notion"],
    "Ngày": ["2025-09-07", "2025-09-08", "2025-09-09"],
    "Trạng thái": ["Thành công", "Thất bại", "Thành công"]
})

st.subheader("⚙️ Cron Job Status")
st.table({
    "Job": ["Job 1", "Job 2", "Job 3"],
    "Lần chạy cuối": ["2025-09-07 10:00", "2025-09-07 11:00", "2025-09-07 12:00"],
    "Kết quả": ["Thành công", "Thất bại", "Thành công"]
})
