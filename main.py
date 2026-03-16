import yfinance as yf
import datetime
import time
from plyer import notification

# 監視リスト（銘柄コード、名前、下落率のしきい値）
WATCH_LIST = [
    {"ticker": "NVDA", "name": "エヌビディア", "drop_limit": -5.0}, # -5%
    {"ticker": "7203.T", "name": "トヨタ", "drop_limit": -3.0},   # -3%
]

last_alert_times = {}

def check_stock_drop():
    print(f"\n--- 騰落チェック: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    
    for item in WATCH_LIST:
        ticker = item["ticker"]
        stock = yf.Ticker(ticker)
        # 過去2日分のデータを取得（前日の終値を知るため）
        data = stock.history(period="2d")
        
        if len(data) < 2:
            print(f"{item['name']}: 比較データが足りません")
            continue
            
        prev_close = data['Close'].iloc[-2] # 前日の終値
        current_price = data['Close'].iloc[-1] # 現在の価格
        
        # 騰落率の計算: ((現在値 - 前日終値) / 前日終値) * 100
        change_percent = ((current_price - prev_close) / prev_close) * 100
        
        print(f"{item['name']}: {current_price:.2f}円 (前日比: {change_percent:+.2f}%)")

        # 通知判定: 設定した下落率（drop_limit）よりも大きく下がっていたら通知
        if change_percent <= item["drop_limit"]:
            now = datetime.datetime.now()
            last_time = last_alert_times.get(ticker)

            # 1時間以内の重複通知を避ける
            if last_time is None or (now - last_time).total_seconds() > 3600:
                msg = f"【急落アラート】\n{item['name']}が前日比 {change_percent:.2f}% 下落しました！\n現在値: {current_price:.2f}円"
                
                notification.notify(title="株価急落アラート", message=msg, timeout=10)
                # もしDiscordやLINEを作ったらここに送信関数を入れる
                
                last_alert_times[ticker] = now
                print(f"!!! アラート送信完了: {item['name']} !!!")

# メインループ
try:
    while True:
        check_stock_drop()
        time.sleep(300) 
except KeyboardInterrupt:
    print("\n監視終了")