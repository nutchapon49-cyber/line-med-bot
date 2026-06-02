"""
Flex Message builders for the medication reminder Line Bot.
All functions return Flex Message container dicts.
"""

# ─────────────────────────────────────────────
# Color palette
# ─────────────────────────────────────────────
GREEN = "#1D9E75"
BLUE = "#378ADD"
AMBER = "#BA7517"
RED = "#A32D2D"
GRAY = "#888780"
BG_GREEN = "#E1F5EE"
BG_BLUE = "#E6F1FB"
BG_AMBER = "#FAEEDA"
BG_GRAY = "#F1EFE8"
TEXT_DARK = "#2C2C2A"
TEXT_MID = "#5F5E5A"
TEXT_LIGHT = "#888780"


# ─────────────────────────────────────────────
# Main Menu
# ─────────────────────────────────────────────
def build_main_menu():
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BG_GREEN,
            "paddingAll": "20px",
            "contents": [
                {"type": "text", "text": "💊 แจ้งเตือนกินยา", "weight": "bold", "size": "xl", "color": "#085041"},
                {"type": "text", "text": "ไม่ลืมกินยาอีกต่อไป", "size": "sm", "color": "#0F6E56", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "16px",
            "contents": [
                _menu_btn("💊 เพิ่มยาใหม่", "action=add", GREEN),
                _menu_btn("📋 รายการยาของฉัน", "action=list", BLUE),
                _menu_btn("📖 ประวัติการกินยา", "action=history", AMBER),
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": 'พิมพ์ "ช่วยเหลือ" เพื่อดูคำสั่งทั้งหมด',
                 "size": "xs", "color": TEXT_LIGHT, "align": "center"},
            ],
        },
    }


def _menu_btn(label, postback_data, color):
    return {
        "type": "button",
        "style": "primary",
        "color": color,
        "action": {"type": "postback", "label": label, "data": postback_data},
        "height": "sm",
    }


# ─────────────────────────────────────────────
# Add medication guide (step by step)
# ─────────────────────────────────────────────
STEPS = {
    "name":  ("1/4", "ชื่อยา", "พิมพ์ชื่อยาที่ต้องการเพิ่มครับ\nเช่น Paracetamol, Metformin"),
    "dose":  ("2/4", "ขนาดและวิธีกิน", "พิมพ์ขนาดและวิธีกินครับ\nเช่น 500mg หลังอาหาร"),
    "times": ("3/4", "เวลากินยา", "พิมพ์เวลา (24 ชม.) คั่นด้วยลูกน้ำครับ\nเช่น 08:00, 12:00, 20:00"),
    "notes": ("4/4", "หมายเหตุ (ถ้ามี)", 'พิมพ์หมายเหตุเพิ่มเติม หรือพิมพ์ "ข้าม" เพื่อข้ามครับ'),
}


def build_add_guide(step: str, name: str = ""):
    prog, title, desc = STEPS[step]
    header_text = f"เพิ่มยาใหม่ — ขั้นตอนที่ {prog}"
    if name:
        header_text += f"\n💊 {name}"
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BG_BLUE,
            "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "เพิ่มยาใหม่", "weight": "bold", "size": "lg", "color": "#0C447C"},
                {"type": "text", "text": f"ขั้นตอนที่ {prog}", "size": "sm", "color": "#185FA5", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "size": "md", "color": TEXT_DARK},
                {"type": "text", "text": desc, "size": "sm", "color": TEXT_MID, "wrap": True},
                {"type": "separator", "margin": "md"},
                {"type": "text",
                 "text": "👆 พิมพ์ข้อมูลในกล่องข้อความด้านล่างครับ",
                 "size": "xs", "color": TEXT_LIGHT, "wrap": True, "margin": "sm"},
            ],
        },
    }


# ─────────────────────────────────────────────
# Medication list
# ─────────────────────────────────────────────
def build_med_list(meds: list):
    if not meds:
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "24px",
                "contents": [
                    {"type": "text", "text": "💊", "size": "3xl", "align": "center"},
                    {"type": "text", "text": "ยังไม่มียาในระบบ", "align": "center",
                     "color": TEXT_MID, "margin": "md"},
                    {"type": "button", "style": "primary", "color": GREEN,
                     "action": {"type": "postback", "label": "เพิ่มยาเลย", "data": "action=add"},
                     "margin": "lg"},
                ],
            },
        }

    bubbles = [_med_bubble(m) for m in meds]
    if len(bubbles) == 1:
        return bubbles[0]
    return {"type": "carousel", "contents": bubbles}


def _med_bubble(med: dict):
    status_color = GREEN if med["active"] else GRAY
    status_text = "เปิดใช้งาน" if med["active"] else "ปิดใช้งาน"
    times = med["times"].replace(",", "  •  ")

    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BG_GREEN if med["active"] else BG_GRAY,
            "paddingAll": "14px",
            "contents": [
                {
                    "type": "box", "layout": "horizontal", "contents": [
                        {"type": "text", "text": med["name"], "weight": "bold",
                         "size": "lg", "color": "#085041" if med["active"] else TEXT_DARK, "flex": 1},
                        {"type": "text", "text": status_text, "size": "xs",
                         "color": status_color, "align": "end", "gravity": "center"},
                    ]
                },
                {"type": "text", "text": med.get("dose") or "—",
                 "size": "sm", "color": TEXT_MID, "margin": "xs"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "14px",
            "contents": [
                _row("⏰ เวลา", times),
                _row("📝 หมายเหตุ", med.get("notes") or "—"),
            ],
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "paddingAll": "12px",
            "contents": [
                {
                    "type": "button", "style": "secondary", "height": "sm", "flex": 1,
                    "action": {"type": "postback",
                               "label": "ปิด" if med["active"] else "เปิด",
                               "data": f"action=toggle&id={med['id']}"},
                },
                {
                    "type": "button", "style": "secondary", "height": "sm", "flex": 1,
                    "action": {"type": "postback", "label": "ลบ",
                               "data": f"action=delete&id={med['id']}"},
                },
            ],
        },
    }


