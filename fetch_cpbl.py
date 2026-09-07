#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CPBL 即時資料自動更新程式

功能：
1. 取得台灣時間今天的賽程
2. 取得每場比賽詳細資料
3. 儲存 today、schedule、history 資料
4. 更新 schedule.json、today-schedule.json、live_score.json
5. 輸出中文化執行紀錄
6. API 失敗時自動重試
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import requests


# ============================================================
# 基本設定
# ============================================================

BASE_URL = "https://stats.cpbl.com.tw/api/proxy/v1"

ROOT = Path(__file__).resolve().parent

TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 3

# 台灣 UTC+8
TAIWAN_TZ = timezone(timedelta(hours=8))


# ============================================================
# 時間與輸出
# ============================================================

def now_tw() -> datetime:
    """取得目前台灣時間。"""
    return datetime.now(TAIWAN_TZ)


def log(message: str) -> None:
    """輸出帶有台灣時間的中文訊息。"""
    print(
        f"[{now_tw():%Y-%m-%d %H:%M:%S}] {message}",
        flush=True
    )


def separator(char: str = "=", length: int = 62) -> None:
    print(char * length, flush=True)


# ============================================================
# API
# ============================================================

def request_json(url: str, description: str) -> Any:
    """
    取得 JSON。
    如果失敗，會自動重試。
    """

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            log(
                f"🌐 正在{description}"
                f"（第 {attempt}/{MAX_RETRIES} 次）"
            )

            response = requests.get(
                url,
                timeout=TIMEOUT,
                headers={
                    "User-Agent": "CPBL-Live-Tracker/1.0",
                    "Accept": "application/json",
                },
            )

            response.raise_for_status()

            data = response.json()

            log("✅ API 回應成功")

            return data

        except (requests.RequestException, ValueError) as error:

            last_error = error

            log(f"⚠️ 取得資料失敗：{error}")

            if attempt < MAX_RETRIES:

                log(
                    f"🔄 {RETRY_DELAY} 秒後重新嘗試……"
                )

                time.sleep(RETRY_DELAY)

    raise RuntimeError(
        f"{description}失敗：{last_error}"
    )


# ============================================================
# JSON 儲存
# ============================================================

