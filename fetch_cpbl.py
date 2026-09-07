import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

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
# 基本工具
# ============================================================

def log(message: str):
    """輸出中文時間紀錄"""
    now = datetime.now(TAIWAN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def save_json(path: Path, data: Any):
    """安全寫入 JSON"""
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

    log(f"💾 已寫入：{path}")


def read_value(data: dict, keys):
    """從多種可能欄位名稱取得值"""

    for key in keys:
        if key in data:
            value = data[key]

            if value is not None and value != "":
                return value

    return None


# ============================================================
# API
# ============================================================

def request_json(url: str):
    """取得 API JSON，失敗自動重試"""

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            log(f"🌐 API 請求：{url}")
            log(f"🔄 第 {attempt}/{MAX_RETRIES} 次嘗試")

            response = requests.get(
                url,
                timeout=TIMEOUT,
                headers={
                    "User-Agent": "Mozilla/5.0 CPBL-GitHub-Actions"
                }
            )

            log(f"📡 HTTP 狀態碼：{response.status_code}")

            response.raise_for_status()

            data = response.json()

            log("✅ API JSON 取得成功")

            return data

        except Exception as e:

            log(f"⚠️ API 請求失敗：{e}")

            if attempt < MAX_RETRIES:
                log(f"⏳ {RETRY_DELAY} 秒後重新嘗試...")
                time.sleep(RETRY_DELAY)

    raise RuntimeError(f"API 請求失敗：{url}")


# ============================================================
# 遊戲資料判斷
# ============================================================

GAME_ID_KEYS = [
    "GameSno",
    "gameSno",
    "GameNo",
    "gameNo",
    "GameID",
    "gameId",
    "gameID",
    "id"
]


def get_game_id(game: dict):

    return read_value(
        game,
        GAME_ID_KEYS
    )


def get_game_kind(game: dict):

    return read_value(
        game,
        [
            "KindCode",
            "kindCode",
            "GameKind",
            "gameKind",
            "kind",
            "Kind"
        ]
    )


def is_game_object(value):

    if not isinstance(value, dict):
        return False

    game_id = get_game_id(value)

    if game_id is None:
        return False

    # 避免把一般 id 物件誤認成比賽
    keys = set(value.keys())

    game_related_keys = {
        "GameSno",
        "gameSno",
        "GameNo",
        "gameNo",
        "GameID",
        "gameId",
        "GameDate",
        "gameDate",
        "HomeTeam",
        "homeTeam",
        "AwayTeam",
        "awayTeam",
        "HomeTeamName",
        "AwayTeamName",
        "HomeTeamCode",
        "AwayTeamCode",
        "KindCode",
        "kindCode"
    }

    return bool(keys & game_related_keys)


# ============================================================
# 遞迴尋找賽程
# ============================================================

def find_game_list(obj, path="root"):
    """
    不管 API JSON 巢狀幾層，
    自動尋找真正的「比賽陣列」。
    """

    # --------------------------------------------------------
    # 如果本身就是 list
    # --------------------------------------------------------

    if isinstance(obj, list):

        game_items = [
            item
            for item in obj
            if is_game_object(item)
        ]

        if game_items:

            return game_items, path

        # 繼續往更深層尋找
        for index, item in enumerate(obj):

            result = find_game_list(
                item,
                f"{path}[{index}]"
            )

            if result is not None:
                return result

        return None

    # --------------------------------------------------------
    # 如果本身是 dict
    # --------------------------------------------------------

    if isinstance(obj, dict):

        # 先檢查常見欄位
        preferred_keys = [
            "data",
            "Data",
            "games",
            "Games",
            "items",
            "Items",
            "result",
            "Result",
            "list",
            "List",
            "records",
            "Records",
            "rows",
            "Rows"
        ]

        for key in preferred_keys:

            if key in obj:

                result = find_game_list(
                    obj[key],
                    f"{path}.{key}"
                )

                if result is not None:
                    return result

        # 如果常見欄位找不到，再掃描所有欄位
        for key, value in obj.items():

            if key in preferred_keys:
                continue

            result = find_game_list(
                value,
                f"{path}.{key}"
            )

            if result is not None:
                return result

    return None


# ============================================================
# API 結構診斷
# ============================================================

def describe_api_response(data):

    log("🔍 開始分析 API 回應結構")

    if isinstance(data, dict):

        keys = list(data.keys())

        log(f"📦 API 最外層為 dict")
        log(f"🔑 最外層欄位：{keys[:30]}")

    elif isinstance(data, list):

        log(f"📦 API 最外層為 list")
        log(f"📊 陣列長度：{len(data)}")

    else:

        log(f"⚠️ API 回應類型：{type(data).__name__}")


# ============================================================
# 取得今日賽程
# ============================================================

def fetch_today_schedule(date_string):

    url = f"{BASE_URL}/games/schedule/{date_string}"

    log("=" * 60)
    log(f"📅 查詢日期：{date_string}")
    log(f"🌐 查詢今日 CPBL 賽程")
    log("=" * 60)

    data = request_json(url)

    describe_api_response(data)

    # --------------------------------------------------------
    # 找真正的賽程陣列
    # --------------------------------------------------------

    result = find_game_list(data)

    if result is None:

        log("❌ API 有回應，但是找不到賽程陣列")
        log("❌ 因此不能判定為「今日沒有比賽」")
        log("❌ 請檢查 API JSON 結構")

        # 印出部分 JSON 幫助除錯
        try:

            preview = json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            )

            if len(preview) > 5000:
                preview = preview[:5000] + "\n......"

            log("🔎 API 回應前 5000 字：")
            print(preview)

        except Exception:
            pass

        raise RuntimeError(
            "API 有回應，但程式無法解析今日賽程"
        )

    games, found_path = result

    log(f"🎯 找到賽程位置：{found_path}")
    log(f"⚾ 今日共有 {len(games)} 場比賽")

    return data, games


