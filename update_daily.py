import datetime

# 假設這是您原本用來抓取資料的函數
# from fetch_cpbl import get_game_data 

def main():
    # 取得昨天的日期
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    print(f"正在檢查 {yesterday} 的比賽資料...")

    # 執行抓取邏輯 (請替換為您實際的函數)
    # game_data = get_game_data(yesterday)
    game_data = [] # 這裡以空陣列模擬無比賽的狀況

    # 判斷無比賽日
    if not game_data:
        print("判斷結果：無比賽日，無資料需更新。")
        return

    # 若有比賽，執行後續儲存或更新邏輯
    print("已取得比賽資料，更新成功！")
    # save_data(game_data)

if __name__ == "__main__":
    main()
