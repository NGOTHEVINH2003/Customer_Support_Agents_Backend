import sqlite3
import json
import hashlib
import datetime
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        question TEXT NOT NULL,
        similarity_score REAL,
        answer TEXT,
        flagged INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")


    cur.execute
    ("""CREATE TABLE IF NOT EXISTS ingestion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        document_id TEXT NOT NULL,
        status TEXT NOT NULL,
        metadata TEXT,
        last_modified TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        Unique(source, document_id)
    )""")

    conn.commit()
    conn.close()


def log_query(query: str, answer: str, similarity_score: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO query_logs (question, similarity_score, answer, created_at) VALUES (?, ?, ?)",
        (query, similarity_score, answer, datetime.utcnow().isoformat() )
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid

def updated_flagged_status(log_id: int, flagged: bool):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE query_logs SET flagged = ? WHERE id = ?",
        (1 if flagged else 0, log_id)
    )
    conn.commit()
    conn.close()

def should_ingest(source: str, document_id: str, last_modified: datetime.datetime) -> bool:
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
    existing_last_modified = datetime.datetime.fromisoformat(existing_last_modified)
    # if the document has been modified since last ingestion -> re-ingest
    return last_modified > existing_last_modified

def log_ingestion(source: str, document_id: str, status: str, metadata: dict = None, last_modified: datetime.datetime = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    metadata_json = json.dumps(metadata) if metadata else None
    last_modified_str = last_modified.isoformat() if last_modified else None

    cursor.execute(
        #if the record exists, update it; otherwise, insert a new record
        """INSERT INTO ingestion_logs (source, document_id, status, metadata, last_modified, created_at)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(source, document_id) DO UPDATE SET
               status=excluded.status,
               metadata=excluded.metadata,
               last_modified=excluded.last_modified,
               created_at=excluded.created_at
        """,
        (source, document_id, status, metadata_json, last_modified_str, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
print(f"Database created at {DB_PATH}")



