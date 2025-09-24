import streamlit as st
import pandas as pd
import requests

api_url = "http://127.0.0.1:8000/get-ingestion-history"

df = pd.DataFrame()

try:
    response = requests.post(api_url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["data"])
    else:
        st.error("Lỗi khi lấy dữ liệu từ API.")
except Exception as e:
    st.error(f"Exception occurred: {str(e)}")

st.title("📂 Ingestion / Data Status")

st.subheader("Upload file to ingest")
uploaded_files = st.file_uploader(
    "Upload data", accept_multiple_files=True, type="txt"
)
for uploaded_file in uploaded_files:
    df = pd.read_csv(uploaded_file)
    st.write(df)

if df.empty:
    st.info("✅ Chưa có dữ liệu ingestion trong DB.")
else:
    st.subheader("Lịch sử ingestion")
    st.dataframe(df)