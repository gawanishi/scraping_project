import requests
from bs4 import BeautifulSoup
import time
import datetime
import yfinance as yf
import csv  # ← ここに「csv」を追加！
from plyer import notification

# --- ここに追加：CSVから銘柄を読み込む手順 ---
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
        print("エラー: stocks.csv が見つかりません。作成してください。")
        return []
    if __name__ == "__main__":
    print("=== システム起動 ===")
    
    # ここで「CSV読み込み手順」を実行してリストを受け取る
    current_watch_list = load_settings() 
    
    if not current_watch_list:
        print("監視する銘柄がないため終了します。")
        exit()
        
    print(f"{len(current_watch_list)}件の銘柄を読み込みました。")
    
    # あとはループさせるだけ
    try:
        while True:
            check_stock_movement(current_watch_list) # ロードしたリストを渡す
            time.sleep(300)