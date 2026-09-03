import os
import json
import requests

GOOGLE_TAG_SCRIPT = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-01KQHNLNQQ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-01KQHNLNQQ');
</script>"""

def build_site():
    html_template = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    {GOOGLE_TAG_SCRIPT}
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CPBL 數據歷史紀錄</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="bg-light">
    <div class="container py-4">
        <h1 class="mb-4 text-center">中華職棒對戰數據紀錄</h1>
        <div id="app"></div>
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    print("index.html 已成功生成並嵌入新的 Google Tag！")

if __name__ == "__main__":
    build_site()
