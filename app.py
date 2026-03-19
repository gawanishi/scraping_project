from flask import Flask, render_template, jsonify
import yfinance as yf
import csv
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- ニュースを取得する関数 ---
def get_latest_news():
    try:
        # Yahoo!ニュースのトップページ（トピックスよりこちらの方が安定します）
        url = "https://news.yahoo.co.jp/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_list = []
        
        # 2026年の最新仕様に合わせたセレクタ
        # ニュースのタイトルとURLが含まれるaタグを広めに探します
        for a_tag in soup.find_all('a'):
            title = a_tag.get_text().strip()
            url = a_tag.get('href', '')
            
            # 「text-link」という言葉が含まれるクラスや、特定の長さ以上のテキストをニュースと判定
            if 'news.yahoo.co.jp/pickup/' in url and len(title) > 10:
                news_list.append({
                    "title": title,
                    "url": url
                })
            
            if len(news_list) >= 5:
                break
                
        if not news_list:
            # もし上記で見つからない場合の予備手段
            items = soup.select('li > a')
            for item in items:
                t = item.get_text().strip()
                u = item.get('href', '')
                if len(t) > 10 and 'news.yahoo.co.jp' in u:
                    news_list.append({"title": t, "url": u})
                if len(news_list) >= 5: break

        return news_list if news_list else [{"title": "ニュースの取得方法を調整中...", "url": "#"}]

    except Exception as e:
        print(f"詳細エラー: {e}")
        return [{"title": "接続エラーが発生しました", "url": "#"}]
    except Exception as e:
        print(f"ニュース取得エラー: {e}")
        return [{"title": f"ニュース取得失敗: {e}", "url": "#"}]

# --- CSVから監視銘柄を読み込む関数 ---
def load_settings():
    watch_list = []
    filename = 'stocks.csv'
    if not os.path.exists(filename):
        return [{"ticker": "NVDA", "name": "エヌビディア"}]
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            watch_list.append(row)
    return watch_list

# --- 全銘柄の最新データを取得する関数 ---
def get_all_stock_data():
    watch_list = load_settings()
    results = []
    for item in watch_list:
        try:
            stock = yf.Ticker(item['ticker'])
            data = stock.history(period="2d")
            if len(data) >= 2:
                current_price = data['Close'].iloc[-1]
                prev_close = data['Close'].iloc[-2]
                change = ((current_price - prev_close) / prev_close) * 100
                results.append({
                    "name": item['name'],
                    "price": round(current_price, 2),
                    "change": round(change, 2)
                })
        except Exception as e:
            print(f"株価取得エラー ({item['ticker']}): {e}")
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update')
def update():
    # 株価とニュースをまとめて辞書形式で返す
    return jsonify({
        "stocks": get_all_stock_data(),
        "news": get_latest_news()
    })

if __name__ == '__main__':
    app.run(debug=True)