def save_json(path: Path, data: Any) -> None:
    """
    使用 UTF-8 儲存 JSON。
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

        file.write("\n")

    temporary_path.replace(path)

    try:
        relative_path = path.relative_to(ROOT)
    except ValueError:
        relative_path = path

    log(f"💾 已儲存：{relative_path}")


# ============================================================
# API 資料解析
# ============================================================

def read_value(
    item: dict[str, Any],
    *keys: str
) -> Any:

    for key in keys:

        if (
            key in item
            and item[key] not in (None, "")
        ):
            return item[key]

    return None


def get_game_id(
    game: dict[str, Any]
) -> str | None:

    value = read_value(
        game,
        "GameSno",
        "gameSno",
        "GameNo",
        "gameNo",
        "GameID",
        "gameId",
        "id",
    )

    if value is None:
        return None

    return str(value)


def get_game_kind(
    game: dict[str, Any]
) -> str:

    value = read_value(
        game,
        "KindCode",
        "kindCode",
        "GameKind",
        "gameKind",
        "kind",
    )

    return str(value or "A")


def get_games(
    schedule_data: Any
) -> list[dict[str, Any]]:

    # API 直接回傳陣列
    if isinstance(schedule_data, list):

        return [
            item
            for item in schedule_data
            if isinstance(item, dict)
        ]

    # API 回傳物件
    if not isinstance(schedule_data, dict):
        return []

    possible_keys = (
        "data",
        "Data",
        "games",
        "Games",
        "items",
        "Items",
        "result",
        "Result",
    )

    for key in possible_keys:

        value = schedule_data.get(key)

        if isinstance(value, list):

            return [
                item
                for item in value
                if isinstance(item, dict)
            ]

    return []


# ============================================================
# 取得賽程
# ============================================================

def fetch_today_schedule(
    date_text: str
) -> Any:

    url = (
        f"{BASE_URL}/games/schedule/"
        f"{date_text}"
    )

    return request_json(
        url,
        "取得今日賽程"
    )


# ============================================================
# 取得單場比賽
# ============================================================

def fetch_game_detail(
    game_id: str
) -> Any:

    url = (
        f"{BASE_URL}/games/"
        f"{game_id}"
    )

    return request_json(
        url,
        f"取得比賽 {game_id} 的詳細資料"
    )


# ============================================================
# 儲存單場比賽
# ============================================================

def save_game_data(
    game: dict[str, Any],
    detail: Any,
    date_text: str
) -> None:

    game_id = get_game_id(game)

    if not game_id:

        raise ValueError(
            "賽程資料缺少比賽編號"
        )

    kind = get_game_kind(game)

    year = date_text[:4]

    # ----------------------------------------
    # 今日資料
    # ----------------------------------------

    save_json(
        ROOT
        / "today"
        / f"{game_id}.json",
        detail
    )

    # ----------------------------------------
    # 歷史資料
    # ----------------------------------------

    history_path = (
        ROOT
        / "history"
        / kind
        / year
        / f"{game_id}.json"
    )

    save_json(
        history_path,
        detail
    )

    # ----------------------------------------
    # 根目錄舊格式
    # ----------------------------------------

    save_json(
        ROOT
        / f"{game_id}.json",
        detail
    )


# ============================================================
# 更新 live_score.json
# ============================================================

def update_live_score(
    details: list[Any]
) -> None:

    if details:

        save_json(
            ROOT / "live_score.json",
            details[0]
        )

    else:

        log(
            "ℹ️ 今天沒有可更新的比賽詳細資料"
        )


# ============================================================
# 主程式
# ============================================================

def main() -> int:

    start_time = time.monotonic()

    date_text = now_tw().strftime(
        "%Y-%m-%d"
    )

    # ========================================================
    # 開始
    # ========================================================

    separator()

    print(
        "       ⚾ CPBL 即時資料自動更新程式",
        flush=True
    )

    separator()

    log(
        f"🇹🇼 台灣時間："
        f"{now_tw():%Y-%m-%d %H:%M:%S}"
    )

    log(
        f"📅 今日日期：{date_text}"
    )

    log(
        "🚀 開始執行 CPBL 資料更新"
    )

    try:

        # ====================================================
        # 取得今日賽程
        # ====================================================

        separator("-")

        log("📋 第 1 步：取得今日賽程")

        separator("-")

        schedule_data = fetch_today_schedule(
            date_text
        )

        games = get_games(
            schedule_data
        )

        log(
            f"🏟️ 今日共有 "
            f"{len(games)} 場比賽"
        )

        # ====================================================
        # 儲存賽程
        # ====================================================

        separator("-")

        log("💾 第 2 步：儲存今日賽程")

        separator("-")

        save_json(
            ROOT
            / "schedule"
            / f"{date_text}.json",
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
            ROOT
            / "today"
            / "schedule.json",
            schedule_data
        )

        # ====================================================
        # 沒有比賽
        # ====================================================

        if not games:

            log(
                "ℹ️ 今天沒有比賽"
            )

            update_live_score([])

            elapsed = (
                time.monotonic()
                - start_time
            )

            separator()

            log(
                "🎉 CPBL 資料更新完成！"
            )

            log(
                f"⏱️ 總執行時間："
                f"{elapsed:.2f} 秒"
            )

            separator()

            return 0

        # ====================================================
        # 取得比賽詳細資料
        # ====================================================

        separator("-")

        log(
            "📡 第 3 步：取得比賽詳細資料"
        )

        separator("-")

        success_count = 0
        failure_count = 0

        details = []
        errors = []

        # ----------------------------------------------------
        # 一場一場處理
        # ----------------------------------------------------

        for index, game in enumerate(
            games,
            start=1
        ):

            game_id = (
                get_game_id(game)
                or f"第 {index} 場"
            )

            log(
                f"⚾ [{index}/{len(games)}]"
                f" 開始處理比賽：{game_id}"
            )

            try:

                # 取得詳細資料
                detail = fetch_game_detail(
                    game_id
                )

                # 儲存
                save_game_data(
                    game,
                    detail,
                    date_text
                )

                details.append(
                    detail
                )

                success_count += 1

                log(
                    f"✅ [{index}/{len(games)}]"
                    f" 比賽 {game_id}"
                    f" 處理完成"
                )

            except Exception as error:

                failure_count += 1

                errors.append(
                    f"{game_id}: {error}"
                )

                log(
                    f"❌ [{index}/{len(games)}]"
                    f" 比賽 {game_id}"
                    f" 處理失敗：{error}"
                )

        # ====================================================
        # 更新即時比分
        # ====================================================

        separator("-")

        log(
            "📡 第 4 步：更新即時比分"
        )

        separator("-")

        update_live_score(
            details
        )

        # ====================================================
        # 統計
        # ====================================================

        separator("-")

        log(
            "📊 第 5 步：更新結果統計"
        )

        separator("-")

        log(
            f"✅ 成功：{success_count} 場"
        )

        log(
            f"❌ 失敗：{failure_count} 場"
        )

        # ====================================================
        # 錯誤清單
        # ====================================================

        if errors:

            log("⚠️ 失敗清單：")

            for error in errors:

                log(
                    f"   └─ {error}"
                )

        # ====================================================
        # 完成
        # ====================================================

        elapsed = (
            time.monotonic()
            - start_time
        )

        separator()

        if failure_count:

            log(
                "💥 CPBL 資料更新未完全成功"
            )

            log(
                f"⏱️ 總執行時間："
                f"{elapsed:.2f} 秒"
            )

            separator()

            return 1

        log(
            "🎉 CPBL 資料更新完成！"
        )

        log(
            f"🕐 完成時間："
            f"{now_tw():%Y-%m-%d %H:%M:%S}"
        )

        log(
            f"⏱️ 總執行時間："
            f"{elapsed:.2f} 秒"
        )

        separator()

        return 0

    except Exception as error:

        separator()

        log(
            f"💥 程式執行失敗：{error}"
        )

        log(
            "🔍 請檢查 CPBL API、"
            "網路連線及資料夾權限"
        )

        separator()

        return 1


# ============================================================
# 程式入口
# ============================================================

if __name__ == "__main__":
    sys.exit(main())
