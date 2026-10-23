import datetime
import json
import os
import requests


def fetch_today_schedule():
    # 取得今天的日期 (台灣時間 UTC+8)
    tz_offset = datetime.timezone(datetime.timedelta(hours=8))
    today = datetime.datetime.now(tz_offset)

    date_str = today.strftime("%Y-%m-%d")
    year_str = str(today.year)
    month_str = today.strftime("%m")  # 補滿兩位數 (如 09)

    print(f"Fetching schedule for date: {date_str}")

    url = f"https://www.cpbl.com.tw/schedule/getgames?date={date_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Referer": "https://www.cpbl.com.tw/schedule",
    }

    raw_data = None
    games = []

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        raw_data = response.json()

        # 判斷 API 回傳結構並正確提取 games 列表
        if isinstance(raw_data, list):
            games = raw_data
        elif isinstance(raw_data, dict):
            # 針對 CPBL API (Data -> Games 或 Data) 提取資料
            data_field = raw_data.get("Data", raw_data.get("data", raw_data))
            if isinstance(data_field, dict):
                games = data_field.get("Games", data_field.get("games", []))
            elif isinstance(data_field, list):
                games = data_field
            if not isinstance(games, list):
                games = []
    except Exception as e:
        print(f"Error fetching data from API: {e}")
        games = []

    if not games:
        print(f"判斷結果：{date_str} 無比賽資料或 API 無資料。")

    # 封裝統一輸出的結構
    output_content = {
        "date": date_str,
        "updated_at": today.strftime("%Y-%m-%d %H:%M:%S"),
        "games": games,
    }

    # 1. 寫入 today-schedule.json
    today_file = "today-schedule.json"
    with open(today_file, "w", encoding="utf-8") as f:
        json.dump(output_content, f, ensure_ascii=False, indent=2)
    print(f"Updated {today_file}")

    # 2. 寫入 schedule/ 資料夾 (schedule/{year}/{month}.json，例如 schedule/2026/09.json)
    schedule_dir = os.path.join("schedule", year_str)
    os.makedirs(schedule_dir, exist_ok=True)
    schedule_file_path = os.path.join(schedule_dir, f"{month_str}.json")

    schedule_data = {}
    if os.path.exists(schedule_file_path):
        try:
            with open(schedule_file_path, "r", encoding="utf-8") as f:
                schedule_data = json.load(f)
        except Exception as e:
            print(f"Error reading existing schedule file {schedule_file_path}: {e}")
            schedule_data = {}

    schedule_data[date_str] = {
        "updated_at": today.strftime("%Y-%m-%d %H:%M:%S"),
        "games": games,
    }

    with open(schedule_file_path, "w", encoding="utf-8") as f:
        json.dump(schedule_data, f, ensure_ascii=False, indent=2)
    print(f"Successfully saved schedule data to {schedule_file_path}")

    # 3. 同步寫入 history 資料夾 (history/A/{year}/{month}.json)
    history_dir = os.path.join("history", "A", year_str)
    os.makedirs(history_dir, exist_ok=True)
    history_file_path = os.path.join(history_dir, f"{month_str}.json")

    history_data = {}
    if os.path.exists(history_file_path):
        try:
            with open(history_file_path, "r", encoding="utf-8") as f:
                history_data = json.load(f)
        except Exception as e:
            print(f"Error reading history file: {e}")
            history_data = {}

    history_data[date_str] = {
        "updated_at": today.strftime("%Y-%m-%d %H:%M:%S"),
        "games": games,
    }

    with open(history_file_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
    print(f"Updated history file at {history_file_path}")


if __name__ == "__main__":
    fetch_today_schedule()
