import requests
import json

url = "https://www.cpbl.com.tw/box/getlive"

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/json; charset=UTF-8",
    "Origin": "https://www.cpbl.com.tw",
    "Referer": "https://www.cpbl.com.tw/box/index",
    "Sec-Ch-Ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "X-Requested-With": "XMLHttpRequest"
}

payload = {
    "year": "2026",
    "kindCode": "A",
    "gameSno": "1"
}

result_data = {}

try:
    # 先 visit 官網首頁帶入整套 Cookie 與 Session
    session.get("https://www.cpbl.com.tw/box/index", headers=headers, timeout=15)
    
    # 發送 POST 請求
    response = session.post(url, headers=headers, json=payload, timeout=15)
    
    if response.status_code == 200:
        result_data = response.json()
        print("✅ 成功獲取 CPBL 數據！")
    else:
        result_data = {"error": True, "message": f"HTTP status {response.status_code}"}
        print(f"❌ HTTP 錯誤：{response.status_code}")
except Exception as e:
    result_data = {"error": True, "message": str(e)}
    print(f"❌ 執行異常：{e}")

with open("live_score.json", "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)
