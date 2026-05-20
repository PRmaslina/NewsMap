from datetime import *
from flask import Flask, request, render_template, url_for, redirect, jsonify, flash
from geo import generate_map
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-fallback-key-12345")

BACKEND_URL = "http://backend:8000"


def parse_single_date(query):
    import re

    patterns = [
        r"(\d{2})[\.\-/](\d{2})[\.\-/](\d{4})",  # ä.ì.ã
        r"(\d{4})[\.\-/](\d{2})[\.\-/](\d{2})",  # ã-ì-ä
    ]

    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            try:
                if len(match.group(1)) == 4:
                    year, month, day = (
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3)),
                    )
                else:
                    day, month, year = (
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3)),
                    )
                return datetime(year, month, day).date()
            except:
                pass
    return None


def parse_date_range(query):
    import re

    pattern = r"(\d{2})[\.\-/](\d{2})[\.\-/](\d{4})\s*[-–]\s*(\d{2})[\.\-/](\d{2})[\.\-/](\d{4})"
    match = re.search(pattern, query)

    if match:
        try:
            day1, month1, year1 = (
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            )
            day2, month2, year2 = (
                int(match.group(4)),
                int(match.group(5)),
                int(match.group(6)),
            )

            date_from = datetime(year1, month1, day1).date()
            date_to = datetime(year2, month2, day2).date()
            return date_from, date_to
        except:
            pass
    return None, None


def get_news():
    url = f"{BACKEND_URL}/articles"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def search_backend(query: str):
    url = f"{BACKEND_URL}/search"

    payload = {
        "query": query,
        "geo_keywords": [],
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

    if not query:
        flash("Введите поисковый запрос 🔍", "info")
        return redirect(url_for("index"))

    fresh_news = search_backend(query)
    lat, lon = None, None
    if fresh_news:
        location = fresh_news[0].location
        lat = location.latitude
        lon = location.longitude
        generate_map(fresh_news, center_lat=lat, center_lon=lon)
    return render_template(
        "website.html", news_list=fresh_news, search_query=query, selected_news_id=None
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
