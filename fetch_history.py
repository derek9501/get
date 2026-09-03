import requests
import json
import os
from datetime import datetime, timedelta

# 設定想補抓的歷史日期區間 (例如: 2026-03-01 到 昨天)
start_date = datetime(2026, 3, 1)
end_date = datetime.now() - timedelta(days=1)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.cpbl.com.tw/"
}

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

current_dt = start_date
while current_dt <= end_date:
    date_str = current_dt.strftime("%Y-%m-%d")
    print(f"🔄 正在補抓歷史資料: {date_str}")
    
    list_url = f"https://stats.cpbl.com.tw/api/proxy/v1/games/schedule/{date_str}"
    try:
        res = requests.get(list_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            games_list = data.get("Data", {}).get("Games", [])
            
            if games_list:
                # 儲存該日的 schedule
                save_json(f"schedule/{date_str}.json", data)
                
                # 抓取該日每場比賽詳情
                for g in games_list:
                    game_id = g.get("GameId")
                    kind_code = g.get("KindCode")
                    game_sno = g.get("GameSno")
                    year = (g.get("PreExeDate") or date_str)[:4]

                    if game_id:
                        detail_url = f"https://stats.cpbl.com.tw/api/proxy/v1/games/{game_id}"
                        detail_res = requests.get(detail_url, headers=headers, timeout=10)
                        if detail_res.status_code == 200:
                            history_path = f"history/{kind_code}/{year}/{game_sno}.json"
                            save_json(history_path, detail_res.json())
            else:
                print(f"⚪ {date_str} 無賽事")
    except Exception as e:
        print(f"❌ {date_str} 抓取失敗: {e}")
        
    current_dt += timedelta(days=1)

print("🎉 歷史資料補抓完成！")
