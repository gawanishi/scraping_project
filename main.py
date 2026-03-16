import requests
from bs4 import BeautifulSoup
import time
import datetime
import yfinance as yf
import csv
import matplotlib.pyplot as plt
from plyer import notification

# --- 1. ログ保存機能 ---
def save_log(message):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('report.txt', 'a', encoding='utf-8') as f:
        f.write(f"[{now}] {message}\n")

# --- 2. ニュース取得（複数サイト） ---
def get_all_news():
    print("=== ニュースを取得中 ===")
    # ヤフー
    y_url = "https://news.yahoo.co.jp/topics/top-picks"
    y_res = requests.get(y_url, headers={"User-Agent": "Mozilla/5.0"})
    y_soup = BeautifulSoup(y_res.text, "html.parser")
    y_titles = [a.get_text(strip=True) for a in y_soup.find_all("a") if len(a.get_text(strip=True)) > 15][:3]
    
    print("【Yahoo!ニュース】")
    for t in y_titles: print(f" ・{t}")

    # ロイター（例として簡易的な取得）
    print("\n【経済ニュース(Reuters/他)】")
    # ※実際のスクレイピングは各サイトの規約や構造に合わせる必要があります
    # ここでは例としてYahooの経済カテゴリーを併用
    e_url = "https://news.yahoo.co.jp/categories/business"
    e_res = requests.get(e_url, headers={"User-Agent": "Mozilla/5.0"})
    e_soup = BeautifulSoup(e_res.text, "html.parser")
    e_titles = [a.get_text(strip=True) for a in e_soup.find_all("a") if len(a.get_text(strip=True)) > 15][:3]
    for t in e_titles: print(f" ・{t}")

# --- (既存のload_settings, save_chartはそのまま) ---
def load_settings():
    watch_list = []
    try:
        with open('stocks.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                watch_list.append({"ticker": row["ticker"], "name": row["name"], "limit": float(row["limit"])})
        return watch_list
    except: return []

def check_stock_movement(watch_list):
    print(f"\n--- 騰落チェック: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    summary = []
    for item in watch_list:
        ticker = item["ticker"]
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="2d")
            if len(data) < 2: continue
            prev_close = data['Close'].iloc[-2]
            current_price = data['Close'].iloc[-1]
            change_percent = ((current_price - prev_close) / prev_close) * 100
            
            log_msg = f"{item['name']}: {current_price:.2f}円 ({change_percent:+.2f}%)"
            print(log_msg)
            save_log(log_msg) # ログに書き込み！
            summary.append(log_msg)

            # (通知判定ロジックは前回と同じ)
            if abs(change_percent) >= item["limit"]:
                status = "🚀【急騰】" if change_percent > 0 else "📉【急落】"
                msg = f"{status}{change_percent:.2f}%\n{item['name']}: {current_price:.2f}円"
                notification.notify(title="株価アラート", message=msg, timeout=10)
        except Exception as e: print(f"エラー({ticker}): {e}")
    return summary

if __name__ == "__main__":
    get_all_news()
    current_watch_list = load_settings()
    if not current_watch_list: exit()
    
    count = 0
    try:
        while True:
            current_summary = check_stock_movement(current_watch_list)
            count += 1
            if count >= 12:
                notification.notify(title="【定期報告】", message="\n".join(current_summary))
                count = 0
            time.sleep(300)
    except KeyboardInterrupt: print("\n終了")