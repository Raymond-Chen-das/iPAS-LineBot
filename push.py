import io
import json
import os
import sys
from datetime import date, datetime, timezone

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
TOTAL_CARDS = 20                  # 20 題模擬題，每天 1 題


def load_cards() -> list:
    """讀取 cards.json，回傳卡片列表。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cards_path = os.path.join(script_dir, "cards.json")
    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["cards"]


def build_message(card: dict, days_left: int) -> str:
    """組合 LINE 推播訊息。"""
    topic   = card["topic"]
    content = card["content"]

    message = (
        f"╔══════════════════╗\n"
        f"📘 L21 模擬題特訓\n"
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


def do_push(message: str, token: str, targets: list) -> bool:
    """對所有 target 發送訊息。遇到月配額已滿時跳過不視為失敗。"""
    all_ok = True
    for target_id in targets:
        label = "群組" if target_id.startswith("C") else "個人"
        print(f"\n📤 發送至{label}（{target_id[:8]}…）")
        status_code, resp_text = send_line_message(message, token, target_id)
        print(f"   HTTP {status_code}")
        if status_code == 200:
            print(f"   ✅ 成功")
            continue

        # 非 200：判斷是否為月配額已滿
        try:
            err_msg = json.loads(resp_text).get("message", "")
        except Exception:
            err_msg = ""
        if "monthly limit" in err_msg:
            print(f"   ⚠️  月配額已滿，跳過{label}推播")
            continue

        print(f"   ❌ 失敗：{resp_text}")
        all_ok = False
    return all_ok


def main():
    # ── 讀取環境變數 ──────────────────────────────────────
    token    = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    user_id  = os.environ.get("LINE_USER_ID", "")
    group_id = os.environ.get("LINE_GROUP_ID", "")   # 選填，有設定才推播到群組

    targets = [t for t in [user_id, group_id] if t]

    # ── 計算天數 ──────────────────────────────────────────
    today     = date.today()
    day_index = (today - START_DATE).days
    days_left = (EXAM_DATE - today).days

    # ── 考試已結束，直接停止 ──────────────────────────────
    if today > EXAM_DATE:
        print(f"  今天：{today}，考試已於 {EXAM_DATE} 結束，不推送。")
        sys.exit(0)

    # ── 選出本次卡片（每天一題） ──────────────────────────
    card_index = max(day_index, 0) % TOTAL_CARDS
    cards      = load_cards()
    card       = cards[card_index]
    message    = build_message(card, days_left)

    print("=" * 40)
    print(f"  今天：{today} | 距考試：{days_left} 天")
    print(f"  UTC 時間：{datetime.now(timezone.utc).strftime('%H:%M')}")
    print(f"  卡片索引：{card_index}  →  {card['topic']}")
    print("=" * 40)
    print(message)
    print("=" * 40)

    # ── 發送 LINE 推播 ────────────────────────────────────
    if not token or not targets:
        print("\n⚠️  未設定 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID，跳過發送。")
        sys.exit(0)

    success = do_push(message, token, targets)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
