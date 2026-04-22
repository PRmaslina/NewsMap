from datetime import *
import re
from geopy.geocoders import Nominatim
from flask import *
from geo import generate_map
import requests
from urllib import parse as urlifyer

app = Flask(__name__)


locator = Nominatim(user_agent="my_news_app")
BACKEND_URL = "http://backend:8000"

def get_news(query: str = ''):
    url = f"{BACKEND_URL}/articles"
    if query:
        url += "?query=" + urlifyer.quote(query)
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def filter_news_by_date(all_news, days):
    start_date = datetime.now() - timedelta(days=days)
    filtered_news = []
    for news in all_news:
        date_of_news = news.get('date', ' ')
        normal_date = datetime.strptime(date_of_news.split('T')[0], '%Y-%m-%d')
        if normal_date >= start_date:
            filtered_news.append(news)
    return filtered_news


@app.route('/')
def index():
    fresh_news = filter_news_by_date(get_news(), days=3)
    generate_map(fresh_news)
    return render_template("website.html", news_list=fresh_news, selected_news_id=None)

@app.route('/search', methods=['POST'])
def search():
    query = (request.form.get('query', '') or '').strip().lower()
    lat, lon = None, None
    filtered_news = get_news(query)

    if query:
        location = locator.geocode(query)
        if location:
            lat, lon = location.latitude, location.longitude


    if lat and lon:
        generate_map(filtered_news, center_lat=lat, center_lon=lon, center_zoom=8)
    else:
        generate_map(filtered_news)

    return render_template(
        "website.html",
        news_list=filtered_news,
        search_query=query,
        selected_news_id=None
    )

@app.route('/news/<int:news_id>')
def show_news(news_id):
    try:
        resp = requests.get(f"{BACKEND_URL}/articles/{news_id}", timeout=5)
        selected_news = resp.json()
    except:
        selected_news = None
    all_news = get_news()
    for news in all_news:
        if news['id'] == news_id:
            selected_news = news
            break

    if selected_news:
        generate_map([selected_news], selected_news_id=news_id)
        return render_template("website.html", news_list=[selected_news], selected_news_id=news_id)
    else:
        return redirect(url_for('website'))


if __name__ == '__main__':
    app.run(debug=True)