import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


# ============================================================
# CPBL 自動更新程式
# ============================================================

BASE_URL = "https://stats.cpbl.com.tw/api/proxy/v1"

TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 3

TAIWAN_TZ = timezone(timedelta(hours=8))

ROOT = Path(__file__).resolve().parent


# ============================================================
# 中文 Log
# ============================================================

def log(message):
    now = datetime.now(TAIWAN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}", flush=True)


# ============================================================
# JSON 儲存
# ============================================================

def save_json(path, data):

    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    temp_path.replace(path)

    log(f"💾 已儲存：{path}")


# ============================================================
# API 請求
# ============================================================

def request_json(url):

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            log(f"🌐 API：{url}")
            log(f"🔄 第 {attempt}/{MAX_RETRIES} 次請求")

            response = requests.get(
                url,
                timeout=TIMEOUT,
                headers={
                    "User-Agent":
                        "Mozilla/5.0 CPBL-GitHub-Actions"
                }
            )

            log(f"📡 HTTP：{response.status_code}")

            response.raise_for_status()

            data = response.json()

            log("✅ API 取得成功")

            return data

        except Exception as e:

            log(f"⚠️ API 請求失敗：{e}")

            if attempt < MAX_RETRIES:

                log(
                    f"⏳ {RETRY_DELAY} 秒後重新嘗試"
                )

                time.sleep(RETRY_DELAY)

    raise RuntimeError(
        f"API 請求失敗：{url}"
    )


# ============================================================
# GameSno
#
# CPBL API：
# 2026-A-306
#
# GitHub：
# A/2026/306.json
# ============================================================

def get_game_sno(game):

    possible_keys = [
        "GameSno",
        "gameSno",
        "GameNo",
        "gameNo",
        "GameID",
        "gameId",
        "gameID"
    ]

    if not isinstance(game, dict):
        return None

    for key in possible_keys:

        value = game.get(key)

        if value is None:
            continue

        value = str(value).strip()

        if not value:
            continue

        return value

    return None


# ============================================================
# 取得 KindCode
#
# 例如：
# 2026-A-306
#       ↑
#       A
#
# GitHub：
# history/A/2026/306.json
# ============================================================

def get_kind_code(game_sno, game=None):

    # 先從 GameSno 判斷
    parts = str(game_sno).split("-")

    if len(parts) >= 3:

        return parts[1]

    # 如果 GameSno 格式不正常，再從資料欄位尋找
    if isinstance(game, dict):

        for key in [
            "KindCode",
            "kindCode",
            "GameKind",
            "gameKind",
            "Kind",
            "kind"
        ]:

            value = game.get(key)

            if value:

                return str(value)

    return "A"


# ============================================================
# 從 GameSno 取得年份
#
# 2026-A-306
# ↑
# 2026
# ============================================================

def get_year(game_sno):

    parts = str(game_sno).split("-")

    if len(parts) >= 3:

        return parts[0]

    return datetime.now(TAIWAN_TZ).strftime("%Y")


# ============================================================
# 從 GameSno 取得比賽編號
#
# 2026-A-306
#          ↑
#          306
# ============================================================

def get_game_number(game_sno):

    parts = str(game_sno).split("-")

    if len(parts) >= 3:

        return parts[-1]

    return str(game_sno)


# ============================================================
# 判斷是否為比賽物件
# ============================================================

def is_game_object(value):

    if not isinstance(value, dict):
        return False

    game_sno = get_game_sno(value)

    if not game_sno:
        return False

    # GameSno 通常會包含 -
    if "-" in game_sno:

        parts = game_sno.split("-")

        if len(parts) >= 3:
            return True

    # 某些 API 可能另外提供 GameNo
    game_keys = {
        "GameSno",
        "gameSno",
        "GameNo",
        "gameNo",
        "GameID",
        "gameId"
    }

    return bool(game_keys & set(value.keys()))


# ============================================================
# 遞迴搜尋賽程
# ============================================================

def find_games(obj, path="root"):

    # --------------------------------------------------------
    # List
    # --------------------------------------------------------

    if isinstance(obj, list):

        games = []

        for item in obj:

            if is_game_object(item):
                games.append(item)

        if games:
            return games, path

        # 繼續往下找
        for index, item in enumerate(obj):

            result = find_games(
                item,
                f"{path}[{index}]"
            )

            if result:
                return result

        return None

    # --------------------------------------------------------
    # Dict
    # --------------------------------------------------------

    if isinstance(obj, dict):

        preferred_keys = [
            "data",
            "Data",
            "games",
            "Games",
            "items",
            "Items",
            "result",
            "Result",
            "records",
            "Records",
            "rows",
            "Rows",
            "list",
            "List"
        ]

        # 優先尋找常見欄位
        for key in preferred_keys:

            if key in obj:

                result = find_games(
                    obj[key],
                    f"{path}.{key}"
                )

                if result:
                    return result

        # 再掃描其他欄位
        for key, value in obj.items():

            if key in preferred_keys:
                continue

            result = find_games(
                value,
                f"{path}.{key}"
            )

            if result:
                return result

    return None


# ============================================================
# 取得今日賽程
# ============================================================

def fetch_today_schedule(date_string):

    url = (
        f"{BASE_URL}/games/schedule/"
        f"{date_string}"
    )

    log("=" * 60)
    log(f"📅 查詢日期：{date_string}")
    log("⚾ 查詢 CPBL 今日賽程")
    log("=" * 60)

    data = request_json(url)

    result = find_games(data)

    if result is None:

        log("❌ API 有回應")
        log("❌ 但是找不到 GameSno 賽程資料")
        log("❌ 不會把這種情況判定成「今日沒有比賽」")

        try:

            preview = json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            )

            if len(preview) > 5000:
                preview = preview[:5000]

            print(preview)

        except Exception:
            pass

        raise RuntimeError(
            "無法解析 CPBL 今日賽程 API"
        )

    games, path = result

    log(f"🔎 找到賽程位置：{path}")
    log(f"⚾ 今日共有 {len(games)} 場比賽")

    return data, games


