import requests
from bs4 import BeautifulSoup
import time
import datetime
import yfinance as yf
from plyer import notification

# --- 設定：ここを自由に書き換えてください ---
WATCH_LIST = [
    {"ticker": "NVDA", "name": "エヌビディア", "limit": 5.0},  # 5%以上動いたら通知
    {"ticker": "7203.T", "name": "トヨタ", "limit": 3.0},      # 3%以上動いたら通知
    {"ticker": "9984.T", "name": "ソフトバンクG", "limit": 3.0}
]

# 通知の重複防止用（1時間制限）
last_alert_times = {}

def get_news():
    """ヤフーニュースのトップを取得"""
    url = "https://news.yahoo.co.jp/topics/top-picks"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        titles = [a.get_text(strip=True) for a in soup.find_all("a") if len(a.get_text(strip=True)) > 15][:5]
        return titles
    except:
        return ["ニュース取得失敗"]

def check_stock_movement():
    """株価の騰落をチェックして通知"""
    print(f"\n--- 騰落チェック: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    for item in WATCH_LIST:
        ticker = item["ticker"]
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="2d")
            if len(data) < 2: continue
            
            prev_close = data['Close'].iloc[-2]
            current_price = data['Close'].iloc[-1]
            change_percent = ((current_price - prev_close) / prev_close) * 100
            
            print(f"{item['name']}: {current_price:.2f}円 ({change_percent:+.2f}%)")

            # 判定ロジック
            is_alert = False
            status_msg = ""
            if change_percent <= -item["limit"]:
                is_alert = True
                status_msg = f"📉【急落】{change_percent:.2f}% 下落！"
            elif change_percent >= item["limit"]:
                is_alert = True
                status_msg = f"🚀【急騰】{change_percent:.2f}% 上昇！"

            if is_alert:
                now = datetime.datetime.now()
                last_time = last_alert_times.get(ticker)
                if last_time is None or (now - last_time).total_seconds() > 3600:
                    msg = f"{status_msg}\n{item['name']}: {current_price:.2f}円"
                    notification.notify(title="株価アラート", message=msg, timeout=10)
                    last_alert_times[ticker] = now
                    print(f"!!! 通知送信: {item['name']} !!!")
        except Exception as e:
            print(f"エラー({ticker}): {e}")

# --- メイン処理 ---
if __name__ == "__main__":
    print("=== システム起動：ニュース取得中 ===")
    news = get_news()
    for n in news:
        print(f"・{n}")
    
    print("\n株価の常時監視を開始します（終了は Ctrl + C）")
    try:
        while True:
            check_stock_movement()
            time.sleep(300) # 5分おきにチェック
    except KeyboardInterrupt:
        print("\n監視を終了しました。")