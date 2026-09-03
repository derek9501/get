import requests
import json
import os
from datetime import datetime

# 取得今天日期 (YYYY-MM-DD)
today_str = datetime.now().strftime("%Y-%m-%d")

# 正確的中職當日賽事清單 API 網址
list_url = f"https://stats.cpbl.com.tw/api/proxy/v1/games/schedule/{today_str}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.cpbl.com.tw/"
}

try:
    # 1. 取得今日賽事列表
    res = requests.get(list_url, headers=headers, timeout=15)
    
    if res.status_code == 200:
        data = res.json()
        games_list = data.get("Data", {}).get("Games", [])
        
        # 先儲存當日的賽事總清單 API (可存成 schedule.json)
        with open("schedule.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已更新今日 ({today_str}) 賽事總清單 (schedule.json)")

        # 2. 遍歷每一場比賽，分別下載詳細數據並存成 {GameId}.json
        for g in games_list:
            game_id = g.get("GameId") # 例如 2026-A-301
            if game_id:
                detail_url = f"https://stats.cpbl.com.tw/api/proxy/v1/games/{game_id}"
                detail_res = requests.get(detail_url, headers=headers, timeout=15)
                
                if detail_res.status_code == 200:
                    game_data = detail_res.json()
                    filename = f"{game_id}.json"
                    
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(game_data, f, ensure_ascii=False, indent=2)
                    print(f"✅ 已成功產出比賽 JSON: {filename}")

        # 3. 將今日第一場比賽同時複製一份給預設的 live_score.json
        if games_list:
            first_game_id = games_list[0].get("GameId")
            if os.path.exists(f"{first_game_id}.json"):
                with open(f"{first_game_id}.json", "r", encoding="utf-8") as src, open("live_score.json", "w", encoding="utf-8") as dst:
                    dst.write(src.read())

    else:
        print(f"❌ 取得賽事清單失敗，HTTP Status: {res.status_code}")

except Exception as e:
    print(f"❌ 執行異常：{e}")
