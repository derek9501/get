import requests
import json

url = "https://www.cpbl.com.tw/box/getlive"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.cpbl.com.tw/box/index?year=2026&kindCode=D&gameSno=88",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://www.cpbl.com.tw",
    "Content-Type": "application/json"
}
payload = {
    "year": "2026",
    "kindCode": "D",
    "gameSno": "88"
}

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    with open("live_score.json", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("成功更新比分資料！")
else:
    print(f"抓取失敗，狀態碼：{response.status_code}")
