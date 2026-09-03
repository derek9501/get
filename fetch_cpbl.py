import os
import json
import re
import requests
from datetime import datetime, timezone, timedelta

# ==========================================
# 1. 工具函式與基礎設定
# ==========================================

def get_tz():
    """取得 UTC+8 時區"""
    return timezone(timedelta(hours=8))

def format_date(date_str):
    """將 YYYY-MM-DD 轉成 M/D (星期X) 格式"""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        return f"{dt.month}/{dt.day} ({weekdays[dt.weekday()]})"
    except Exception:
        return date_str

def save_to_history(game_id, game_data):
    """
    解析 GameId (例如 "2026-A-301")
    自動寫入歷史目錄: history/{KindCode}/{Year}/{GameSno}.json
    """
    try:
        # 使用正規表達式拆解 GameId 格式 (年份-類別代碼-場次)
        match = re.match(r"^(\d{4})-([A-Z]+)-(\d+)$", game_id)
        if match:
            year, kind_code, game_sno = match.groups()
            history_dir = os.path.join("history", kind_code, year)
            os.makedirs(history_dir, exist_ok=True)
            
            # 歷史目錄檔名以場次編號命名 (例: 301.json)
            history_filepath = os.path.join(history_dir, f"{int(game_sno)}.json")
            with open(history_filepath, "w", encoding="utf-8") as f:
                json.dump(game_data, f, ensure_ascii=False, indent=2)
            print(f"📁 [歷史歸檔] 已備份至: {history_filepath}")
    except Exception as e:
        print(f"⚠️ 歸檔歷史資料時發生錯誤 ({game_id}): {e}")

# ==========================================
# 2. 舊版資料抓取與整合核心 (API Fetcher)
# ==========================================

def fetch_cpbl_data():
    """從 CPBL 官方 API 取得當日賽事清單與單場數據，並同步歸檔至歷史目錄"""
    today_str = datetime.now(get_tz()).strftime("%Y-%m-%d")
    list_url = f"https://stats.cpbl.com.tw/api/proxy/v1/games/schedule/{today_str}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.cpbl.com.tw/"
    }

    try:
        print(f"🚀 開始抓取今日 ({today_str}) CPBL 賽事資訊...")
        res = requests.get(list_url, headers=headers, timeout=15)
        
        if res.status_code == 200:
            data = res.json()
            games_list = data.get("Data", {}).get("Games", [])
            
            # 1. 儲存當日總清單
            with open("schedule.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已更新賽事總清單 (schedule.json)")

            if not games_list:
                print("ℹ️ 今日無排定賽事。")
                return

            # 2. 遍歷每場賽事，下載詳細數據
            for g in games_list:
                game_id = g.get("GameId") # 例如 2026-A-301
                if game_id:
                    detail_url = f"https://stats.cpbl.com.tw/api/proxy/v1/games/{game_id}"
                    detail_res = requests.get(detail_url, headers=headers, timeout=15)
                    
                    if detail_res.status_code == 200:
                        game_data = detail_res.json()
                        filename = f"{game_id}.json"
                        
                        # 儲存根目錄 JSON
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(game_data, f, ensure_ascii=False, indent=2)
                        print(f"✅ 已成功產出比賽 JSON: {filename}")

                        # 新版功能：同步歸檔至 history/ 結構
                        save_to_history(game_id, game_data)

            # 3. 將今日第一場比賽複製給預設 live_score.json
            first_game_id = games_list[0].get("GameId")
            if first_game_id and os.path.exists(f"{first_game_id}.json"):
                with open(f"{first_game_id}.json", "r", encoding="utf-8") as src, \
                     open("live_score.json", "w", encoding="utf-8") as dst:
                    dst.write(src.read())
                print(f"✅ 已更新 live_score.json (來源: {first_game_id}.json)")

        else:
            print(f"❌ 取得賽事清單失敗，HTTP Status: {res.status_code}")

    except Exception as e:
        print(f"❌ 執行 API 抓取時發生異常：{e}")

# ==========================================
# 3. HTML 網頁生成 (新版模組)
# ==========================================

def generate_html():
    """產生前端網頁 index.html"""
    html_content = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CPBL 賽事資訊與對戰歷史</title>
    <style>
        :root {
            --primary-color: #003865;
            --secondary-color: #05549e;
            --bg-color: #f4f6f9;
            --card-bg: #ffffff;
            --text-color: #333333;
            --border-color: #e0e0e0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: var(--primary-color);
        }
        .game-card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .game-header {
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            margin-bottom: 15px;
            font-weight: bold;
        }
        .team-vs {
            display: flex;
            align-items: center;
            justify-content: space-around;
            font-size: 1.2em;
            margin-bottom: 15px;
        }
        .history-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .history-table th, .history-table td {
            border: 1px solid var(--border-color);
            padding: 8px;
            text-align: center;
            font-size: 0.9em;
        }
        .history-table th {
            background-color: #f0f4f8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>CPBL 賽事歷史對戰數據</h1>
        <div id="content"></div>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ 已成功生成 index.html")

# ==========================================
# 主程式進入點
# ==========================================

if __name__ == "__main__":
    # 執行資料抓取與歷史歸檔
    fetch_cpbl_data()
    
    # 生成 HTML 頁面
    generate_html()
