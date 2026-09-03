import requests
import json

url = "https://www.cpbl.com.tw/box/getlive"

# 1. 使用 Session 自動處理必要的 Cookie 與連線狀態
session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.cpbl.com.tw/box/index",
    "Origin": "https://www.cpbl.com.tw",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}

# 2. 帶入當前實際比賽的年份與參數 (請依實際比賽更改 year / gameSno)
payload = {
    "year": "2026",      # 年份
    "kindCode": "A",     # 例行賽通常為 A，熱身賽/官辦為 D
    "gameSno": "1"       # 場次編號
}

try:
    # 先存取一次首頁取得 Cookies
    session.get("https://www.cpbl.com.tw/box/index", headers=headers, timeout=10)
    
    # 發送 POST 請求
    response = session.post(url, headers=headers, json=payload, timeout=10)
    
    if response.status_code == 200:
        with open("live_score.json", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("✅ 成功獲取 CPBL 數據：", response.text[:100])
    else:
        print(f"❌ HTTP 錯誤：{response.status_code}")
except Exception as e:
    print(f"❌ 執行異常：{e}")
