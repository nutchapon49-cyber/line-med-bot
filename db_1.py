import os
import json
import psycopg2
import psycopg2.extras


class Database:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        self._init()

    def _conn(self):
        return psycopg2.connect(self.db_url, sslmode="require")

    def _init(self):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT NOW(),
                        state TEXT,
                        temp_data TEXT
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS medications (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        dose TEXT,
                        times TEXT NOT NULL,
                        notes TEXT,
                        active INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS med_logs (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        med_id INTEGER NOT NULL,
                        med_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        logged_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sent_reminders (
                        id SERIAL PRIMARY KEY,
                        med_id INTEGER NOT NULL,
                        sent_date TEXT NOT NULL,
                        sent_time TEXT NOT NULL,
                        UNIQUE (med_id, sent_date, sent_time)
                    );
                """)
            conn.commit()

    # --- Users ---
    def add_user(self, user_id):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
                    (user_id,),
                )
            conn.commit()

    def get_state(self, user_id):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT state FROM users WHERE user_id=%s", (user_id,))
                row = cur.fetchone()
                return row[0] if row else None

    def set_state(self, user_id, state):
        self.add_user(user_id)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET state=%s WHERE user_id=%s", (state, user_id))
            conn.commit()

    def clear_state(self, user_id):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET state=NULL, temp_data=NULL WHERE user_id=%s", (user_id,))
            conn.commit()

    def set_temp(self, user_id, key, value):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT temp_data FROM users WHERE user_id=%s", (user_id,))
                row = cur.fetchone()
                data = json.loads(row[0]) if row and row[0] else {}
                data[key] = value
                cur.execute(
                    "UPDATE users SET temp_data=%s WHERE user_id=%s",
                    (json.dumps(data, ensure_ascii=False), user_id),
                )
            conn.commit()

    def get_temp(self, user_id):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT temp_data FROM users WHERE user_id=%s", (user_id,))
                row = cur.fetchone()
                return json.loads(row[0]) if row and row[0] else {}

    # --- Medications ---
    def add_med(self, user_id, name, dose, times, notes):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO medications (user_id, name, dose, times, notes) "
                    "VALUES (%s,%s,%s,%s,%s) RETURNING id",
                    (user_id, name, dose, times, notes),
                )
                med_id = cur.fetchone()[0]
            conn.commit()
            return med_id

    def get_meds(self, user_id):
        with self._conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM medications WHERE user_id=%s ORDER BY created_at DESC",
                    (user_id,),
                )
                return [dict(r) for r in cur.fetchall()]

    def get_med(self, med_id):
        with self._conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM medications WHERE id=%s", (med_id,))
                row = cur.fetchone()
                return dict(row) if row else {}

    def get_all_active_meds(self):
        with self._conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM medications WHERE active=1")
                return [dict(r) for r in cur.fetchall()]

    def delete_med(self, med_id):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM medications WHERE id=%s", (med_id,))
            conn.commit()

    def toggle_med(self, med_id):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE medications SET active = CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=%s",
                    (med_id,),
                )
            conn.commit()

    # --- Logs ---
    def log_taken(self, user_id, med_id):
        med = self.get_med(med_id)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO med_logs (user_id, med_id, med_name, status) VALUES (%s,%s,%s,%s)",
                    (user_id, med_id, med.get("name", "?"), "taken"),
                )
            conn.commit()

    def log_skipped(self, user_id, med_id):
        med = self.get_med(med_id)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO med_logs (user_id, med_id, med_name, status) VALUES (%s,%s,%s,%s)",
                    (user_id, med_id, med.get("name", "?"), "skipped"),
                )
            conn.commit()

    def get_history(self, user_id, limit=10):
        with self._conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM med_logs WHERE user_id=%s ORDER BY logged_at DESC LIMIT %s",
                    (user_id, limit),
                )
                return [dict(r) for r in cur.fetchall()]

    # --- Reminder de-duplication ---
    def already_sent(self, med_id, date_str, time_str):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM sent_reminders WHERE med_id=%s AND sent_date=%s AND sent_time=%s",
                    (med_id, date_str, time_str),
                )
                return cur.fetchone() is not None

    def mark_sent(self, med_id, date_str, time_str):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sent_reminders (med_id, sent_date, sent_time) "
                    "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                    (med_id, date_str, time_str),
                )
            conn.commit()
