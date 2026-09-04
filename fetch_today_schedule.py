import json
import requests
from datetime import datetime, timezone, timedelta

# 1. 設定目標日期 (預設為 2026-09-03，亦可動態改為今天日期)
# TARGET_DATE = "2026-09-03"

# 若需要自動改為當天日期 (UTC+8)，取消下一行的註解即可：
TARGET_DATE = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d")

def fetch_today_schedule(target_date):
    url = f"https://stats.cpbl.com.tw/api/proxy/v1/games/schedule/{target_date}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.cpbl.com.tw/"
    }

    try:
        print(f"🚀 開始抓取 ({target_date}) 賽事賽程清單...")
        res = requests.get(url, headers=headers, timeout=15)
        
        if res.status_code == 200:
            data = res.json()
            
            # 將抓取到的資料存成 today-schedule.json
            output_filename = "today-schedule.json"
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            games_count = len(data.get("Data", {}).get("Games", []))
            print(f"✅ 成功產出 {output_filename}！(當日共有 {games_count} 場賽事)")
        else:
            print(f"❌ 抓取失敗，HTTP 狀態碼: {res.status_code}")

    except Exception as e:
        print(f"❌ 執行時發生異常: {e}")

if __name__ == "__main__":
    fetch_today_schedule(TARGET_DATE)
