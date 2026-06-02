import sqlite3
import json
from datetime import datetime


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init()

    def _conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    state TEXT,
                    temp_data TEXT
                );

                CREATE TABLE IF NOT EXISTS medications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    dose TEXT,
                    times TEXT NOT NULL,
                    notes TEXT,
                    active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS med_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    med_id INTEGER NOT NULL,
                    med_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    logged_at TEXT DEFAULT (datetime('now','localtime'))
                );
            """)

    # --- Users ---
    def add_user(self, user_id: str):
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
            )

    def get_state(self, user_id: str):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT state FROM users WHERE user_id=?", (user_id,)
            ).fetchone()
            return row["state"] if row else None

    def set_state(self, user_id: str, state: str):
        self.add_user(user_id)
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET state=? WHERE user_id=?", (state, user_id)
            )

    def clear_state(self, user_id: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET state=NULL, temp_data=NULL WHERE user_id=?",
                (user_id,),
            )

    def set_temp(self, user_id: str, key: str, value: str):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT temp_data FROM users WHERE user_id=?", (user_id,)
            ).fetchone()
            data = json.loads(row["temp_data"] or "{}") if row else {}
            data[key] = value
            conn.execute(
                "UPDATE users SET temp_data=? WHERE user_id=?",
                (json.dumps(data, ensure_ascii=False), user_id),
            )

    def get_temp(self, user_id: str) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT temp_data FROM users WHERE user_id=?", (user_id,)
            ).fetchone()
            return json.loads(row["temp_data"] or "{}") if row else {}

    # --- Medications ---
    def add_med(self, user_id: str, name: str, dose: str, times: str, notes: str) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO medications (user_id, name, dose, times, notes) VALUES (?,?,?,?,?)",
                (user_id, name, dose, times, notes),
            )
            return cur.lastrowid

    def get_meds(self, user_id: str) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM medications WHERE user_id=? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_med(self, med_id: int) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM medications WHERE id=?", (med_id,)
            ).fetchone()
            return dict(row) if row else {}

    def get_all_active_meds(self) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM medications WHERE active=1"
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_med(self, med_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM medications WHERE id=?", (med_id,))

    def toggle_med(self, med_id: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE medications SET active = CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=?",
                (med_id,),
            )

    # --- Logs ---
    def log_taken(self, user_id: str, med_id: int):
        med = self.get_med(med_id)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO med_logs (user_id, med_id, med_name, status) VALUES (?,?,?,?)",
                (user_id, med_id, med.get("name", "?"), "taken"),
            )

    def log_skipped(self, user_id: str, med_id: int):
        med = self.get_med(med_id)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO med_logs (user_id, med_id, med_name, status) VALUES (?,?,?,?)",
                (user_id, med_id, med.get("name", "?"), "skipped"),
            )

    def get_history(self, user_id: str, limit: int = 10) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM med_logs WHERE user_id=? ORDER BY logged_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
