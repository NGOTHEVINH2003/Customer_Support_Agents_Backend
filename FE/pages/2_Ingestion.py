import streamlit as st
import pandas as pd
from api_client import ingest_local_files, get_ingestion_history


st.title("📂 Ingestion / Data Status")

# ================= Upload Files =================
import streamlit as st
from api_client import ingest_local_files

# Upload files
uploaded_files = st.file_uploader(
    "Upload data",
    type=["pdf", "docx", "xlsx", "txt", "csv"],
    accept_multiple_files=True,
)

if uploaded_files:
    results = ingest_local_files(uploaded_files)
    for res in results:
        if res["status"] == "success":
            st.success(f"✅ {res['file']} ingested successfully")
        else:
            st.error(f"❌ {res['file']} failed: {res.get('error', 'unknown error')}")
    results = []


# ================= Ingestion History =================
history = get_ingestion_history()
if not history:
    st.info("✅ Chưa có dữ liệu ingestion trong DB.")
else:
    st.subheader("📜 Lịch sử ingestion")
    df = pd.DataFrame(history)
    st.dataframe(df)
