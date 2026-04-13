import io
import json
import os
import sys
from datetime import datetime, date, timezone

# 強制 stdout 使用 UTF-8，避免 Windows cp950 無法輸出 emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 本地端測試時，嘗試載入 .env 檔
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── 常數設定 ──────────────────────────────────────────────
START_DATE  = date(2026, 4, 12)   # 備考開始日
EXAM_DATE   = date(2026, 5, 23)   # 考試日
TOTAL_CARDS = 80

# UTC 小時 → Slot 編號（台灣時間 = UTC+8）
#   台灣 07:00 = UTC 23:00（前一天）→ slot 0
#   台灣 12:00 = UTC 04:00          → slot 1
#   台灣 17:00 = UTC 09:00          → slot 2
#   台灣 21:00 = UTC 13:00          → slot 3
SLOT_MAP = {23: 0, 4: 1, 9: 2, 13: 3}


def load_cards() -> list:
    """讀取 cards.json，回傳卡片列表。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cards_path = os.path.join(script_dir, "cards.json")
    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["cards"]


def get_slot() -> int:
    """
    根據當前 UTC 小時決定推播 slot（0-3）。
    若不在預定時間（例如本地手動測試），用 UTC 小時 mod 4 作為 fallback。
    """
    utc_hour = datetime.now(timezone.utc).hour
    if utc_hour in SLOT_MAP:
        return SLOT_MAP[utc_hour]
    # fallback：本地測試用，讓每次執行都能看到卡片
    return utc_hour % 4


def build_message(card: dict, days_left: int) -> str:
    """組合 LINE 推播訊息。"""
    subject = card["subject"]
    topic   = card["topic"]
    content = card["content"]

    emoji = "📘" if subject == "L21" else "📗"

    message = (
        f"╔══════════════════╗\n"
        f"{emoji} {subject} 考點速記\n"
        f"╚══════════════════╝\n"
        f"\n"
        f"【{topic}】\n"
        f"{content}\n"
        f"\n"
        f"🗓 距考試還有 {days_left} 天"
    )
    return message


def send_line_message(message: str, token: str, target_id: str) -> tuple:
    """
    透過 LINE Messaging API 發送 Push Message。
    target_id 可以是 User ID（U 開頭）或 Group ID（C 開頭）。
    回傳 (status_code, response_text)。
    """
    import requests  # 延遲 import，讓「邏輯測試」不依賴 requests

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    body = {
        "to": target_id,
        "messages": [
            {
                "type": "text",
                "text": message,
            }
        ],
    }
    resp = requests.post(url, headers=headers, json=body, timeout=10)
    return resp.status_code, resp.text


def do_push(message: str, token: str, targets: list[str]) -> bool:
    """對所有 target 發送訊息，全部成功才回傳 True。"""
    all_ok = True
    for target_id in targets:
        label = "群組" if target_id.startswith("C") else "個人"
        print(f"\n📤 發送至{label}（{target_id[:8]}…）")
        status_code, resp_text = send_line_message(message, token, target_id)
        print(f"   HTTP {status_code}")
        if status_code == 200:
            print(f"   ✅ 成功")
        else:
            print(f"   ❌ 失敗：{resp_text}")
            all_ok = False
    return all_ok


def main():
    # ── 讀取環境變數 ──────────────────────────────────────
    token    = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    user_id  = os.environ.get("LINE_USER_ID", "")
    group_id = os.environ.get("LINE_GROUP_ID", "")   # 選填，有設定才推播到群組

    # 決定推播對象（個人必填，群組選填）
    targets = [t for t in [user_id, group_id] if t]

    # ── 計算天數 ──────────────────────────────────────────
    today     = date.today()
    day_index = (today - START_DATE).days
    days_left = (EXAM_DATE - today).days

    # ── 考試已結束，直接停止 ──────────────────────────────
    if today > EXAM_DATE:
        print(f"  今天：{today}，考試已於 {EXAM_DATE} 結束，不推送。")
        sys.exit(0)

    # ── 選出本次卡片 ──────────────────────────────────────
    slot       = get_slot()
    card_index = (day_index * 4 + slot) % TOTAL_CARDS
    cards      = load_cards()
    card       = cards[card_index]
    message    = build_message(card, days_left)

    # ── 印出除錯資訊 ──────────────────────────────────────
    print("=" * 40)
    print(f"  今天：{today} | 距考試：{days_left} 天")
    print(f"  UTC 時間：{datetime.now(timezone.utc).strftime('%H:%M')}（Slot {slot}）")
    print(f"  卡片索引：{card_index}  →  {card['subject']} - {card['topic']}")
    print("=" * 40)
    print(message)
    print("=" * 40)

    # ── 發送 LINE 推播 ────────────────────────────────────
    if not token or not targets:
        print("\n⚠️  未設定 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID，跳過發送。")
        print("   本地端請建立 .env 檔案或執行：")
        print("   export LINE_CHANNEL_ACCESS_TOKEN=你的token")
        print("   export LINE_USER_ID=你的userID")
        print("   export LINE_GROUP_ID=群組ID（選填）")
        sys.exit(0)

    success = do_push(message, token, targets)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
