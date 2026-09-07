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
# 儲存 JSON
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

            log(f"🌐 請求 API：{url}")
            log(f"🔄 第 {attempt}/{MAX_RETRIES} 次")

            response = requests.get(
                url,
                timeout=TIMEOUT,
                headers={
                    "User-Agent":
                        "Mozilla/5.0 CPBL-GitHub-Actions"
                }
            )

            log(
                f"📡 HTTP 狀態碼："
                f"{response.status_code}"
            )

            response.raise_for_status()

            data = response.json()

            log("✅ API JSON 取得成功")

            return data

        except Exception as e:

            log(f"⚠️ API 取得失敗：{e}")

            if attempt < MAX_RETRIES:

                log(
                    f"⏳ {RETRY_DELAY} 秒後重新嘗試"
                )

                time.sleep(RETRY_DELAY)

    raise RuntimeError(
        f"API 請求失敗：{url}"
    )


# ============================================================
# 取得 GameSno
#
# 正確格式：
#
# 2026-A-306
#
# 不能只使用：
#
# 306
# ============================================================

def get_game_sno(game):

    if not isinstance(game, dict):
        return None

    possible_keys = [
        "GameSno",
        "gameSno",
        "GameID",
        "gameId",
        "gameID",
        "GameNo",
        "gameNo"
    ]

    value = None

    for key in possible_keys:

        if key in game:

            if game[key] not in (None, ""):

                value = str(game[key]).strip()

                break

    if not value:
        return None

    # --------------------------------------------------------
    # 如果本身就是完整 GameSno
    #
    # 例如：
    # 2026-A-306
    # --------------------------------------------------------

    if value.count("-") >= 2:

        return value

    # --------------------------------------------------------
    # 如果只有 306
    # 就補年份與賽事類型
    # --------------------------------------------------------

    year = None
    kind = None

    # 年份
    for key in [
        "Year",
        "year",
        "Season",
        "season"
    ]:

        if game.get(key) not in (None, ""):

            year = str(game[key]).strip()

            break

    # 賽事類別
    for key in [
        "KindCode",
        "kindCode",
        "GameKind",
        "gameKind",
        "Kind",
        "kind"
    ]:

        if game.get(key) not in (None, ""):

            kind = str(game[key]).strip()

            break

    # 如果沒有年份
    if not year:

        year = datetime.now(
            TAIWAN_TZ
        ).strftime("%Y")

    # 如果沒有類別
    if not kind:

        kind = "A"

    return f"{year}-{kind}-{value}"


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

    return datetime.now(
        TAIWAN_TZ
    ).strftime("%Y")


# ============================================================
# 從 GameSno 取得 KindCode
#
# 2026-A-306
#      ↑
#      A
# ============================================================

def get_kind_code(game_sno):

    parts = str(game_sno).split("-")

    if len(parts) >= 3:

        return parts[1]

    raise RuntimeError(
        f"GameSno 格式錯誤：{game_sno}"
    )


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

    raise RuntimeError(
        f"GameSno 格式錯誤：{game_sno}"
    )


# ============================================================
# 判斷是否為比賽資料
# ============================================================

def is_game_object(value):

    if not isinstance(value, dict):

        return False

    game_sno = get_game_sno(value)

    if not game_sno:

        return False

    # 必須是完整 GameSno
    if game_sno.count("-") >= 2:

        return True

    return False


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

        # 繼續往內搜尋
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

        # 先搜尋常見欄位
        for key in preferred_keys:

            if key in obj:

                result = find_games(
                    obj[key],
                    f"{path}.{key}"
                )

                if result:

                    return result

        # 再搜尋其他欄位
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

    # --------------------------------------------------------
    # 找不到賽程
    # --------------------------------------------------------

    if result is None:

        log("❌ API 有回應")
        log("❌ 但是找不到有效的 GameSno")
        log("❌ 不會判定成「今日沒有比賽」")

        try:

            preview = json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            )

            if len(preview) > 5000:

                preview = (
                    preview[:5000]
                    + "\n......"
                )

            log("🔎 API 回應：")

            print(
                preview,
                flush=True
            )

        except Exception:

            pass

        raise RuntimeError(
            "CPBL 賽程 API 無法解析"
        )

    games, path = result

    log(f"🔎 找到賽程位置：{path}")
    log(f"⚾ 找到 {len(games)} 場比賽")

    return data, games


# ============================================================
# 取得單場比賽
#
# ★ 這裡強制要求完整 GameSno
#
# 正確：
# /games/2026-A-306
#
# 錯誤：
# /games/306
# ============================================================

