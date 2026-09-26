import requests
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SCHEDULE = os.environ.get("SCHEDULE", "")

TARGET_CHAIN = "Solana"

TVL_CHANGE_1H = 20
MIN_TVL = 1_000_000

FEE_CHANGE_1D = 20
MIN_FEE_24H = 10_000


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    res = requests.post(url, json=payload, timeout=10)
    print("Telegramの返事:", res.status_code, res.text)


def check_tvl_surges():
    print("DefiLlama TVLデータを取得中...")
    res = requests.get("https://api.llama.fi/protocols", timeout=30)
    protocols = res.json()

    alerts = []
    for p in protocols:
        if TARGET_CHAIN not in p.get("chains", []):
            continue

        name = p.get("name", "Unknown")
        slug = p.get("slug", "")
        tvl = p.get("tvl", 0) or 0
        change_1h = p.get("change_1h")
        category = p.get("category", "")

        if tvl < MIN_TVL:
            continue
        if change_1h is None or change_1h < TVL_CHANGE_1H:
            continue

        tvl_str = f"${tvl/1_000_000:.1f}M" if tvl >= 1_000_000 else f"${tvl:,.0f}"
        link = f"https://defillama.com/protocol/{slug}"
        msg = (
            f"🚀 <b>{name}</b>（TVL急増）\n"
            f"TVL: {tvl_str}\n"
            f"1h: <b>+{change_1h:.1f}%</b>\n"
            f"Category: {category}\n"
            f"<a href='{link}'>DefiLlamaで見る</a>"
        )
        alerts.append(msg)
    return alerts


def check_fee_surges():
    print("DefiLlama Feeデータを取得中...")
    url = f"https://api.llama.fi/overview/fees/{TARGET_CHAIN.lower()}"
    res = requests.get(url, timeout=30)
    data = res.json()
    protocols = data.get("protocols", [])

    alerts = []
    for p in protocols:
        name = p.get("name", "Unknown")
        slug = p.get("slug", "")
        total24h = p.get("total24h", 0) or 0
        change_1d = p.get("change_1d")
        category = p.get("category", "")

        if total24h < MIN_FEE_24H:
            continue
        if change_1d is None or change_1d < FEE_CHANGE_1D:
            continue

        fee_str = f"${total24h/1_000_000:.2f}M" if total24h >= 1_000_000 else f"${total24h:,.0f}"
        link = f"https://defillama.com/protocol/{slug}"
        msg = (
            f"💰 <b>{name}</b>（Fee急増）\n"
            f"24h Fee: {fee_str}\n"
            f"1d: <b>+{change_1d:.1f}%</b>\n"
            f"Category: {category}\n"
            f"<a href='{link}'>DefiLlamaで見る</a>"
        )
        alerts.append(msg)
    return alerts


def send_alerts(alerts, header_title):
    if not alerts:
        print("急増したプロトコルはありませんでした")
        return

    header = f"{header_title} ({datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC)\n\n"
    for alert in alerts[:5]:
        send_telegram(header + alert)
        header = ""
    print(f"{len(alerts)}件のアラートを送信しました")


def main():
    if SCHEDULE == "0 0 * * *":
        send_alerts(check_fee_surges(), "💰 Solana Fee急増アラート")
    elif SCHEDULE == "0 * * * *":
        send_alerts(check_tvl_surges(), "📊 Solana TVL急増アラート")
    else:
        send_alerts(check_tvl_surges(), "📊 Solana TVL急増アラート")
        send_alerts(check_fee_surges(), "💰 Solana Fee急増アラート")


if __name__ == "__main__":
    main()
