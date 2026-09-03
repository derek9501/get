import os
import json

def generate_date_index(history_dir="history", output_file="date_index.json"):
    """
    掃描 history 資料夾，建立 { "YYYY-MM-DD": ["path/to/game1.json", ...] } 的索引檔
    """
    date_map = {}

    if not os.path.exists(history_dir):
        print(f"⚠️ 找不到目錄：{history_dir}")
        return

    # 遍歷 history 目錄下的所有 JSON 檔
    for root, _, files in os.walk(history_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        # 讀取 JSON 中的日期（支援 common 鍵值名稱）
                        game_date = data.get("date") or data.get("game_date") or data.get("Date")
                        
                        # 取得相對於專案根目錄的相對路徑 (例如: history/A/2026/100.json)
                        relative_path = os.path.relpath(file_path, ".").replace("\\", "/")

                        if game_date:
                            if game_date not in date_map:
                                date_map[game_date] = []
                            if relative_path not in date_map[game_date]:
                                date_map[game_date].append(relative_path)
                except Exception as e:
                    print(f"❌ 讀取 {file_path} 失敗: {e}")

    # 將日期排序後輸出成 json
    sorted_date_map = {k: sorted(date_map[k]) for k in sorted(date_map.keys())}

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sorted_date_map, f, ensure_ascii=False, indent=2)

    print(f"✅ 成功生成日期對照索引檔：{output_file}")

if __name__ == "__main__":
    # 執行生成索引檔
    generate_date_index()
