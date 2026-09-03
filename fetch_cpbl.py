import requests
import json
import os
import shutil
from datetime import datetime

# 取得今天日期
today_dt = datetime.now()
today_str = today_dt.strftime("%Y-%m-%d")

# CPBL 當日賽事清單 API
list_url = f"https://stats.cpbl.com.tw/api/proxy/v1/games/schedule/{today_str}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.cpbl.com.tw/"
}

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

try:
    res = requests.get(list_url, headers=headers, timeout=15)
    
    if res.status_code == 200:
        data = res.json()
        games_list = data.get("Data", {}).get("Games", [])
        
        # 1. 儲存當日 schedule 到 today/ 與 schedule/ 資料夾
        save_json("today/schedule.json", data)
        save_json(f"schedule/{today_str}.json", data)
        print(f"✅ 已更新今日 schedule (today/schedule.json & schedule/{today_str}.json)")

        # 2. 清空 today/ 資料夾內的舊比賽 JSON 檔 (避免跨日殘留)
        if os.path.exists("today"):
            for fname in os.listdir("today"):
                if fname != "schedule.json" and fname.endswith(".json"):
                    os.remove(os.path.join("today", fname))

        # 3. 下載今日各場次，同時存入 today/ 與 history/
        for g in games_list:
            game_id = g.get("GameId")       # 例: 2026-A-306
            kind_code = g.get("KindCode")   # 例: A
            game_sno = g.get("GameSno")     # 例: 306
            year = g.get("PreExeDate", today_str)[:4]

            if game_id:
                detail_url = f"https://stats.cpbl.com.tw/api/proxy/v1/games/{game_id}"
                detail_res = requests.get(detail_url, headers=headers, timeout=15)
                
                if detail_res.status_code == 200:
                    game_data = detail_res.json()
                    
                    # 存入 today/ 資料夾 (格式: today/2026-A-306.json)
                    save_json(f"today/{game_id}.json", game_data)
                    
                    # 歸檔至 history/ 資料夾 (格式: history/A/2026/306.json)
                    history_path = f"history/{kind_code}/{year}/{game_sno}.json"
                    save_json(history_path, game_data)
                    print(f"✅ 已產出: today/{game_id}.json 與 {history_path}")

    else:
        print(f"❌ API 請求失敗，Status Code: {res.status_code}")

except Exception as e:
    print(f"❌ 執行錯誤: {e}")
