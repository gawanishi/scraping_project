import requests
from bs4 import BeautifulSoup
import time
import urllib3

# SSL警告を非表示にする
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://news.yahoo.co.jp/topics/top-picks"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

try:
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    articles = soup.find_all("a")

    print(f"--- 取得結果 ---")
    
    # データを保存するためのリストを用意
    results = []
    
    count = 1
    for article in articles:
        title = article.get_text(strip=True)
        # 10文字以上、かつ「もっと見る」などの不要な言葉を除外
        if len(title) > 10 and "一覧" not in title:
            line = f"{count}: {title}"
            print(line)
            results.append(line)
            count += 1
            if count > 10: break

    # --- ここからファイル保存処理 ---
    with open("news_list.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    
    print("\n[完了] news_list.txt に保存しました！")

except Exception as e:
    print(f"エラーが発生しました: {e}")