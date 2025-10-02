import sqlite3
import csv
from datetime import datetime, timezone, timedelta
import random
from pathlib import Path

DB_PATH = Path(__file__).parent / "log.db"


# -----------------------------
# DB CONNECTION
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# DB CREATION
# -----------------------------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # bảng query_logs để log các câu hỏi
    cur.execute(
        """CREATE TABLE IF NOT EXISTS query_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT NOT NULL,
            question TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            similarity_score REAL,
            answer TEXT,
            status TEXT DEFAULT 'answered',
            flagged INTEGER DEFAULT 0,
            thumbs_up INTEGER DEFAULT 0,
            thumbs_down INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )

    # bảng ingestion_logs, không UNIQUE, để track lịch sử ingest
    cur.execute(
        """CREATE TABLE IF NOT EXISTS ingestion_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            document_id TEXT NOT NULL,
            document_type TEXT,
            document_name TEXT,
            status TEXT NOT NULL,
            last_modified TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    )

    conn.commit()
    conn.close()


# -----------------------------
# Query logs 
# -----------------------------
def log_query(
    question_id: str,
    user_id: str,
    channel_id: str,
    query: str,
    answer: str,
    similarity_score: float,
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    flagged = 1 if similarity_score < 50 else 0

    cursor.execute(
        """INSERT INTO query_logs
           (question_id, channel_id, user_id, question, flagged, similarity_score, answer, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            question_id,
            channel_id,
            user_id,
            query,
            flagged,
            similarity_score,
            answer,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id


# -----------------------------
# Reaction Added
# -----------------------------
def update_reaction_added(question_id: str, thumbs_up: bool, thumbs_down: bool):
    with sqlite3.connect(DB_PATH) as conn:
        print({
            "question_id": question_id,
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down
            })
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE query_logs
            SET 
                thumbs_up   = thumbs_up + ?,
                thumbs_down = thumbs_down + ?,
                flagged = CASE 
                            WHEN (thumbs_down + ?) > (thumbs_up + ?) THEN 1
                            ELSE 0
                          END
            WHERE question_id = ?
            """,
            (
                1 if thumbs_up else 0,   
                1 if thumbs_down else 0, 
                1 if thumbs_down else 0, 
                1 if thumbs_up else 0,   
                question_id,
            ),
        )


# -----------------------------
# Reaction Removed
# -----------------------------
def update_reaction_removed(question_id: str, thumbs_up: bool, thumbs_down: bool):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE query_logs
            SET 
                thumbs_up   = MAX(thumbs_up - ?, 0),
                thumbs_down = MAX(thumbs_down - ?, 0),
                flagged = CASE 
                            WHEN MAX(thumbs_down - ?, 0) > MAX(thumbs_up - ?, 0) THEN 1
                            ELSE 0
                          END
            WHERE question_id = ?
            """,
            (
                1 if thumbs_up else 0,
                1 if thumbs_down else 0,
                1 if thumbs_down else 0,
                1 if thumbs_up else 0,
                question_id,
            ),
        )
        print("Rows updated (remove):", cursor.rowcount)

# -----------------------------
# Update logs status when export.
# -----------------------------

# def mark_done(question_ids: list[int]):
#     if not question_ids:
#         return

#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     placeholders = ",".join("?" for _ in question_ids)
#     query = f"UPDATE query_logs SET status = 'done' WHERE question_id IN ({placeholders})"
#     cursor.execute(query, question_ids)

#     conn.commit()
#     conn.close()

# # -----------------------------
# # Get list flagged pending for overview/export.
# # -----------------------------

# def get_flagged_pending():
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     cursor = conn.cursor()
#     cursor.execute(
#         "SELECT * FROM query_logs WHERE flagged = 1 AND status = 'pending'"
#     )
#     rows = cursor.fetchall()
#     conn.close()
#     return [dict(row) for row in rows]

# # -----------------------------
# # Export list question to CSV for answer
# # -----------------------------

# def export_flagged_pending_to_csv(filename="flagged_logs.csv"):
#     logs = get_flagged_pending()
#     if not logs:
#         return

#     keys = logs[0].keys()
#     with open(filename, "w", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=keys)
#         writer.writeheader()
#         writer.writerows(logs)


# -----------------------------
# Ingestion logs
# -----------------------------
def insert_ingestion_log(
    source: str,
    document_id: str,
    document_type: str,
    document_name: str,
    status: str,
    last_modified: datetime,
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    last_modified_str = last_modified.isoformat() if last_modified else None

    cursor.execute(
        """INSERT INTO ingestion_logs
              (source, document_id, document_type, document_name, status, last_modified, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            source,
            document_id,
            document_type,
            document_name,
            status,
            last_modified_str,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()

def should_ingest(document_id: str, last_modified: datetime) -> bool:
    """
    Kiểm tra xem document có cần ingest lại không
    - document_id: id duy nhất của tài liệu (ví dụ path, fileId, ...)
    - last_modified: thời gian chỉnh sửa cuối cùng của tài liệu (datetime)
    
    Return:
        True  -> nếu chưa có trong ingestion_logs hoặc có thay đổi mới
        False -> nếu bản mới nhất trong DB vẫn còn valid (status='success' và last_modified trùng)
    """
    history = get_ingestion_history(document_id)
    if not history:
        return True  # chưa từng ingest

    latest = history[0]  # bản gần nhất
    latest_status = latest.get("status")
    latest_modified = latest.get("last_modified")

    # Nếu bản cũ failed hoặc không có last_modified => cần ingest lại
    if latest_status != "success" or not latest_modified:
        return True

    # So sánh last_modified
    latest_dt = datetime.fromisoformat(latest_modified)
    if last_modified and last_modified > latest_dt:
        return True

    return False


def get_ingestion_logs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ingestion_logs ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_ingestion_history(document_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM ingestion_logs WHERE document_id = ? ORDER BY created_at DESC",
        (document_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def insert_mock_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ---------------- Query Logs ----------------
    sample_questions = [
        ("q1", "user1", "channel1", "Làm sao cài Docker?", "Bạn có thể dùng Docker Desktop.", 78.5),
        ("q2", "user2", "channel1", "Python lỗi Unicode?", "Dùng encoding='utf-8' khi mở file.", 62.3),
        ("q3", "user3", "channel2", "Hãy giải thích về RAG?", "RAG = Retrieval-Augmented Generation.", 45.0),
        ("q4", "user4", "channel2", "Test case khác test scenario thế nào?", "Scenario bao gồm nhiều test case.", 88.1),
        ("q5", "user5", "channel3", "Làm sao ingest file PDF?", "Dùng hàm ingest_local_files().", 30.0),
    ]

    for qid, uid, cid, q, a, score in sample_questions:
        flagged = 1 if score < 50 else 0
        cursor.execute(
            """INSERT INTO query_logs
               (question_id, channel_id, user_id, question, flagged, similarity_score, answer, thumbs_up, thumbs_down, status, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                qid,
                cid,
                uid,
                q,
                flagged,
                score,
                a,
                random.randint(0, 5),
                random.randint(0, 3),
                "answered",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    # ---------------- Ingestion Logs ----------------
    sample_docs = [
        ("local", "doc1", "pdf", "Docker Guide.pdf", "success"),
        ("local", "doc2", "txt", "Unicode Notes.txt", "success"),
        ("gdrive", "doc3", "pptx", "AI Presentation.pptx", "failed"),
        ("local", "doc4", "pdf", "ISTQB Foundation.pdf", "success"),
    ]

    now = datetime.now(timezone.utc)
    for source, did, dtype, name, status in sample_docs:
        cursor.execute(
            """INSERT INTO ingestion_logs
               (source, document_id, document_type, document_name, status, last_modified, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                source,
                did,
                dtype,
                name,
                status,
                (now - timedelta(days=random.randint(0, 30))).isoformat(),
                now.isoformat(),
            ),
        )

    conn.commit()
    conn.close()
    print("✅ Mock data inserted thành công!")


def get_all_query_logs(db_path="log.db"):
    """
    Lấy toàn bộ dữ liệu từ bảng query_logs
    Trả về: list các dict
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Cho phép truy cập theo tên cột
    cur = conn.cursor()

    cur.execute("SELECT * FROM query_logs")
    rows = cur.fetchall()

    result = [dict(row) for row in rows]

    conn.close()
    return result

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    init_db()
    # logs = get_all_query_logs("log.db")

    # for log in logs:
    #     print(log)

