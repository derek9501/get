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
    month_str = str(today.month)

    print(f"Fetching schedule for date: {date_str}")

    # CPBL API URL (抓取當天賽程)
    url = f"https://www.cpbl.com.tw/api/getschedule?date={date_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching data from API: {e}")
        data = []

    # 1. 寫入 today_schedule.json (供首頁或當日即時資訊使用)
    today_file = "today_schedule.json"
    with open(today_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "date": date_str,
                "updated_at": today.strftime("%Y-%m-%d %H:%M:%S"),
                "games": data,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"Updated {today_file}")

    # 2. 寫入 schedule/ 資料夾 (schedule/{year}/{month}.json)
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

    # 以日期為 key 儲存或更新當日賽程資料
    schedule_data[date_str] = {
        "updated_at": today.strftime("%Y-%m-%d %H:%M:%S"),
        "games": data,
    }

    with open(schedule_file_path, "w", encoding="utf-8") as f:
        json.dump(schedule_data, f, ensure_ascii=False, indent=2)
    print(f"Successfully saved schedule data to {schedule_file_path}")

    # 3. 同步寫入 history 資料夾 (保持歷史檔案備份)
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
        "games": data,
    }

    with open(history_file_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
    print(f"Updated history file at {history_file_path}")


if __name__ == "__main__":
    fetch_today_schedule()
