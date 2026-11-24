import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = "@aboutIslam313"
THREAD_ID = 7
STATE_FILE = "last_message.json"
TZ = ZoneInfo("Asia/Baghdad")

PRAYER_NAMES = {
    "Fajr": "الفجر",
    "Dhuhr": "الظهر",
    "Asr": "العصر",
    "Maghrib": "المغرب",
    "Isha": "العشاء",
}


def tg_request(method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_najaf_timings() -> dict:
    now = datetime.now(TZ)
    date_str = now.strftime("%d-%m-%Y")
    params = urllib.parse.urlencode({
        "city": "Najaf",
        "country": "Iraq",
        "method": 0,
    })
    url = f"https://api.aladhan.com/v1/timings/{date_str}?{params}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["data"]["timings"]


def main() -> None:
    now = datetime.now(TZ)
    current_hm = now.strftime("%H:%M")
    today_key = now.strftime("%Y-%m-%d")

    timings = get_najaf_timings()
    state = load_state()

    for eng_key, ar_name in PRAYER_NAMES.items():
        prayer_hm = timings[eng_key][:5]
        sent_key = f"{today_key}_{eng_key}"

        if current_hm >= prayer_hm and state.get("last_sent_key") != sent_key:
            old_msg_id = state.get("last_message_id")
            if old_msg_id:
                try:
                    tg_request(
                        "deleteMessage",
                        {"chat_id": CHAT_ID, "message_id": old_msg_id},
                    )
                except Exception:
                    pass

            text = (
                f"📢 حان الآن موعد أذان {ar_name} ({prayer_hm})\n"
                f"📍 حسب التوقيت المحلي لمدينة النجف الأشرف\n\n"
                f"🕌 اترك ما بيدك وأقبل على الصلاة؛ ففيها راحة القلب وطمأنينة النفس.\n"
                f"تقبّل الله منّا ومنكم صالح الأعمال."
            )

            res = tg_request(
                "sendMessage",
                {
                    "chat_id": CHAT_ID,
                    "message_thread_id": THREAD_ID,
                    "text": text,
                },
            )

            if res.get("ok"):
                state["last_message_id"] = res["result"]["message_id"]
                state["last_sent_key"] = sent_key
                save_state(state)
            break


if __name__ == "__main__":
    main()
