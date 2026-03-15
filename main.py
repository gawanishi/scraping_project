import requests
from bs4 import BeautifulSoup
import time
import urllib3
import yfinance as yf
import datetime

# --- 初期設定 ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
headers = {"User-Agent": "Mozilla/5.0"}

# --- 【機能1】ニュースを取得する関数 ---
def get_news():
    url = "https://news.yahoo.co.jp/topics/top-picks"
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # aタグの中から見出しっぽいものを探す（前回の修正版）
        articles = soup.find_all("a")
        news_titles = []
        for article in articles:
            title = article.get_text(strip=True)
            if len(title) > 10 and "一覧" not in title:
                news_titles.append(title)
                if len(news_titles) >= 10: break
        return news_titles
    except Exception as e:
        return [f"ニュース取得エラー: {e}"]

# --- 【機能2】株価を取得する関数 ---
def get_stock_price(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        # 最新1日分のデータを取得
        data = stock.history(period="1d")
        if not data.empty:
            # 最新の終値を小数点2桁で返す
            return f"{data['Close'].iloc[-1]:.2f}"
        return "データなし"
    except Exception as e:
        return f"エラー: {e}"

# --- 【メイン処理】実行 ---
if __name__ == "__main__":
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"=== 実行時刻: {now_str} ===")

    # 1. ニュース取得
    print("\n--- 今日のニュース ---")
    titles = get_news()
    for i, t in enumerate(titles, 1):
        print(f"{i}: {t}")

    # 2. 株価取得
    print("\n--- 最新株価 ---")
    # 好きな銘柄を追加・変更できます（.Tは東京証券取引所）
    target_stocks = {
        "NVDA": "エヌビディア",
        "7203.T": "トヨタ自動車",
        "9984.T": "ソフトバンクG",
        "AAPL": "アップル"
    }
    
    stock_results = []
    for ticker, name in target_stocks.items():
        price = get_stock_price(ticker)
        line = f"{name} ({ticker}): {price}"
        print(line)
        stock_results.append(line)

    # 3. ファイル保存 (report.txt)
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(f"取得日時: {now_str}\n\n")
        f.write("【ニュース】\n")
        f.write("\n".join(titles) + "\n\n")
        f.write("【株価】\n")
        f.write("\n".join(stock_results))
    
    print("\n[完了] report.txt に結果を保存しました！")