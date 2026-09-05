import os
import json
import re
import time
import requests
from datetime import datetime, timezone, timedelta


# ============================================================
# CPBL 自動資料更新程式
# ============================================================
#
# 功能：
# 1. 自動取得台灣今天的 CPBL 賽程
# 2. 儲存 schedule/YYYY-MM-DD.json
# 3. 取得今天每一場比賽的詳細資料
# 4. 儲存到 today/
# 5. 自動備份到 history/
# 6. 更新 live_score.json
# 7. API 失敗時自動重試
# 8. 不會修改 index.html
#
# ============================================================


# ------------------------------------------------------------
# 基本設定
# ------------------------------------------------------------

BASE_URL = "https://stats.cpbl.com.tw/api/proxy/v1"

# 台灣時區 UTC+8
TAIPEI_TZ = timezone(timedelta(hours=8))

# API 重試次數
MAX_RETRIES = 3

# 每次重試等待秒數
RETRY_DELAY = 3

# HTTP Timeout
REQUEST_TIMEOUT = 20


# ------------------------------------------------------------
# HTTP Headers
# ------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.cpbl.com.tw/",
}


# ============================================================
# 工具函式
# ============================================================

def get_today_tw():
    """
    取得台灣時間今天的日期。

    回傳格式：
    YYYY-MM-DD
    """
    return datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d")


def save_json(file_path, data):
    """
    儲存 JSON 檔案。
    """

    directory = os.path.dirname(file_path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


def request_json(url):
    """
    從 API 取得 JSON。

    如果失敗會自動重試 MAX_RETRIES 次。
    """

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            print(
                f"🌐 API 請求 "
                f"(第 {attempt}/{MAX_RETRIES} 次)：{url}"
            )

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )

            # HTTP 錯誤直接觸發 exception
            response.raise_for_status()

            # 解析 JSON
            return response.json()

        except Exception as error:

            last_error = error

            print(
                f"⚠️ API 請求失敗：{error}"
            )

            if attempt < MAX_RETRIES:

                print(
                    f"⏳ {RETRY_DELAY} 秒後重新嘗試..."
                )

                time.sleep(RETRY_DELAY)

    # 三次全部失敗
    raise RuntimeError(
        f"API 請求失敗，已重試 {MAX_RETRIES} 次："
        f"{url}\n最後錯誤：{last_error}"
    )


# ============================================================
# GameId → history 路徑
# ============================================================

def get_history_path(game_id):
    """
    將 GameId 轉成歷史資料路徑。

    例如：

    2026-A-301

    →

    history/A/2026/301.json
    """

    if not game_id:
        return None

    match = re.match(
        r"^(\d{4})-([A-Z]+)-(\d+)$",
        game_id
    )

    if not match:
        print(
            f"⚠️ 無法解析 GameId：{game_id}"
        )
        return None

    year, kind_code, game_sno = match.groups()

    return os.path.join(
        "history",
        kind_code,
        year,
        f"{int(game_sno)}.json"
    )


# ============================================================
# 清理 today/
# ============================================================

def clean_today_directory():
    """
    清除 today/ 裡面的舊比賽 JSON。

    避免昨天的比賽一直留在 today/。

    schedule.json 會在後面重新產生。
    """

    today_dir = "today"

    os.makedirs(today_dir, exist_ok=True)

    for filename in os.listdir(today_dir):

        file_path = os.path.join(
            today_dir,
            filename
        )

        # 只刪除 JSON
        if (
            os.path.isfile(file_path)
            and filename.lower().endswith(".json")
        ):

            try:

                os.remove(file_path)

                print(
                    f"🧹 清除舊 today 資料：{filename}"
                )

            except Exception as error:

                print(
                    f"⚠️ 無法刪除 {filename}：{error}"
                )


# ============================================================
# 抓取 CPBL 今日賽程
# ============================================================

def fetch_today_schedule(date_str):
    """
    取得指定日期的 CPBL 賽程。
    """

    url = (
        f"{BASE_URL}/games/schedule/"
        f"{date_str}"
    )

    print("")
    print("=" * 60)
    print(
        f"📅 開始抓取 CPBL 賽程：{date_str}"
    )
    print("=" * 60)

    data = request_json(url)

    games = (
        data
        .get("Data", {})
        .get("Games", [])
        or []
    )

    print(
        f"📊 今日共有 {len(games)} 場比賽"
    )

    return data, games


# ============================================================
# 儲存今日賽程
# ============================================================

def save_schedule(date_str, schedule_data):
    """
    儲存：

    schedule/YYYY-MM-DD.json

    同時保留：

    schedule.json
    today-schedule.json
    today/schedule.json
    """

    # 給 index.html 使用
    schedule_path = os.path.join(
        "schedule",
        f"{date_str}.json"
    )

    save_json(
        schedule_path,
        schedule_data
    )

    print(
        f"✅ 已更新：{schedule_path}"
    )

    # 舊版相容
    save_json(
        "schedule.json",
        schedule_data
    )

    print(
        "✅ 已更新：schedule.json"
    )

    # 舊版相容
    save_json(
        "today-schedule.json",
        schedule_data
    )

    print(
        "✅ 已更新：today-schedule.json"
    )

    # today 資料夾
    save_json(
        os.path.join(
            "today",
            "schedule.json"
        ),
        schedule_data
    )

    print(
        "✅ 已更新：today/schedule.json"
    )


