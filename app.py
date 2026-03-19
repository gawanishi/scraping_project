from flask import Flask, render_template, jsonify
import yfinance as yf
import datetime

app = Flask(__name__)

# 株価を取得する関数
def get_stock_data():
    ticker = "NVDA" # 今回はテストでエヌビディア固定
    stock = yf.Ticker(ticker)
    data = stock.history(period="2d")
    current_price = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-2]
    change = ((current_price - prev_close) / prev_close) * 100
    return {
        "name": "エヌビディア",
        "price": round(current_price, 2),
        "change": round(change, 2),
        "time": datetime.datetime.now().strftime('%H:%M:%S')
    }

@app.route('/')
def index():
    # 最初にページを開いた時の処理
    return render_template('index.html')

@app.route('/api/update')
def update():
    # ボタンが押された時にJSから呼ばれるルート
    data = get_stock_data()
    return jsonify(data) # データをJSON形式で返す

if __name__ == '__main__':
    app.run(debug=True)