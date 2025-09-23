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