# ============================================================
# 取得單場詳細資料
#
# 例如：
#
# https://stats.cpbl.com.tw/api/proxy/v1/games/2026-A-306
# ============================================================

def fetch_game_detail(game_sno):

    url = (
        f"{BASE_URL}/games/"
        f"{game_sno}"
    )

    log(f"📊 取得單場資料：{game_sno}")

    return request_json(url)


# ============================================================
# 建立 GitHub Pages 歷史網址
#
# API：
# 2026-A-306
#
# GitHub：
# A/2026/306.json
# ============================================================

def github_history_url(game_sno):

    year = get_year(game_sno)

    kind = get_kind_code(game_sno)

    number = get_game_number(game_sno)

    return (
        "https://derek9501.github.io/get/history/"
        f"{kind}/{year}/{number}.json"
    )


# ============================================================
# 處理單場比賽
# ============================================================

def process_game(game):

    game_sno = get_game_sno(game)

    if not game_sno:

        raise RuntimeError(
            "找不到 GameSno"
        )

    year = get_year(game_sno)
    kind = get_kind_code(game_sno)
    number = get_game_number(game_sno)

    log("=" * 60)
    log(f"⚾ 比賽：{game_sno}")
    log(f"📅 年份：{year}")
    log(f"🏷️ 類別：{kind}")
    log(f"🔢 比賽編號：{number}")

    # --------------------------------------------------------
    # 正確 CPBL API
    # --------------------------------------------------------

    api_url = (
        f"{BASE_URL}/games/"
        f"{game_sno}"
    )

    log(f"🌐 CPBL API：{api_url}")

    detail = fetch_game_detail(game_sno)

    # --------------------------------------------------------
    # today
    # --------------------------------------------------------

    save_json(
        ROOT
        / "today"
        / f"{game_sno}.json",
        detail
    )

    # --------------------------------------------------------
    # history
    #
    # history/A/2026/306.json
    # --------------------------------------------------------

    history_path = (
        ROOT
        / "history"
        / kind
        / year
        / f"{number}.json"
    )

    save_json(
        history_path,
        detail
    )

    # --------------------------------------------------------
    # 舊版根目錄
    # --------------------------------------------------------

    save_json(
        ROOT
        / f"{game_sno}.json",
        detail
    )

    # --------------------------------------------------------
    # GitHub Pages 網址
    # --------------------------------------------------------

    github_url = github_history_url(
        game_sno
    )

    log(f"🔗 GitHub Pages：{github_url}")

    log(f"✅ {game_sno} 更新成功")

    return detail


# ============================================================
# 主程式
# ============================================================

def main():

    log("=" * 60)
    log("⚾ CPBL 自動更新程式")
    log("=" * 60)

    now = datetime.now(TAIWAN_TZ)

    today = now.strftime("%Y-%m-%d")

    log(
        f"🇹🇼 台灣時間："
        f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    log(f"📅 今日：{today}")

    # --------------------------------------------------------
    # 今日賽程
    # --------------------------------------------------------

    schedule_data, games = fetch_today_schedule(
        today
    )

    # --------------------------------------------------------
    # 儲存賽程
    # --------------------------------------------------------

    save_json(
        ROOT
        / "schedule"
        / f"{today}.json",
        schedule_data
    )

    save_json(
        ROOT
        / "schedule.json",
        schedule_data
    )

    save_json(
        ROOT
        / "today-schedule.json",
        schedule_data
    )

    save_json(
        ROOT
        / "today"
        / "schedule.json",
        schedule_data
    )

    # --------------------------------------------------------
    # 真的沒有比賽
    # --------------------------------------------------------

    if not games:

        log("ℹ️ CPBL API 明確表示今日沒有比賽")
        log("✅ 賽程更新完成")

        return 0

    # --------------------------------------------------------
    # 更新每場比賽
    # --------------------------------------------------------

    success = 0
    failed = 0

    first_detail = None

    for index, game in enumerate(
        games,
        start=1
    ):

        log(
            f"📌 開始處理 "
            f"{index}/{len(games)}"
        )

        try:

            detail = process_game(game)

            success += 1

            if first_detail is None:

                first_detail = detail

        except Exception as e:

            failed += 1

            log(
                f"❌ 比賽更新失敗：{e}"
            )

    # --------------------------------------------------------
    # live_score.json
    # --------------------------------------------------------

    if first_detail is not None:

        save_json(
            ROOT / "live_score.json",
            first_detail
        )

        log("📺 live_score.json 已更新")

    # --------------------------------------------------------
    # 結果
    # --------------------------------------------------------

    log("=" * 60)
    log("📊 更新結果")
    log("=" * 60)

    log(f"⚾ 今日比賽：{len(games)}")
    log(f"✅ 成功：{success}")
    log(f"❌ 失敗：{failed}")

    if success == 0:

        log("❌ 所有比賽都更新失敗")

        return 1

    if failed > 0:

        log("⚠️ 有部分比賽更新失敗")

        return 1

    log("🎉 CPBL 資料全部更新完成！")

    return 0


# ============================================================
# 程式入口
# ============================================================

if __name__ == "__main__":

    try:

        sys.exit(main())

    except KeyboardInterrupt:

        log("⛔ 程式被中止")

        sys.exit(1)

    except Exception as e:

        log("=" * 60)
        log("💥 程式發生錯誤")
        log(f"💥 {e}")
        log("=" * 60)

        sys.exit(1)
