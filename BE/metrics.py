import datetime
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

    cur.execute("SELECT COUNT(*) FROM query_logs")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM query_logs WHERE flagged=1")
    escalated = cur.fetchone()[0]
    ai_answered = total - escalated

    conn.close()
    return today_count, week_count, month_count, ai_answered, escalated