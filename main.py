import yfinance as yf
from plyer import notification # 通知用ライブラリ

def check_stock_alert(ticker, name, target_price, direction="above"):
    """
    株価をチェックして、目標値を超えたら通知を出す関数
    direction: "above" (以上) または "below" (以下)
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    
    if data.empty:
        return
        
    current_price = data['Close'].iloc[-1]
    
    # 条件判定
    is_alert = False
    if direction == "above" and current_price >= target_price:
        is_alert = True
        msg = f"{target_price}円を超えました！ (現在: {current_price:.2f}円)"
    elif direction == "below" and current_price <= target_price:
        is_alert = True
        msg = f"{target_price}円を下回りました！ (現在: {current_price:.2f}円)"

    # 条件を満たしていたら、デスクトップ通知を飛ばす
    if is_alert:
        notification.notify(
            title=f"【株価アラート】{name}",
            message=msg,
            app_name="Stock Monitor",
            timeout=10 # 通知が表示される時間（秒）
        )
        print(f"!!! ALERT !!! {name}: {msg}")

# 実行例：トヨタが2500円以下になったら通知
check_stock_alert("7203.T", "トヨタ自動車", 2500, direction="below")

# 実行例：エヌビディアが130ドル以上になったら通知
check_stock_alert("NVDA", "エヌビディア", 130, direction="above")