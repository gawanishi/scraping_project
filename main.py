import requests
from bs4 import BeautifulSoup
import time
import datetime
import yfinance as yf
import csv
from plyer import notification

# --- 1. ログ保存機能 ---
def save_log(message):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('report.txt', 'a', encoding='utf-8') as f:
        f.write(f"[{now}] {message}\n")

# --- 2. HTML Webページ生成機能 ---
def update_web_page(summary, news_list):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # CSSの波括弧だけを {{ }} にしています
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>株価ダッシュボード</title>
        <style>
            body {{ 
                font-family: 'Helvetica Neue', Arial, sans-serif; 
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                min-height: 100vh;
                padding: 20px; 
                color: #333; 
            }}
            .container {{ 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
            }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; text-align: center; }}
            h3 {{ color: #2980b9; margin-top: 30px; border-left: 5px solid #2980b9; padding-left: 10px; }}
            .stock-item {{ 
                padding: 15px; 
                border-bottom: 2px solid #3498db; 
                font-size: 2.0em; 
                font-weight: 900; 
                color: #2c3e50;
                display: flex; 
                justify-content: space-between; 
            }}
            .stock-item:hover {{
                background-color: #f1f9ff;
                transform: scale(1.02);
                transition: 0.3s;
                cursor: pointer;
            }}
            .news-item {{ padding: 8px 0; border-bottom: 1px dashed #ccc; color: #444; }}
            .time {{ text-align: right; color: #7f8c8d; font-size: 0.9em; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 投資ダッシュボード</h1>
            <p class="time">最終更新日時: {now}</p>
            
            <h3>📈 現在の株価状況</h3>
            {"".join([f'<div class="stock-item">{item}</div>' for item in summary])}
            
            <h3>📰 最新ニュース</h3>
            {"".join([f'<div class="news-item">・{n}</div>' for n in news_list])}
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("🌐 Webページを更新しました (index.html)")

# --- 3. ニュース取得 ---
def get_all_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    all_titles = []
    try:
        res = requests.get("https://news.yahoo.co.jp/topics/top-picks", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        titles = [a.get_text(strip=True) for a in soup.find_all("a") if len(a.get_text(strip=True)) > 15][:4]
        all_titles.extend(titles)
    except:
        all_titles.append("ニュース取得失敗")
    return all_titles

# --- 4. 監視設定ロード ---
def load_settings():
    watch_list = []
    try:
        with open('stocks.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # ここはPythonの辞書なので { } で正解！
                watch_list.append({"ticker": row["ticker"], "name": row["name"], "limit": float(row["limit"])})
        return watch_list
    except Exception as e:
        print(f"エラー: {e}")
        return []

# --- 5. メイン監視ロジック ---
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
            save_log(log_msg)
            summary.append(log_msg)

            if abs(change_percent) >= item["limit"]:
                status = "🚀【急騰】" if change_percent > 0 else "📉【急落】"
                msg = f"{status}{change_percent:.2f}%\n{item['name']}: {current_price:.2f}円"
                notification.notify(title="株価アラート", message=msg, timeout=10)
        except Exception as e:
            print(f"エラー({ticker}): {e}")
    return summary

# --- 6. 実行メイン ---
if __name__ == "__main__":
    print("=== システム起動 ===")
    current_watch_list = load_settings()
    if not current_watch_list:
        print("設定ファイルが読み込めませんでした。stocks.csvを確認してください。")
        exit()
    
    count = 0
    try:
        while True:
            latest_news = get_all_news()
            current_summary = check_stock_movement(current_watch_list)
            update_web_page(current_summary, latest_news)
            
            count += 1
            if count >= 12:
                notification.notify(title="【定期報告】", message="\n".join(current_summary))
                count = 0
            
            print("5分間待機中...")
            time.sleep(300)
    except KeyboardInterrupt:
        print("\n監視を終了しました。")