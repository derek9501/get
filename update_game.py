import sys
import json
import re
from pathlib import Path

import requests


API_URL = "https://stats.cpbl.com.tw/api/proxy/v1/games/{game_sno}"


def parse_game_sno(game_sno):
    """
    解析場次，例如：
    2026-A-306
    """

    pattern = r"^(\d{4})-([AD])-(\d+)$"
    match = re.match(pattern, game_sno.upper())

    if not match:
        raise ValueError(
            "場次格式錯誤，請使用 YYYY-A-NNN 或 YYYY-D-NNN，例如：2026-A-306"
        )

    year = match.group(1)
    kind_code = match.group(2)
    game_no = match.group(3)

    return year, kind_code, game_no


def update_game(game_sno):
    game_sno = game_sno.strip().upper()

    year, kind_code, game_no = parse_game_sno(game_sno)

    print(f"開始更新指定場次：{game_sno}")

    # CPBL 官方 API
    url = API_URL.format(game_sno=game_sno)

    print(f"讀取官方資料：{url}")

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    data = response.json()

    # 確認有取得資料
    if not data:
        raise ValueError(f"CPBL API 沒有回傳 {game_sno} 的資料")

    # 指定歷史資料位置
    output_dir = Path("history") / kind_code / year
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{game_no}.json"

    # 寫入 JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )
        f.write("\n")

    print(f"更新完成：{output_file}")


def main():
    if len(sys.argv) != 2:
        print("使用方式：")
        print("python update_game.py 2026-A-306")
        sys.exit(1)

    game_sno = sys.argv[1]

    try:
        update_game(game_sno)
    except Exception as e:
        print(f"更新失敗：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
