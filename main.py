import yfinance as yf
import time
import datetime
from plyer import notification

# 監視設定
WATCH_LIST = [
    {"ticker": "NVDA", "name": "エヌビディア", "target": 130, "direction": "above"},
    {"ticker": "7203.T", "name": "トヨタ", "target": 2500, "direction": "below"},
]

# 各銘柄の「最後に通知した時間」を記録する辞書（最初は空っぽ）
last_alert_times = {}

def check_stocks():
    print(f"\n--- チェック開始: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    for item in WATCH_LIST:
        ticker = item["ticker"]
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        
        if data.empty:
            continue
            
        current_price = data['Close'].iloc[-1]
        print(f"{item['name']}: {current_price:.2f}")

        # 通知が必要かどうかの判定
        is_alert_condition = False
        if item["direction"] == "above" and current_price >= item["target"]:
            is_alert_condition = True
        elif item["direction"] == "below" and current_price <= item["target"]:
            is_alert_condition = True

        if is_alert_condition:
            # --- 【追加】前回の通知から1時間（3600秒）経っているか確認 ---
            now = datetime.datetime.now()
            last_time = last_alert_times.get(ticker) # 過去の通知時間を取得

            # 初めての通知、または前回の通知から3600秒以上経過していたら実行
            if last_time is None or (now - last_time).total_seconds() > 3600:
                notification.notify(
                    title=f"【株価アラート】{item['name']}",
                    message=f"目標価格に達しました: {current_price:.2f}",
                    timeout=10
                )
                # 通知した時間を記録（更新）
                last_alert_times[ticker] = now
                print(f"!!! 通知を送信しました: {item['name']} !!!")
            else:
                # 1時間以内なので、条件は満たしているが通知はスキップ
                print(f"（{item['name']}は条件を満たしていますが、1時間以内のため通知をスキップします）")

# --- メインループ (変更なし) ---
try:
    while True:
        check_stocks()
        time.sleep(300) 
except KeyboardInterrupt:
    print("\n監視を終了しました。")