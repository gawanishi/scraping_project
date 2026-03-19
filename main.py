import requests
from bs4 import BeautifulSoup
import time
import datetime
import yfinance as yf
import csv
import os
from plyer import notification

# --- 1. ログ保存機能 ---
def save_log(message):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('report.txt', 'a', encoding='utf-8') as f:
        f.write(f"[{now}] {message}\n")

# --- 2. HTML Webページ生成機能 ---
def update_web_page(summary, news_list):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    items_html = ""
    for item in summary:
        status_class = "status-down" if "-" in item else "status-up"
        items_html += f'<div class="stock-item {status_class}">{item}</div>'

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
            .container {{ max-width: 900px; margin: 0 auto; background: #2d2d2d; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); transition: 0.5s; }}
            h1 {{ text-align: center; color: #fff; margin-bottom: 10px; }}
            .controls {{ text-align: center; margin-bottom: 30px; }}
            #update-btn {{ background: #3498db; color: white; border: none; padding: 10px 25px; border-radius: 30px; cursor: pointer; font-weight: bold; transition: 0.3s; }}
            .stock-item {{ background: #3d3d3d; margin-bottom: 15px; padding: 20px; border-radius: 0 10px 10px 0; font-size: 1.5em; font-weight: bold; display: flex; justify-content: space-between; transition: 0.2s; }}
            .status-up {{ color: #ff4d4d; border-left: 10px solid #ff4d4d; padding-left: 15px; }}
            .status-down {{ color: #00fa9a; border-left: 10px solid #00fa9a; padding-left: 15px; }}
            .news-item {{ padding: 12px; border-bottom: 1px solid #444; }}
            .news-item a {{ color: #3498db; text-decoration: none; font-size: 1.1em; }}
            .info-bar {{ display: flex; justify-content: space-between; color: #888; font-size: 0.9em; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 MARKET DASHBOARD</h1>
            <div class="info-bar">
                <span>現在時刻: <span id="realtime-clock">...</span></span>
                <span>データ最終更新: {now}</span>
            </div>
            <div class="controls"><button id="update-btn" onclick="refreshEffect()">最新情報に更新</button></div>
            <h3>💹 監視銘柄</h3>
            {items_html}
            <h3>📰 ヘッドライン</h3>
            {news_html}
        </div>
        <script>
            function updateClock() {{
                const now = new Date();
                document.getElementById('realtime-clock').innerText = now.toLocaleTimeString('ja-JP');
            }}
            setInterval(updateClock, 1000);
            updateClock();
            function refreshEffect() {{
                const btn = document.getElementById('update-btn');
                btn.innerText = "更新確認中...";
                setTimeout(() => {{
                    btn.innerText = "最新情報に更新";
                    alert("Python側で5分ごとに自動更新されます。");
                }}, 1200);
            }}
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("🌐 index.html を更新しました。")

# --- 3. ニュース取得 ---
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
    filename = 'stocks.csv'
    
    # 診断: ファイルが存在するか
    if not os.path.exists(filename):
        print(f"❌ エラー: '{filename}' が見つかりません。")
        return []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                watch_list.append({"ticker": row["ticker"], "name": row["name"], "limit": float(row["limit"])})
        return watch_list
    except Exception as e:
        print(f"❌ エラー: CSVの読み込み中に問題が発生しました: {e}")
        return []

# --- 5. メイン監視ロジック ---
def check_stock_movement(watch_list):
    print(f"--- 騰落チェック開始: {datetime.datetime.now().strftime('%H:%M:%S')} ---")
    summary = []
    for item in watch_list:
        try:
            stock = yf.Ticker(item["ticker"])
            data = stock.history(period="2d")
            if len(data) < 2: continue
            prev_close = data['Close'].iloc[-2]
            current_price = data['Close'].iloc[-1]
            change_percent = ((current_price - prev_close) / prev_close) * 100
            msg = f"{item['name']}: {current_price:.2f}円 ({change_percent:+.2f}%)"
            print(f"  > {msg}")
            summary.append(msg)
        except Exception as e:
            print(f"  > ❌ エラー({item['ticker']}): {e}")
    return summary

# --- 6. 実行メイン ---
if __name__ == "__main__":
    print("\n🚀 === システム起動診断開始 ===")
    
    # 手動でリストを作成（CSVがダメな時用）
    current_watch_list = load_settings()
    
    if not current_watch_list:
        print("💡 CSVが読み込めないため、テスト用銘柄（エヌビディア）で起動します。")
        current_watch_list = [{"ticker": "NVDA", "name": "エヌビディア(TEST)", "limit": 1.0}]

    print(f"✅ {len(current_watch_list)}件の銘柄で監視をスタートします。")
    
    try:
        while True:
            latest_news = get_all_news()
            current_summary = check_stock_movement(current_watch_list)
            update_web_page(current_summary, latest_news)
            
            print("🕒 5分間待機します... (中断は Ctrl+C)")
            time.sleep(300)
    except KeyboardInterrupt:
        print("\n👋 監視を終了しました。")