import requests
from bs4 import BeautifulSoup
import time
import datetime
import yfinance as yf
import csv
import matplotlib.pyplot as plt # グラフ用
from plyer import notification

# --- 設定：CSV読み込み ---
def load_settings():
    watch_list = []
    try:
        with open('stocks.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                watch_list.append({
                    "ticker": row["ticker"],
                    "name": row["name"],
                    "limit": float(row["limit"])
                })
        return watch_list
    except FileNotFoundError:
        print("エラー: stocks.csv が見つかりません")
        return []

def get_news():
    url = "https://news.yahoo.co.jp/topics/top-picks"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        titles = [a.get_text(strip=True) for a in soup.find_all("a") if len(a.get_text(strip=True)) > 15][:5]
        return titles
    except: return ["ニュース取得失敗"]

# --- 3. グラフ保存機能 ---
def save_chart(ticker, name):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo") # 1ヶ月分
        plt.figure(figsize=(8, 4))
        plt.plot(hist['Close'], color='blue', label='Price')
        plt.title(f"{name} ({ticker}) - 1 Month")
        plt.grid(True)
        filename = f"{ticker}_chart.png"
        plt.savefig(filename)
        plt.close()
        print(f"📊 チャートを保存しました: {filename}")
    except Exception as e:
        print(f"チャート作成エラー: {e}")

# 通知の重複防止
last_alert_times = {}

def check_stock_movement(watch_list):
    print(f"\n--- 騰落チェック: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    summary = [] # 定期報告用
    
    for item in watch_list:
        ticker = item["ticker"]
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="2d")
            if len(data) < 2: continue
            
            prev_close = data['Close'].iloc[-2]
            current_price = data['Close'].iloc[-1]
            change_percent = ((current_price - prev_close) / prev_close) * 100
            
            print(f"{item['name']}: {current_price:.2f}円 ({change_percent:+.2f}%)")
            summary.append(f"{item['name']}: {current_price:.2f}円")

            # 判定
            is_alert = False
            if change_percent <= -item["limit"]:
                is_alert, status = True, "📉【急落】"
            elif change_percent >= item["limit"]:
                is_alert, status = True, "🚀【急騰】"

            if is_alert:
                now = datetime.datetime.now()
                if ticker not in last_alert_times or (now - last_alert_times[ticker]).total_seconds() > 3600:
                    msg = f"{status}{change_percent:.2f}%\n{item['name']}: {current_price:.2f}円"
                    notification.notify(title="株価アラート", message=msg, timeout=10)
                    save_chart(ticker, item['name']) # ここでグラフ保存！
                    last_alert_times[ticker] = now
        except Exception as e:
            print(f"エラー({ticker}): {e}")
    return summary

# --- メイン処理 ---
if __name__ == "__main__":
    print("=== システム起動 ===")
    news = get_news()
    for n in news: print(f"・{n}")
    
    current_watch_list = load_settings()
    if not current_watch_list: exit()
    
    count = 0
    try:
        while True:
            current_summary = check_stock_movement(current_watch_list)
            
            count += 1
            # 12回（1時間）ごとに中間報告
            if count >= 12:
                report_msg = "\n".join(current_summary)
                notification.notify(title="【1時間定期報告】", message=report_msg, timeout=10)
                count = 0
                
            time.sleep(300) 
    except KeyboardInterrupt:
        print("\n監視を終了しました。")