def fetch_game_detail(game_sno):

    game_sno = str(game_sno).strip()

    # --------------------------------------------------------
    # 防止錯誤網址
    # --------------------------------------------------------

    if game_sno.count("-") < 2:

        raise RuntimeError(
            "❌ 錯誤 GameSno："
            f"{game_sno}\n"
            "CPBL API 必須使用完整格式："
            "2026-A-306"
        )

    # --------------------------------------------------------
    # 建立正確 API
    # --------------------------------------------------------

    url = (
        f"{BASE_URL}/games/"
        f"{game_sno}"
    )

    log(
        f"🌐 CPBL 正確 API："
        f"{url}"
    )

    return request_json(url)


# ============================================================
# 建立 GitHub Pages 歷史資料網址
#
# CPBL：
# 2026-A-306
#
# GitHub：
# A/2026/306.json
# ============================================================

def get_github_history_url(game_sno):

    year = get_year(game_sno)

    kind = get_kind_code(game_sno)

    number = get_game_number(game_sno)

    return (
        "https://derek9501.github.io/get/"
        f"history/{kind}/{year}/{number}.json"
    )


# ============================================================
# 處理單場比賽
# ============================================================

def process_game(game):

    game_sno = get_game_sno(game)

    if not game_sno:

        raise RuntimeError(
            "❌ 找不到 GameSno"
        )

    # --------------------------------------------------------
    # 最重要的防呆
    # --------------------------------------------------------

    if game_sno.count("-") < 2:

        raise RuntimeError(
            f"❌ GameSno 不完整：{game_sno}"
        )

    year = get_year(game_sno)

    kind = get_kind_code(game_sno)

    number = get_game_number(game_sno)

    log("=" * 60)
    log(f"⚾ GameSno：{game_sno}")
    log(f"📅 年份：{year}")
    log(f"🏷️ 類別：{kind}")
    log(f"🔢 編號：{number}")

    # --------------------------------------------------------
    # CPBL API
    # --------------------------------------------------------

    detail = fetch_game_detail(
        game_sno
    )

    # --------------------------------------------------------
    # 今日資料
    #
    # today/2026-A-306.json
    # --------------------------------------------------------

    save_json(
        ROOT
        / "today"
        / f"{game_sno}.json",
        detail
    )

    # --------------------------------------------------------
    # 歷史資料
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
    # 根目錄
    #
    # 2026-A-306.json
    # --------------------------------------------------------

    save_json(
        ROOT
        / f"{game_sno}.json",
        detail
    )

    # --------------------------------------------------------
    # GitHub Pages
    # --------------------------------------------------------

    github_url = get_github_history_url(
        game_sno
    )

    log(
        f"🔗 GitHub Pages："
        f"{github_url}"
    )

    log(
        f"✅ {game_sno} 更新完成"
    )

    return detail


# ============================================================
# 主程式
# ============================================================

def main():

    log("=" * 60)
    log("⚾ CPBL 自動更新程式開始")
    log("=" * 60)

    # --------------------------------------------------------
    # 台灣時間
    # --------------------------------------------------------

    now = datetime.now(
        TAIWAN_TZ
    )

    today = now.strftime(
        "%Y-%m-%d"
    )

    log(
        "🇹🇼 台灣時間："
        f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    log(
        f"📅 查詢日期：{today}"
    )

    # --------------------------------------------------------
    # 今日賽程
    # --------------------------------------------------------

    schedule_data, games = (
        fetch_today_schedule(today)
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

        log(
            "ℹ️ CPBL API 確認今日沒有比賽"
        )

        log(
            "✅ 賽程更新完成"
        )

        return 0

    # --------------------------------------------------------
    # 更新每一場
    # --------------------------------------------------------

    success = 0
    failed = 0

    first_detail = None

    for index, game in enumerate(
        games,
        start=1
    ):

        log(
            f"📌 處理比賽 "
            f"{index}/{len(games)}"
        )

        try:

            detail = process_game(
                game
            )

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
            ROOT
            / "live_score.json",
            first_detail
        )

        log(
            "📺 live_score.json 已更新"
        )

    # --------------------------------------------------------
    # 最終結果
    # --------------------------------------------------------

    log("=" * 60)
    log("📊 CPBL 更新結果")
    log("=" * 60)

    log(
        f"⚾ 今日比賽：{len(games)} 場"
    )

    log(
        f"✅ 成功：{success} 場"
    )

    log(
        f"❌ 失敗：{failed} 場"
    )

    # --------------------------------------------------------
    # 全部失敗
    # --------------------------------------------------------

    if success == 0:

        log(
            "❌ 所有比賽更新失敗"
        )

        return 1

    # --------------------------------------------------------
    # 部分失敗
    # --------------------------------------------------------

    if failed > 0:

        log(
            "⚠️ 部分比賽更新失敗"
        )

        return 1

    # --------------------------------------------------------
    # 全部成功
    # --------------------------------------------------------

    log("=" * 60)
    log("🎉 CPBL 所有資料更新完成！")
    log("=" * 60)

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
        log("💥 程式發生未預期錯誤")
        log(f"💥 {e}")
        log("=" * 60)

        sys.exit(1)