def _row(label: str, value: str):
    return {
        "type": "box", "layout": "horizontal", "spacing": "sm",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": TEXT_LIGHT, "flex": 2},
            {"type": "text", "text": value, "size": "sm", "color": TEXT_DARK,
             "flex": 3, "wrap": True},
        ],
    }


# ─────────────────────────────────────────────
# Reminder push (sent at scheduled time)
# ─────────────────────────────────────────────
def build_reminder(meds: list, time_str: str):
    med_items = []
    for med in meds:
        med_items.append({
            "type": "box", "layout": "vertical", "spacing": "xs",
            "paddingAll": "12px",
            "backgroundColor": BG_GREEN,
            "cornerRadius": "8px",
            "contents": [
                {"type": "text", "text": f"💊 {med['name']}", "weight": "bold",
                 "size": "md", "color": "#085041"},
                {"type": "text", "text": med.get("dose") or "", "size": "sm",
                 "color": "#0F6E56"},
                {
                    "type": "box", "layout": "horizontal", "spacing": "sm", "margin": "sm",
                    "contents": [
                        {
                            "type": "button", "style": "primary", "height": "sm",
                            "color": GREEN, "flex": 1,
                            "action": {"type": "postback", "label": "✅ กินแล้ว",
                                       "data": f"action=confirm&id={med['id']}"},
                        },
                        {
                            "type": "button", "style": "secondary", "height": "sm", "flex": 1,
                            "action": {"type": "postback", "label": "⏭️ ข้าม",
                                       "data": f"action=skip&id={med['id']}"},
                        },
                    ],
                },
            ],
        })

    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": GREEN,
            "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": f"⏰ ถึงเวลากินยาแล้ว!", "weight": "bold",
                 "size": "lg", "color": "#ffffff"},
                {"type": "text", "text": f"เวลา {time_str} น.", "size": "sm",
                 "color": "#9FE1CB"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "14px",
            "contents": med_items,
        },
    }


# ─────────────────────────────────────────────
# Medication detail
# ─────────────────────────────────────────────
def build_med_detail(med: dict):
    times_list = med["times"].split(",")
    time_boxes = [
        {"type": "text", "text": f"• {t.strip()}", "size": "sm", "color": TEXT_DARK}
        for t in times_list
    ]
    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": BG_BLUE, "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": med["name"], "weight": "bold",
                 "size": "xl", "color": "#0C447C"},
                {"type": "text", "text": med.get("dose") or "—",
                 "size": "sm", "color": "#185FA5", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "md", "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "⏰ เวลากินยา", "weight": "bold",
                 "size": "sm", "color": TEXT_MID},
                *time_boxes,
                {"type": "separator", "margin": "md"},
                _row("📝 หมายเหตุ", med.get("notes") or "—"),
                _row("📅 เพิ่มเมื่อ", med.get("created_at", "—")[:10]),
                _row("สถานะ", "เปิดใช้งาน" if med["active"] else "ปิดใช้งาน"),
            ],
        },
        "footer": {
            "type": "box", "layout": "horizontal",
            "spacing": "sm", "paddingAll": "12px",
            "contents": [
                {
                    "type": "button", "style": "primary", "color": RED,
                    "action": {"type": "postback", "label": "🗑️ ลบยานี้",
                               "data": f"action=delete&id={med['id']}"},
                },
            ],
        },
    }


# ─────────────────────────────────────────────
# History log
# ─────────────────────────────────────────────
def build_history(logs: list):
    if not logs:
        return {
            "type": "bubble",
            "body": {
                "type": "box", "layout": "vertical", "paddingAll": "24px",
                "contents": [
                    {"type": "text", "text": "📖", "size": "3xl", "align": "center"},
                    {"type": "text", "text": "ยังไม่มีประวัติการกินยา", "align": "center",
                     "color": TEXT_MID, "margin": "md"},
                ],
            },
        }

    rows = []
    for log in logs:
        icon = "✅" if log["status"] == "taken" else "⏭️"
        color = GREEN if log["status"] == "taken" else GRAY
        dt = log["logged_at"][:16].replace("T", " ")
        rows.append({
            "type": "box", "layout": "horizontal", "spacing": "sm",
            "paddingAll": "8px",
            "contents": [
                {"type": "text", "text": icon, "flex": 0, "size": "sm"},
                {"type": "text", "text": log["med_name"], "flex": 2,
                 "size": "sm", "color": TEXT_DARK},
                {"type": "text", "text": dt, "flex": 3, "size": "xs",
                 "color": TEXT_LIGHT, "align": "end"},
            ],
        })

    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": BG_AMBER, "paddingAll": "14px",
            "contents": [
                {"type": "text", "text": "📖 ประวัติการกินยา", "weight": "bold",
                 "size": "lg", "color": "#633806"},
                {"type": "text", "text": f"{len(logs)} รายการล่าสุด",
                 "size": "sm", "color": "#854F0B", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "none", "paddingAll": "8px",
            "contents": rows,
        },
    }
