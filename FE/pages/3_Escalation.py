import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(r"E:\Python\Customer_Support_Agents_Backend\BE\log.db")

def getEscalation():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT question FROM query_logs WHERE flagged=1"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.title("🚨 Escalation / Alerts")

df = getEscalation()

if df.empty:
    st.info("✅ Chưa có câu hỏi nào bị escalate.")
else:
    st.subheader("Danh sách câu hỏi đã escalate")
    st.table(df)
