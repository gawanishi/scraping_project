from flask import Flask, render_template, jsonify
import yfinance as yf
import datetime
import csv
import os

app = Flask(__name__)

# CSVから監視銘柄を読み込む関数
def load_settings():
    watch_list = []
    filename = 'stocks.csv'
    if not os.path.exists(filename):
        # ファイルがない場合のバックアップ用データ
        return [{"ticker": "NVDA", "name": "エヌビディア"}]
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            watch_list.append(row)
    return watch_list

# 全銘柄の最新データを取得する関数
def get_all_stock_data():
    watch_list = load_settings()
    results = []
    
    for item in watch_list:
        try:
            ticker = item['ticker']
            stock = yf.Ticker(ticker)
            # 最新2日分のデータを取得
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
            print(f"エラー ({item['ticker']}): {e}")
            
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update')
def update():
    # JavaScriptからのリクエストに応じて全データを返す
    data_list = get_all_stock_data()
    return jsonify(data_list)

if __name__ == '__main__':
    # debug=Trueにしておくと、コードを書き換えたら自動でサーバーが再起動します
    app.run(debug=True)