# ============================================================
# 抓取單場比賽
# ============================================================

def fetch_game_detail(game_id):
    """
    取得單場比賽詳細資料。
    """

    url = (
        f"{BASE_URL}/games/"
        f"{game_id}"
    )

    return request_json(url)


# ============================================================
# 儲存單場比賽
# ============================================================

def save_game(game_id, game_data):
    """
    將單場比賽同時儲存到：

    today/GameId.json

    history/A/年份/GameSno.json
    """

    # --------------------------------------------------------
    # today/
    # --------------------------------------------------------

    today_path = os.path.join(
        "today",
        f"{game_id}.json"
    )

    save_json(
        today_path,
        game_data
    )

    print(
        f"✅ 今日資料：{today_path}"
    )

    # --------------------------------------------------------
    # history/
    # --------------------------------------------------------

    history_path = get_history_path(
        game_id
    )

    if history_path:

        save_json(
            history_path,
            game_data
        )

        print(
            f"📁 歷史資料：{history_path}"
        )


# ============================================================
# 更新 live_score.json
# ============================================================

def update_live_score(games_data):
    """
    更新 live_score.json。

    為了保持你原本專案的相容性：

    - 如果今天有比賽
      → 使用第一場比賽詳細資料

    - 如果今天沒有比賽
      → 儲存空資料結構
    """

    if games_data:

        first_game = games_data[0]

        save_json(
            "live_score.json",
            first_game
        )

        print(
            "⚾ live_score.json 已更新"
        )

    else:

        empty_data = {
            "Data": {
                "Games": []
            }
        }

        save_json(
            "live_score.json",
            empty_data
        )

        print(
            "ℹ️ 今日無比賽，live_score.json 已清空"
        )


# ============================================================
# 主更新流程
# ============================================================

def update_cpbl():
    """
    CPBL 完整自動更新流程。
    """

    today = get_today_tw()

    print("")
    print("🏟️ CPBL 自動更新程式")
    print(
        f"🇹🇼 台灣日期：{today}"
    )
    print("")


    # --------------------------------------------------------
    # 1. 清除舊 today 資料
    # --------------------------------------------------------

    clean_today_directory()


    # --------------------------------------------------------
    # 2. 抓取今日賽程
    # --------------------------------------------------------

    schedule_data, games = fetch_today_schedule(
        today
    )


    # --------------------------------------------------------
    # 3. 儲存賽程
    # --------------------------------------------------------

    save_schedule(
        today,
        schedule_data
    )


    # --------------------------------------------------------
    # 4. 沒有比賽
    # --------------------------------------------------------

    if not games:

        print("")
        print(
            "ℹ️ 今天沒有排定的 CPBL 比賽"
        )

        update_live_score([])

        print("")
        print("🎉 更新完成")
        return


    # --------------------------------------------------------
    # 5. 抓取每一場比賽
    # --------------------------------------------------------

    successful_games = []

    failed_games = []

    for index, game in enumerate(
        games,
        start=1
    ):

        game_id = game.get(
            "GameId"
        )

        if not game_id:

            print(
                f"⚠️ 第 {index} 場沒有 GameId，跳過"
            )

            failed_games.append(
                f"第 {index} 場（無 GameId）"
            )

            continue


        print("")
        print(
            "-" * 60
        )
        print(
            f"⚾ 比賽 {index}/{len(games)}："
            f"{game_id}"
        )
        print(
            "-" * 60
        )


        try:

            # 取得詳細資料
            game_data = fetch_game_detail(
                game_id
            )

            # 儲存 today + history
            save_game(
                game_id,
                game_data
            )

            successful_games.append(
                game_data
            )

        except Exception as error:

            print(
                f"❌ {game_id} 更新失敗："
                f"{error}"
            )

            failed_games.append(
                game_id
            )


    # --------------------------------------------------------
    # 6. 更新 live_score.json
    # --------------------------------------------------------

    update_live_score(
        successful_games
    )


    # --------------------------------------------------------
    # 7. 結果統計
    # --------------------------------------------------------

    print("")
    print("=" * 60)
    print("📊 CPBL 更新結果")
    print("=" * 60)

    print(
        f"📅 日期：{today}"
    )

    print(
        f"🏟️ 賽程：{len(games)} 場"
    )

    print(
        f"✅ 成功：{len(successful_games)} 場"
    )

    print(
        f"❌ 失敗：{len(failed_games)} 場"
    )


    # --------------------------------------------------------
    # 8. 如果有任何比賽失敗，讓 GitHub Actions 顯示失敗
    # --------------------------------------------------------

    if failed_games:

        print("")
        print(
            "❌ 以下比賽更新失敗："
        )

        for game_id in failed_games:

            print(
                f"   - {game_id}"
            )

        raise RuntimeError(
            "部分 CPBL 比賽資料更新失敗"
        )


    print("")
    print(
        "🎉 CPBL 資料更新完成！"
    )


# ============================================================
# 程式入口
# ============================================================

if __name__ == "__main__":

    try:

        update_cpbl()

    except Exception as error:

        print("")
        print("=" * 60)
        print("❌ CPBL 自動更新失敗")
        print("=" * 60)
        print(error)

        # 讓 GitHub Actions 判定這次執行失敗
        raise
