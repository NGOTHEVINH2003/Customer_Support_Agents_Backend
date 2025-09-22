import sqlite3
import pandas as pd
import datetime
from pathlib import Path
from io import BytesIO
from Database import get_db_connection

def GetToday():
    today = datetime.date.today()
    return today

def GetWeekRange():
    today = GetToday()
    start_week = today - datetime.timedelta(days=today.weekday())  # thứ 2
    end_week = start_week + datetime.timedelta(days=6)             # chủ nhật
    return start_week, end_week

def QueryDailyData():
    today = GetToday()

    conn = get_db_connection()
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
    df = QueryDailyData()

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
    return df

def QueryWeeklyData():
    start_week, end_week = GetWeekRange()

    conn = get_db_connection()
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

    df = QueryWeeklyData()
    start_week, end_week = GetWeekRange()
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
    return df

def CreateReport(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Report", startrow=2)

    output.seek(0)
    return output