import datetime
import pandas as pd
from Database import get_db_connection

def GetMetrics():
    conn = get_db_connection()
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

    # AI answered and escalated
    cur.execute("SELECT COUNT(*) FROM query_logs")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM query_logs WHERE flagged=1")
    escalated = cur.fetchone()[0]
    ai_answered = total - escalated

    query = "SELECT question FROM query_logs WHERE flagged=1"
    escalated_table = pd.read_sql(query, conn)

    conn.close()
    return today_count, week_count, month_count, ai_answered, escalated, escalated_table

def GetNegativeFeedbackTrend():
    conn = get_db_connection()
    query = """
        SELECT DATE(timestamp) as Day, SUM(Thumps_down) as Negative_Feedback
        FROM query_logs
        GROUP BY DATE(timestamp)
        ORDER BY Day
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def GetIngestionHistory():
    conn = get_db_connection()
    query = """
        SELECT document_name as 'Tên tài liệu',
               source as 'Nguồn',
               DATETIME(last_modified) as 'Lần cuối sửa',
               DATETIME(created_at) as 'Ngày tải lên',
               status as 'Trạng thái'
        FROM ingestion_logs
        ORDER BY last_modified DESC
        LIMIT 10
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def ShowHardQuestions():
    conn = get_db_connection()
    query = """
        SELECT 
            question,
            COUNT(*) AS total_asked,
            MAX(timestamp) AS last_asked,
            CASE 
                WHEN SUM(flagged) > 0 
                    OR SUM(CASE WHEN similarity_score < 0.5 THEN 1 ELSE 0 END) > 0
                    OR SUM(CASE WHEN Thumps_down > Thumps_up THEN 1 ELSE 0 END) > 0
                THEN 'Yes'
                ELSE 'No'
            END AS escalated
        FROM query_logs
        GROUP BY question;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df