# ============================================================
# 取得單場比賽詳細資料
# ============================================================

def fetch_game_detail(game_id):

    url = f"{BASE_URL}/games/{game_id}"

    log(f"📊 取得比賽詳細資料：GAME {game_id}")

    return request_json(url)


# ============================================================
# 主程式
# ============================================================

def main():

    log("=" * 60)
    log("⚾ CPBL 自動更新程式開始")
    log("=" * 60)

    # --------------------------------------------------------
    # 台灣日期
    # --------------------------------------------------------

    now = datetime.now(TAIWAN_TZ)

    today = now.strftime("%Y-%m-%d")
    year = now.strftime("%Y")

    log(f"🇹🇼 台灣時間：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📅 今日日期：{today}")

    # --------------------------------------------------------
    # 取得今日賽程
    # --------------------------------------------------------

    schedule_data, games = fetch_today_schedule(today)

    # --------------------------------------------------------
    # 保存原始今日賽程
    # --------------------------------------------------------

    save_json(
        ROOT / "schedule" / f"{today}.json",
        schedule_data
    )

    save_json(
        ROOT / "schedule.json",
        schedule_data
    )

    save_json(
        ROOT / "today-schedule.json",
        schedule_data
    )

    save_json(
        ROOT / "today" / "schedule.json",
        schedule_data
    )

    # --------------------------------------------------------
    # 如果真的沒有比賽
    # --------------------------------------------------------

    if len(games) == 0:

        log("ℹ️ API 明確回傳今日沒有比賽")

        log("=" * 60)
        log("✅ 今日賽程更新完成")
        log("=" * 60)

        return 0

    # --------------------------------------------------------
    # 開始處理比賽
    # --------------------------------------------------------

    success_count = 0
    fail_count = 0

    first_success_detail = None

    for index, game in enumerate(games, start=1):

        game_id = get_game_id(game)

        kind = get_game_kind(game)

        if kind is None:
            kind = "A"

        kind = str(kind)

        if game_id is None:

            log(
                f"⚠️ 第 {index} 場找不到 GameSno，跳過"
            )

            fail_count += 1
            continue

        game_id = str(game_id)

        log("=" * 60)
        log(f"⚾ 處理第 {index}/{len(games)} 場")
        log(f"🎮 GAME：{game_id}")
        log(f"🏷️ 類別：{kind}")

        try:

            detail = fetch_game_detail(game_id)

            # ------------------------------------------------
            # 今日資料
            # ------------------------------------------------

            save_json(
                ROOT / "today" / f"{game_id}.json",
                detail
            )

            # ------------------------------------------------
            # 歷史資料
            # ------------------------------------------------

            save_json(
                ROOT
                / "history"
                / kind
                / year
                / f"{game_id}.json",
                detail
            )

            # ------------------------------------------------
            # 舊版根目錄資料
            # ------------------------------------------------

            save_json(
                ROOT / f"{game_id}.json",
                detail
            )

            success_count += 1

            if first_success_detail is None:
                first_success_detail = detail

            log(f"✅ GAME {game_id} 更新成功")

        except Exception as e:

            fail_count += 1

            log(
                f"❌ GAME {game_id} 更新失敗：{e}"
            )

    # --------------------------------------------------------
    # 更新 live_score.json
    # --------------------------------------------------------

    if first_success_detail is not None:

        save_json(
            ROOT / "live_score.json",
            first_success_detail
        )

        log("📺 live_score.json 已更新")

    # --------------------------------------------------------
    # 最終結果
    # --------------------------------------------------------

    log("=" * 60)
    log("📊 CPBL 更新結果")
    log("=" * 60)

    log(f"⚾ 今日比賽：{len(games)} 場")
    log(f"✅ 成功：{success_count} 場")
    log(f"❌ 失敗：{fail_count} 場")

    # --------------------------------------------------------
    # 有比賽但全部失敗
    # --------------------------------------------------------

    if success_count == 0:

        log("❌ 所有比賽資料取得失敗")
        log("❌ GitHub Actions 將標記為失敗")

        return 1

    # --------------------------------------------------------
    # 部分失敗
    # --------------------------------------------------------

    if fail_count > 0:

        log("⚠️ 部分比賽更新失敗")
        log("⚠️ GitHub Actions 將標記為失敗")

        return 1

    # --------------------------------------------------------
    # 全部成功
    # --------------------------------------------------------

    log("=" * 60)
    log("🎉 CPBL 資料更新完成！")
    log("=" * 60)

    return 0


# ============================================================
# 程式入口
# ============================================================

if __name__ == "__main__":

    try:

        exit_code = main()

        sys.exit(exit_code)

    except KeyboardInterrupt:

        log("⛔ 使用者中止程式")
        sys.exit(1)

    except Exception as e:

        log("=" * 60)
        log("💥 程式發生未預期錯誤")
        log(f"💥 {e}")
        log("=" * 60)

        sys.exit(1)
