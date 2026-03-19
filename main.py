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
    
    # 株価リストのHTML作成
    items_html = ""
    for item in summary:
        status_class = "status-down" if "-" in item else "status-up"
        items_html += f'<div class="stock-item {status_class}">{item}</div>'

    # ニュースリスト（リンク付き）のHTML作成
    news_html = ""
    for n in news_list:
        news_html += f'<div class="news-item"><a href="{n["url"]}" target="_blank">・{n["title"]}</a></div>'

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>プロ仕様・株価ダッシュボード</title>
        <style>
            body {{ font-family: 'Segoe UI', Meiryo, sans-serif; background: #1a1a1a; color: #eee; padding: 40px; }}
            .container {{ max-width: 900px; margin: 0 auto; background: #2d2d2d; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
            h1 {{ text-align: center; color: #fff; margin-bottom: 30px; }}
            
            .stock-item {{ 
                background: #3d3d3d; margin-bottom: 15px; padding: 20px; border-radius: 0 10px 10px 0;
                font-size: 1.5em; font-weight: bold; display: flex; justify-content: space-between; transition: 0.2s;
            }}
            .stock-item:hover {{ transform: translateX(10px); }}
            .status-up {{ color: #ff4d4d; border-left: 10px solid #ff4d4d; padding-left: 15px; }}
            .status-down {{ color: #00fa9a; border-left: 10px solid #00fa9a; padding-left: 15px; }}

            .news-item {{ padding: 12px; border-bottom: 1px solid #444; }}
            .news-item a {{ color: #3498db; text-decoration: none; transition: 0.3s; font-size: 1.1em; }}
            .news-item a:hover {{ color: #5dade2; text-decoration: underline; }}
            
            .time {{ text-align: right; color: #888; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 MARKET DASHBOARD</h1>
            <p class="time">LAST UPDATE: {now}</p>
            <h3>💹 監視銘柄</h3>
            {items_html}
            <h3>📰 ヘッドライン (クリックで記事へ)</h3>
            {news_html}
        </div>
        <p class="time">現在時刻: <span id="realtime-clock">読み込み中...</span></p>
        <script>
        function updateClock() {{
        const now = new Date();
        const timeString = now.toLocaleTimeString('ja-JP');
        document.getElementById('realtime-clock').innerText = timeString;
         }}
        // 1秒(1000ミリ秒)ごとにupdateClockを実行する
         setInterval(updateClock, 1000);
         updateClock(); // 最初の一回を実行
     </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("🌐 ニュースリンク付きで更新しました！ (index.html)")

# --- 3. ニュース取得 (タイトルとURLをペアで取得) ---
def get_all_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    news_data = []
    try:
        res = requests.get("https://news.yahoo.co.jp/topics/top-picks", headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a"):
            title = a.get_text(strip=True)
            url = a.get("href")
            if len(title) > 15 and url and url.startswith("http"):
                news_data.append({"title": title, "url": url})
                if len(news_data) >= 4: break
    except:
        news_data.append({"title": "ニュース取得失敗", "url": "#"})
    return news_data

# --- 4. 監視設定ロード ---
def load_settings():
    watch_list = []
    try:
        with open('stocks.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                watch_list.append({"ticker": row["ticker"], "name": row["name"], "limit": float(row["limit"])})
        return watch_list
    except:
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
            msg = f"{item['name']}: {current_price:.2f}円 ({change_percent:+.2f}%)"
            print(msg)
            save_log(msg)
            summary.append(msg)
            if abs(change_percent) >= item["limit"]:
                notification.notify(title="株価アラート", message=msg, timeout=10)
        except Exception as e:
            print(f"エラー({ticker}): {e}")
    return summary

# --- 6. 実行メイン ---
if __name__ == "__main__":
    print("=== システム起動 ===")
    current_watch_list = load_settings()
    if not current_watch_list:
        print("設定ファイルを読み込めませんでした。")
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