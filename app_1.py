import os
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, PostbackEvent, FollowEvent
)

from db import Database
from flex_messages import (
    build_main_menu, build_med_list, build_add_guide,
    build_history, build_med_detail, build_reminder
)

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "YOUR_SECRET")
TZ = ZoneInfo("Asia/Bangkok")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

db = Database()


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    db.add_user(user_id)
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text="💊 สวัสดีครับ! ยินดีต้อนรับสู่บอทแจ้งเตือนกินยา\n\nระบบนี้จะช่วยให้คุณไม่ลืมกินยาอีกต่อไปครับ 🎉"),
            FlexSendMessage(alt_text="เมนูหลัก", contents=build_main_menu()),
        ],
    )


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    state = db.get_state(user_id)

    # --- State machine for adding medication ---
    if state and state.startswith("ADD:"):
        handle_add_state(event, user_id, text, state)
        return

    # --- Commands ---
    if text in ["เมนู", "menu", "หน้าแรก"]:
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="เมนูหลัก", contents=build_main_menu()),
        )

    elif text in ["รายการยา", "ยาของฉัน"]:
        meds = db.get_meds(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="รายการยา", contents=build_med_list(meds)),
        )

    elif text in ["เพิ่มยา", "เพิ่ม"]:
        db.set_state(user_id, "ADD:name")
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="เพิ่มยา", contents=build_add_guide("name")),
        )

    elif text in ["ประวัติ", "history"]:
        logs = db.get_history(user_id, limit=10)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="ประวัติการกินยา", contents=build_history(logs)),
        )

    elif text in ["ช่วยเหลือ", "help", "วิธีใช้"]:
        help_text = (
            "📋 คำสั่งที่ใช้ได้:\n\n"
            "💊 เพิ่มยา — เพิ่มยาใหม่\n"
            "📋 รายการยา — ดูยาทั้งหมด\n"
            "📖 ประวัติ — ดูประวัติการกินยา\n"
            "🏠 เมนู — กลับหน้าหลัก\n\n"
            "เมื่อถึงเวลา บอทจะส่งการแจ้งเตือนให้อัตโนมัติครับ ✅"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))

    else:
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text='พิมพ์ "เมนู" เพื่อดูตัวเลือกครับ 😊'),
                FlexSendMessage(alt_text="เมนูหลัก", contents=build_main_menu()),
            ],
        )


def handle_add_state(event, user_id, text, state):
    step = state.split("ADD:")[1]

    if step == "name":
        db.set_temp(user_id, "name", text)
        db.set_state(user_id, "ADD:dose")
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="เพิ่มยา", contents=build_add_guide("dose", name=text)),
        )

    elif step == "dose":
        db.set_temp(user_id, "dose", text)
        db.set_state(user_id, "ADD:times")
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="เพิ่มยา", contents=build_add_guide("times")),
        )

    elif step == "times":
        # Parse times like "08:00, 12:00, 20:00"
        raw = [t.strip() for t in text.replace(" ", "").split(",")]
        valid_times = []
        for t in raw:
            try:
                datetime.strptime(t, "%H:%M")
                valid_times.append(t)
            except ValueError:
                pass

        if not valid_times:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ รูปแบบเวลาไม่ถูกต้อง กรุณาพิมพ์ใหม่ เช่น 08:00, 12:00, 20:00"),
            )
            return

        db.set_temp(user_id, "times", ",".join(valid_times))
        db.set_state(user_id, "ADD:notes")
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="เพิ่มยา", contents=build_add_guide("notes")),
        )

    elif step == "notes":
        notes = text if text not in ["ข้าม", "-", "skip"] else ""
        temp = db.get_temp(user_id)
        med_id = db.add_med(
            user_id,
            name=temp["name"],
            dose=temp["dose"],
            times=temp["times"],
            notes=notes,
        )
        db.clear_state(user_id)

        times_list = temp["times"].replace(",", ", ")
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(
                    text=f"✅ เพิ่มยาสำเร็จ!\n\n"
                         f"💊 {temp['name']}\n"
                         f"📌 {temp['dose']}\n"
                         f"⏰ {times_list}\n"
                         f"{'📝 ' + notes if notes else ''}\n\n"
                         f"บอทจะแจ้งเตือนตามเวลาที่กำหนดครับ 🔔"
                ),
                FlexSendMessage(alt_text="เมนูหลัก", contents=build_main_menu()),
            ],
        )


@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    data = event.postback.data

    if data == "action=menu":
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="เมนูหลัก", contents=build_main_menu()),
        )

    elif data == "action=add":
        db.set_state(user_id, "ADD:name")
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="เพิ่มยา", contents=build_add_guide("name")),
        )

    elif data == "action=list":
        meds = db.get_meds(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="รายการยา", contents=build_med_list(meds)),
        )

    elif data == "action=history":
        logs = db.get_history(user_id, limit=10)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="ประวัติ", contents=build_history(logs)),
        )

    elif data.startswith("action=confirm&id="):
        med_id = int(data.split("id=")[1])
        db.log_taken(user_id, med_id)
        med = db.get_med(med_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"✅ บันทึกแล้ว! คุณกิน {med['name']} เรียบร้อยครับ 💪"),
        )

    elif data.startswith("action=skip&id="):
        med_id = int(data.split("id=")[1])
        db.log_skipped(user_id, med_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⏭️ บันทึกแล้ว ข้ามมื้อนี้"),
        )

    elif data.startswith("action=delete&id="):
        med_id = int(data.split("id=")[1])
        med = db.get_med(med_id)
        db.delete_med(med_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"🗑️ ลบยา {med['name']} แล้วครับ"),
        )

    elif data.startswith("action=toggle&id="):
        med_id = int(data.split("id=")[1])
        db.toggle_med(med_id)
        meds = db.get_meds(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text="รายการยา", contents=build_med_list(meds)),
        )

    elif data.startswith("action=detail&id="):
        med_id = int(data.split("id=")[1])
        med = db.get_med(med_id)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text=med["name"], contents=build_med_detail(med)),
        )


@app.route("/")
def health():
    return "OK", 200


@app.route("/check-reminders")
def check_reminders():
    """
    Called by an external cron (cron-job.org) every minute.
    Checks the current time against all active medication times,
    sends a reminder for any match, and records it so it won't
    be sent twice. This is resilient to server restarts because
    everything is read from the database, not memory.
    """
    now = datetime.now(TZ)
    current_time = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")

    meds = db.get_all_active_meds()

    # Group medications that are due right now, by user
    user_meds = {}
    for med in meds:
        for t in med["times"].split(","):
            if t.strip() == current_time:
                if db.already_sent(med["id"], today, current_time):
                    continue  # skip duplicates
                user_meds.setdefault(med["user_id"], []).append(med)

    sent_count = 0
    for user_id, meds_due in user_meds.items():
        try:
            line_bot_api.push_message(
                user_id,
                FlexSendMessage(
                    alt_text=f"⏰ ถึงเวลากินยา {current_time}",
                    contents=build_reminder(meds_due, current_time),
                ),
            )
            for med in meds_due:
                db.mark_sent(med["id"], today, current_time)
            sent_count += len(meds_due)
        except Exception as e:
            print(f"[check-reminders] push error to {user_id}: {e}")

    return {"time": current_time, "sent": sent_count}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
