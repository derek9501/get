import os
import json
import re
from datetime import datetime, timezone, timedelta

def get_tz():
    return timezone(timedelta(hours=8))

def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        return f"{dt.month}/{dt.day} ({weekdays[dt.weekday()]})"
    except Exception:
        return date_str

def generate_html():
    html_content = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CPBL 賽事資訊與對戰歷史</title>
    <style>
        :root {
            --primary-color: #003865;
            --secondary-color: #05549e;
            --bg-color: #f4f6f9;
            --card-bg: #ffffff;
            --text-color: #333333;
            --border-color: #e0e0e0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: var(--primary-color);
        }
        .game-card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .game-header {
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            margin-bottom: 15px;
            font-weight: bold;
        }
        .team-vs {
            display: flex;
            align-items: center;
            justify-content: space-around;
            font-size: 1.2em;
            margin-bottom: 15px;
        }
        .history-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .history-table th, .history-table td {
            border: 1px solid var(--border-color);
            padding: 8px;
            text-align: center;
            font-size: 0.9em;
        }
        .history-table th {
            background-color: #f0f4f8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>CPBL 賽事歷史對戰數據</h1>
        <div id="content"></div>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_html()
