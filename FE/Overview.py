import streamlit as st
import plotly.express as px
import pandas as pd
from pathlib import Path
import sqlite3
import datetime
from io import BytesIO

DB_PATH = Path(r"E:\Python\Customer_Support_Agents_Backend\FE\log.db")

def GetMetrics():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.datetime.now()

    # Today's questions
    today = now.date().isoformat()
    cur.execute("SELECT COUNT(*) FROM query_logs WHERE DATE(timestamp) = ?", (today,))
    today_count = cur.fetchone()[0]

    # This week's questions
    startWeek = (now - datetime.timedelta(days=now.weekday())).date().isoformat()
    cur.execute("SELECT COUNT(*) FROM query_logs WHERE DATE(timestamp) >= ?", (startWeek,))
    week_count = cur.fetchone()[0]

    # This month's questions
    startMonth = now.replace(day=1).date().isoformat()
    cur.execute("SELECT COUNT(*) FROM query_logs WHERE DATE(timestamp) >= ?", (startMonth,))
    month_count = cur.fetchone()[0]

    conn.close()
    return today_count, week_count, month_count

def getAIVsEscalated():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM query_logs")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM query_logs WHERE flagged=1")
    escalated = cur.fetchone()[0]

    conn.close()
    ai_answered = total - escalated
    return ai_answered, escalated

def GetTodayDate():
    return datetime.date.today()

def ExportDailyReport():
    today = GetTodayDate()

    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            COUNT(*) as TotalQuery,
            SUM(CASE WHEN flagged=0 THEN 1 ELSE 0 END) as AIAnswered,
            SUM(CASE WHEN flagged=1 THEN 1 ELSE 0 END) as Escalated,
            SUM(Thumps_up) as Like,
            SUM(Thumps_down) as Dislike
        FROM query_logs
        WHERE DATE(timestamp) = ?
    """
    df = pd.read_sql(query, conn, params=(today,))
    conn.close()

    total = df.loc[0, "TotalQuery"]
    ai_answered = df.loc[0, "AIAnswered"] or 0
    escalated = df.loc[0, "Escalated"] or 0
    like = df.loc[0, "Like"] or 0
    dislike = df.loc[0, "Dislike"] or 0

    df["Answered/Escalated Ratio(%)"] = (
        f"{(ai_answered/total*100):.1f} : {(escalated/total*100):.1f}"
        if total > 0 else "0:0"
    )
    df["Like/Dislike ratio(%)"] = (
        f"{(like/(like+dislike)*100):.1f} : {(dislike/(like+dislike)*100):.1f}"
        if (like+dislike) > 0 else "0:0"
    )

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        sheet_name = "Daily Report"
        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)

        worksheet = writer.sheets[sheet_name]
        worksheet.write(0, 0, f"Daily Report - {today}")

    output.seek(0)
    filename = f"report_{today}.xlsx"
    return output.getvalue(), filename

def ExportWeeklyReport():
    today = GetTodayDate()
    start_week = today - datetime.timedelta(days=today.weekday())  # thứ 2
    end_week = start_week + datetime.timedelta(days=6)             # chủ nhật

    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT DATE(timestamp) as Day,
               COUNT(*) as TotalQuery,
               SUM(CASE WHEN flagged=0 THEN 1 ELSE 0 END) as AIAnswered,
               SUM(CASE WHEN flagged=1 THEN 1 ELSE 0 END) as Escalated,
               SUM(Thumps_up) as Like,
               SUM(Thumps_down) as Dislike
        FROM query_logs
        WHERE DATE(timestamp) BETWEEN ? AND ?
        GROUP BY DATE(timestamp)
        ORDER BY Day
    """
    df = pd.read_sql(query, conn, params=(start_week.isoformat(), end_week.isoformat()))
    conn.close()

    # Tính tỷ lệ
    df["Answered/Escalated Ratio(%)"] = df.apply(
        lambda r: f"{(r['AIAnswered']/r['TotalQuery']*100):.1f} : {(r['Escalated']/r['TotalQuery']*100):.1f}"
        if r['TotalQuery']>0 else "0:0", axis=1
    )
    df["Like/Dislike ratio(%)"] = df.apply(
        lambda r: f"{(r['Like']/(r['Like']+r['Dislike'])*100):.1f} : {(r['Dislike']/(r['Like']+r['Dislike'])*100):.1f}"
        if (r['Like']+r['Dislike'])>0 else "0:0", axis=1
    )

    # Thêm tổng
    total_row = pd.DataFrame({
        "Day": ["total"],
        "TotalQuery": [df["TotalQuery"].sum()],
        "AIAnswered": [df["AIAnswered"].sum()],
        "Escalated": [df["Escalated"].sum()],
        "Like": [df["Like"].sum()],
        "Dislike": [df["Dislike"].sum()],
        "Answered/Escalated Ratio(%)": [
            f"{(df['AIAnswered'].sum()/df['TotalQuery'].sum()*100):.1f} : {(df['Escalated'].sum()/df['TotalQuery'].sum()*100):.1f}"
            if df["TotalQuery"].sum()>0 else "0:0"
        ],
        "Like/Dislike ratio(%)": [
            f"{(df['Like'].sum()/(df['Like'].sum()+df['Dislike'].sum())*100):.1f} : {(df['Dislike'].sum()/(df['Like'].sum()+df['Dislike'].sum())*100):.1f}"
            if (df['Like'].sum()+df['Dislike'].sum())>0 else "0:0"
        ]
    })
    df = pd.concat([df, total_row], ignore_index=True)

    # Xuất ra Excel 
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        sheet_name = "Weekly Report"
        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)

        # Ghi tiêu đề
        worksheet = writer.sheets[sheet_name]
        worksheet.write(0, 0, f"Weekly Report ({start_week} → {end_week})")

    output.seek(0)
    filename = f"weekly_report_{start_week}_to_{end_week}.xlsx"
    return output.getvalue(), filename

st.set_page_config(
    page_title="AI Agent Monitor Dashboard", 
    layout="wide"
)

st.title("📊 Overview")

todayQuestions, thisWeekQuestions, thisMonthQuestions = st.columns(3, border=True)
today_count, week_count, month_count = GetMetrics()

with todayQuestions:
    st.metric("Số câu hỏi hôm nay", today_count)
with thisWeekQuestions:
    st.metric("Số câu hỏi tuần này", week_count)
with thisMonthQuestions:
    st.metric("Số câu hỏi tháng này", month_count)

answered, escalated = getAIVsEscalated()

df = pd.DataFrame({
    "name": ["AI answered", "Escalated"],
    "value": [answered, escalated]
    })

aiVSEscalatedPie = st.columns(1, border=True)[0]

with aiVSEscalatedPie:
    st.subheader("AI Answered vs Escalated")
    fig =  px.pie(df, names="name", values="value", hole=0.5,
                     color="name", color_discrete_map={"AI answered":"#22c55e","Escalated":"#ef4444"})
    st.plotly_chart(fig, use_container_width=True, theme=None)

excelFileToday, filenameToday = ExportDailyReport()

st.download_button(
    label="📥 Export Today Report",
    data=excelFileToday,
    file_name=filenameToday,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

excelFileWeek, filenameWeekly = ExportWeeklyReport()

st.download_button(
    label="📥 Export This Week Report",
    data=excelFileWeek,
    file_name=filenameWeekly,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)