import requests
import json

# 直接指定新版 API 網址 (2026 年例行賽 308 場次)
url = "https://stats.cpbl.com.tw/api/proxy/v1/games/2026-A-308"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.cpbl.com.tw/"
}

result_data = {}

try:
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code == 200:
        result_data = response.json()
        print("✅ 成功獲取場次 308 即時數據！")
    else:
        result_data = {"error": True, "message": f"HTTP status {response.status_code}"}
        print(f"❌ HTTP 錯誤：{response.status_code}")

except Exception as e:
    result_data = {"error": True, "message": str(e)}
    print(f"❌ 執行異常：{e}")

# 儲存為 live_score.json
with open("live_score.json", "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)
