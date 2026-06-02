import schedule
import threading
from datetime import datetime
from linebot.models import FlexSendMessage, TextSendMessage


class MedScheduler:
    def __init__(self, db, line_bot_api):
        self.db = db
        self.line_bot_api = line_bot_api
        self._lock = threading.Lock()

    def start(self):
        self.reload()

    def reload(self):
        with self._lock:
            schedule.clear("med")
            meds = self.db.get_all_active_meds()
            seen = set()
            for med in meds:
                for t in med["times"].split(","):
                    t = t.strip()
                    key = f"{t}"
                    if key not in seen:
                        seen.add(key)
                        schedule.every().day.at(t, "Asia/Bangkok").do(

                            self._send_reminders_at, t
                        ).tag("med")

    def _send_reminders_at(self, target_time: str):
        meds = self.db.get_all_active_meds()
        # Group by user
        user_meds = {}
        for med in meds:
            for t in med["times"].split(","):
                if t.strip() == target_time:
                    user_id = med["user_id"]
                    if user_id not in user_meds:
                        user_meds[user_id] = []
                    user_meds[user_id].append(med)

        for user_id, meds_due in user_meds.items():
            self._push_reminder(user_id, meds_due, target_time)

    def _push_reminder(self, user_id: str, meds: list, time_str: str):
        from flex_messages import build_reminder
        try:
            self.line_bot_api.push_message(
                user_id,
                FlexSendMessage(
                    alt_text=f"⏰ ถึงเวลากินยา {time_str}",
                    contents=build_reminder(meds, time_str),
                ),
            )
        except Exception as e:
            print(f"[Scheduler] Error pushing to {user_id}: {e}")
