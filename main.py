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
    
    # --- 1. 株価ごとに「上昇(up)」か「下落(down)」かのHTMLを作る ---
    items_html = ""
    for item in summary:
        # 文字列の中に "-" (マイナス) があれば下落クラス、なければ上昇クラス
        status_class = "status-down" if "-" in item else "status-up"
        items_html += f'<div class="stock-item {status_class}">{item}</div>'

    # --- 2. HTML全体の組み立て ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>プロ仕様・株価ダッシュボード</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Meiryo, sans-serif; 
                background: #1a1a1a; /* ダークモード風 */
                color: #eee;
                padding: 40px; 
            }}
            .container {{ 
                max-width: 900px; 
                margin: 0 auto; 
                background: #2d2d2d; 
                padding: 30px; 
                border-radius: 20px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
            }}
            h1 {{ text-align: center; color: #fff; margin-bottom: 30px; }}
            
            /* あなたが作ったスタイルをここに適用！ */
            .stock-item {{ 
                background: #3d3d3d;
                margin-bottom: 15px;
                padding: 20px;
                border-radius: 0 10px 10px 0;
                font-size: 1.5em;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                transition: transform 0.2s;
            }}
            .stock-item:hover {{ transform: translateX(10px); }}

            .status-up {{ 
                color: #ff4d4d; 
                border-left: 10px solid #ff4d4d; 
                padding-left: 15px; 
            }}
            .status-down {{ 
                color: #00fa9a; 
                border-left: 10px solid #00fa9a; 
                padding-left: 15px; 
            }}

            .news-item {{ padding: 10px; border-bottom: 1px solid #444; color: #ccc; }}
            .time {{ text-align: right; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 MARKET DASHBOARD</h1>
            <p class="time">LAST UPDATE: {now}</p>
            
            <h3>💹 監視銘柄</h3>
            {items_html}
            
            <h3>📰 ヘッドライン</h3>
            {"".join([f'<div class="news-item">・{n}</div>' for n in news_list])}
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("🌐 デザインを更新しました！ (index.html)")
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