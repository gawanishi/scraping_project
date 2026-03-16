import yfinance as yf
import time
import datetime
from plyer import notification

# 監視したい銘柄の設定 (銘柄コード, 名前, 目標価格, 条件)
WATCH_LIST = [
    {"ticker": "NVDA", "name": "エヌビディア", "target": 130, "direction": "above"},
    {"ticker": "7203.T", "name": "トヨタ", "target": 2500, "direction": "below"},
]

def check_stocks():
    print(f"\n--- チェック開始: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    for item in WATCH_LIST:
        stock = yf.Ticker(item["ticker"])
        data = stock.history(period="1d")
        
        if data.empty:
            continue
            
        current_price = data['Close'].iloc[-1]
        print(f"{item['name']}: {current_price:.2f}")

        # 通知判定
        is_alert = False
        if item["direction"] == "above" and current_price >= item["target"]:
            is_alert = True
        elif item["direction"] == "below" and current_price <= item["target"]:
            is_alert = True

        if is_alert:
            notification.notify(
                title=f"【株価アラート】{item['name']}",
                message=f"目標価格に達しました: {current_price:.2f}",
                timeout=10
            )

# --- メインループ ---
print("株価監視ボットを起動しました（終了するには Ctrl + C を押してください）")

try:
    while True:
        check_stocks()
        
        # 300秒（5分）待機
        print("5分間待機します...")
        time.sleep(300) 
        
except KeyboardInterrupt:
    print("\n監視を終了しました。")