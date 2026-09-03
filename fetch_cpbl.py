import requests
import json

url = "https://www.cpbl.com.tw/box/getlive"

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.cpbl.com.tw/box/index",
    "Origin": "https://www.cpbl.com.tw",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}

payload = {
    "year": "2026",
    "kindCode": "A",
    "gameSno": "1"
}

result_data = {}

try:
    # 存取首頁取得 Cookie
    session.get("https://www.cpbl.com.tw/box/index", headers=headers, timeout=10)
    
    # 發送 POST 請求
    response = session.post(url, headers=headers, json=payload, timeout=10)
    
    if response.status_code == 200:
        result_data = response.json()
        print("✅ 成功獲取 CPBL 數據！")
    else:
        result_data = {"error": True, "message": f"HTTP status {response.status_code}"}
        print(f"❌ HTTP 錯誤：{response.status_code}")
except Exception as e:
    result_data = {"error": True, "message": str(e)}
    print(f"❌ 執行異常：{e}")

# 確保無論成功與否都寫入檔案，避免 Git 建檔失敗
with open("live_score.json", "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)
