import sqlite3
import json
import hashlib
from datetime import datetime,timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "log.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS query_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id TEXT NOT NULL,
        question TEXT NOT NULL,
        channel_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        similarity_score REAL,
        answer TEXT,
        flagged INTEGER DEFAULT 0,
        Thumps_up INTEGER DEFAULT 0,
        Thumps_down INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")


    cur.execute("""CREATE TABLE IF NOT EXISTS ingestion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        document_id TEXT NOT NULL,
        document_type TEXT,
        document_name TEXT,
        status TEXT NOT NULL,
        last_modified TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        Unique(source, document_id)
    )""")

    conn.commit()
    conn.close()


def log_query(question_id: str,user_id:str, channel_id:str,query: str, answer: str, similarity_score: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO query_logs (question_id,channel_id,user_id, question, similarity_score, answer, timestamp) VALUES (?, ?, ?, ?,?, ?, ?)",
        (question_id, channel_id, user_id, query, similarity_score, answer, datetime.now(timezone.utc).isoformat() )
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


# when an reaction is added to a message, update the thumbs up/down count
def update_reaction_added(question_id: int, thumbs_up: bool, thumbs_down: bool):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE query_logs SET thumbs_up = thumbs_up + ?, thumbs_down = thumbs_down + ? WHERE question_id = ?",
        (1 if thumbs_up else 0, 1 if thumbs_down else 0, question_id)
    )
    conn.commit()
    conn.close()
def update_reaction_removed(question_id: int, thumbs_up: bool, thumbs_down: bool):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE query_logs SET thumbs_up = thumbs_up - ?, thumbs_down = thumbs_down - ? WHERE question_id = ? AND thumbs_up > 0 AND thumbs_down > 0",
        (1 if thumbs_up else 0, 1 if thumbs_down else 0, question_id)
    )
    conn.commit()
    conn.close()

# update the flagged status of a query log entry
def updated_flagged_status(question_id: int, flagged: bool):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE query_logs SET flagged = ?  WHERE question_id = ?",
        (1 if flagged else 0, question_id)
    )
    conn.commit()
    conn.close()
# dictate that whether to ingest the document based on its last modified timestamp
def should_ingest(source: str, document_id: str, last_modified: datetime) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, last_modified FROM ingestion_logs WHERE source = ? AND document_id = ?",
        (source, document_id)
    )
    row = cursor.fetchone()
    # not existed in the db -> ingest into vector db
    if row is None:
        return True
    existing_status, existing_last_modified = row
    if existing_status == "failed":
        # previous ingestion failed -> try again
        return True
    if existing_last_modified is None or last_modified is None:
        return False
    existing_last_modified = datetime.fromisoformat(existing_last_modified)
    # if the document has been modified since last ingestion -> re-ingest
    return last_modified > existing_last_modified
# log the ingestion status into the db for monitoring and version control
def upsert_log(source, document_id, document_type, document_name, status, last_modified):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    last_modified_str = last_modified.isoformat() if last_modified else None

    cursor.execute(
        #if the record exists, update it; otherwise, insert a new record
        """INSERT INTO ingestion_logs (source, document_id, document_type, document_name,  status, last_modified, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(source, document_id) DO UPDATE SET
                document_type=excluded.document_type,
                document_name=excluded.document_name,
                status=excluded.status,
                last_modified=excluded.last_modified,
                created_at=excluded.created_at
        """,
        (source, document_id,document_type,document_name , status, last_modified_str, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()


def get_ingestion_logs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ingestion_logs ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()