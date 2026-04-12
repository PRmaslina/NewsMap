import json
import os
import sys
import time
import requests
from datetime import datetime

BACKEND_URL = "http://backend:8000"

def read_news_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_date(date_str):
    if not date_str:
        return None
    if ',' in date_str:
        date_part = date_str.split(',', 1)[1].strip()
    else:
        date_part = date_str.strip()
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    for ru_month, num in months.items():
        if ru_month in date_part:
            remaining = date_part.replace(ru_month, '').strip()
            parts = remaining.split()
            if len(parts) >= 2:
                day = parts[0].strip()
                year = parts[1].strip()
                try:
                    return datetime(int(year), num, int(day)).date().isoformat()
                except:
                    pass
    return None

def send_article(article, verbose=True):
    url = f"{BACKEND_URL}/articles"
    payload = {
        "url": article.get("link"),
        "title": article.get("title"),
        "subtitle": article.get("subTitle"),
        "position": article.get("position"),
        "date": parse_date(article.get("date")),
        "tags": article.get("tags")
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            if verbose:
                print(f"Добавлена")
            return True
        elif resp.status_code == 400 and "already exists" in resp.text:
            if verbose:
                print(f"Уже есть")
            return True
        else:
            if verbose:
                print(f"Ошибка {resp.status_code}")
            return False
    except Exception as err:
        if verbose:
            print(f"Исключение: {err}")
        return False

def main():
    json_path = os.path.join("News.json")
    try:
        news_list = read_news_json(json_path)
    except json.JSONDecodeError as err:
        print(f"Ошибка JSON: {err}")
        sys.exit(1)

    total = len(news_list)
    print(f"Найдено новостей: {total}")

    success_count = 0
    for idx, item in enumerate(news_list, 1):
        print(f"\n[{idx}/{total}] {item.get('title', '')[:60]}...")
        if send_article(item):
            success_count += 1
        time.sleep(0.5)

    print(f"\nзагружено: {success_count} из {total}")

if __name__ == "__main__":
    main()