from datetime import *
import os
from typing import Optional
import requests

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from geo import generate_map

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-fallback-key-12345")

BACKEND_URL = "http://backend:8000"


def get_news():
    url = f"{BACKEND_URL}/articles"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def search_backend(
    query: str, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
):
    url = f"{BACKEND_URL}/search"
    if isinstance(date_from, datetime):
        date_from = date_from.isoformat()  # type: ignore
    if isinstance(date_to, datetime):
        date_to = date_to.isoformat()  # type: ignore
    payload = {
        "query": query,
        "date_range": {"date_from": date_from, "date_to": date_to},
        "min_relevance": 0.1,
        "limit": 50,
    }
    resp = requests.post(url, json=payload, timeout=5)
    resp.raise_for_status()
    return resp.json().get("articles", [])


def filter_news_by_date(all_news, days):
    start_date = datetime.now() - timedelta(days=days)
    filtered_news = []
    for news in all_news:
        date_of_news = news.get("published_at", " ")
        normal_date = datetime.strptime(date_of_news.split("T")[0], "%Y-%m-%d")
        if normal_date >= start_date:
            filtered_news.append(news)
    return filtered_news


@app.route("/")
def index():
    fresh_news = filter_news_by_date(get_news(), days=3)
    generate_map(fresh_news)
    return render_template("website.html", news_list=fresh_news, selected_news_id=None)


@app.route("/search", methods=["POST"])
def search():
    query = (request.form.get("query", "") or "").strip().lower()
    date_from_str = request.form.get("date_from", "")
    date_to_str = request.form.get("date_to", "")

    # 🎯 Дефолтные даты: 2000–2100, если не указаны
    DEFAULT_FROM = datetime(2000, 1, 1)
    DEFAULT_TO = datetime(2100, 12, 31)

    date_from = None
    date_to = None
    date_info = None

    # Парсинг date_from
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
        except ValueError:
            date_from = DEFAULT_FROM  # fallback при ошибке формата
    else:
        date_from = DEFAULT_FROM

    # Парсинг date_to
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
        except ValueError:
            date_to = DEFAULT_TO  # fallback при ошибке формата
    else:
        date_to = DEFAULT_TO

    # Формирование строки для отображения
    if date_from and date_to:
        if date_from == DEFAULT_FROM and date_to == DEFAULT_TO:
            date_info = "📅 Все за время"
        elif date_from == date_to:
            date_info = f"📅 {date_from.strftime('%d.%m.%Y')}"
        else:
            date_info = (
                f"📅 {date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')}"
            )
    filtered_news = search_backend(query, date_from, date_to)
    lat, lon = None, None
    if filtered_news:
        location = filtered_news[0]["location"]
        lat = location["latitude"]
        lon = location["longitude"]
        generate_map(filtered_news, center_lat=lat, center_lon=lon)
    return render_template(
        "website.html",
        news_list=filtered_news,
        search_query=None,
        selected_news_id=None,
        date_info=date_info,
    )


@app.route("/news/<int:news_id>")
def show_news(news_id):
    try:
        resp = requests.get(f"{BACKEND_URL}/articles/{news_id}", timeout=5)
        selected_news = resp.json()
    except:
        selected_news = None
    all_news = get_news()
    for news in all_news:
        if news["id"] == news_id:
            selected_news = news
            break

    if selected_news:
        generate_map([selected_news], selected_news_id=news_id)
        return render_template(
            "website.html", news_list=[selected_news], selected_news_id=news_id
        )
    else:
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
