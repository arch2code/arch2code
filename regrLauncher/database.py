import threading
import sqlite3
import os

lock = threading.Lock()

SESSION_STATUS_ENUM = { 'pending': 0, 'running': 1, 'finished': 2, 'aborted': 3 }

def init_db(db_file):

    # Allow connection sharing across threads
    conn = sqlite3.connect(db_file, check_same_thread=False)

    """Initialize the SQLite database with a table."""
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT NOT NULL,
                session_dir TEXT,
                start_date TEXT,
                finish_date TEXT,
                status INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                session_id INTEGER NOT NULL REFERENCES sessions(id),
                test_group TEXT,
                test_name TEXT,
                run_dir TEXT,
                run_cmd TEXT,
                status INTEGER,
                num_failures INTEGER,
                duration REAL,
                exec_status_ INTEGER
            )
        """)
    conn.close()

class sqlDbSession:

    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.session_id = None

    def __del__(self):
        self.conn.close()

    def insert_session(self, session_name, session_dir, start_date, status):
        with self.conn:  # 'with' handles transactions and commits
            cursor = self.conn.cursor()
            with lock:  # Ensure thread-safe access to the connection
                cursor.execute("""
                    INSERT INTO sessions (session_name, session_dir, start_date, status)
                    VALUES (?, ?, ?, ?)
                """, (session_name, session_dir, start_date, status))
            self.conn.commit()
        self.session_id = cursor.lastrowid

    def update_session(self, finish_date, status):
        if not self.session_id:
            raise ValueError("Session ID is not set. Cannot update session.")
        with self.conn:  # 'with' handles transactions and commits
            with lock:  # Ensure thread-safe access to the connection
                self.conn.execute("""
                    UPDATE sessions
                    SET finish_date = ?, status = ?
                    WHERE id = ?
                """, (finish_date, status, self.session_id))
            self.conn.commit()

class sqlDbRun:

    def __init__(self, db_file, session_id):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.session_id = session_id

    def __del__(self):
        self.conn.close()

    def insert_run(self, run_id, test_group, test_name, run_dir, run_cmd):
        with self.conn:  # 'with' handles transactions and commits
            cursor = self.conn.cursor()
            with lock:  # Ensure thread-safe access to the connection
                cursor.execute("""
                INSERT INTO runs (run_id, session_id, test_group, test_name, run_dir, run_cmd)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (run_id, self.session_id, test_group, test_name, run_dir, run_cmd))
        self.conn.commit()
        return cursor.lastrowid

    def update_run(self, run_id, status, num_failures, duration, exec_status_):
        with self.conn:  # 'with' handles transactions and commits
            with lock:  # Ensure thread-safe access to the connection
                self.conn.execute("""
                    UPDATE runs
                    SET status = ?, num_failures = ?, duration = ?, exec_status_ = ?
                    WHERE (run_id = ? AND session_id = ?)
                """, (status, num_failures, duration, exec_status_, run_id, self.session_id))
        self.conn.close()