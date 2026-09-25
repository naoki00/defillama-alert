import requests
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

TVL_CHANGE_1H = 15
TVL_CHANGE_1D = 30
MIN_TVL = 1_000_000

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    requests.post(url, json=payload, timeout=10)

def check_tvl_surges():
    print("DefiLlamaデータを取得中...")
    res = requests.get("https://api.llama.fi/protocols", timeout=30)
    protocols = res.json()

    alerts = []

    for p in protocols:
        name = p.get("name", "Unknown")
        slug = p.get("slug", "")
        tvl = p.get("tvl", 0) or 0
        change_1h = p.get("change_1h")
        change_1d = p.get("change_1d")
        category = p.get("category", "")

        if tvl < MIN_TVL:
            continue
        if change_1h is None and change_1d is None:
            continue

        triggered = False
        reasons = []

        if change_1h is not None and change_1h >= TVL_CHANGE_1H:
            triggered = True
            reasons.append(f"1h: <b>+{change_1h:.1f}%</b>")

        if change_1d is not None and change_1d >= TVL_CHANGE_1D:
            triggered = True
            reasons.append(f"1d: <b>+{change_1d:.1f}%</b>")

        if triggered:
            tvl_str = f"${tvl/1_000_000:.1f}M" if tvl >= 1_000_000 else f"${tvl:,.0f}"
            link = f"https://defillama.com/protocol/{slug}"
            msg = (
                f"🚀 <b>{name}</b>\n"
                f"TVL: {tvl_str}\n"
                f"{' / '.join(reasons)}\n"
                f"Category: {category}\n"
                f"<a href='{link}'>DefiLlamaで見る</a>"
            )
            alerts.append(msg)

    if alerts:
        header = f"📊 DefiLlama TVL急増アラート ({datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC)\n\n"
        for alert in alerts[:10]:
            send_telegram(header + alert)
            header = ""
        print(f"{len(alerts)}件のアラートを送信しました")
    else:
        print("急増したプロトコルはありませんでした")
        # テスト用に必ず1通送る
        send_telegram("✅ テスト成功！システムは正常に動作しています。")

if __name__ == "__main__":
    check_tvl_surges()
