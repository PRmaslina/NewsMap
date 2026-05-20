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

def parse_single_date(query):
    import re
    patterns = [
        r'(\d{2})[\.\-/](\d{2})[\.\-/](\d{4})',  # ä.ì.ã
        r'(\d{4})[\.\-/](\d{2})[\.\-/](\d{2})',  # ã-ì-ä
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            try:
                if len(match.group(1)) == 4:
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                else:
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return datetime(year, month, day).date()
            except:
                pass
    return None


def parse_date_range(query):
    import re
    pattern = r'(\d{2})[\.\-/](\d{2})[\.\-/](\d{4})\s*[-–]\s*(\d{2})[\.\-/](\d{2})[\.\-/](\d{4})'
    match = re.search(pattern, query)
    
    if match:
        try:
            day1, month1, year1 = int(match.group(1)), int(match.group(2)), int(match.group(3))
            day2, month2, year2 = int(match.group(4)), int(match.group(5)), int(match.group(6))
            
            date_from = datetime(year1, month1, day1).date()
            date_to = datetime(year2, month2, day2).date()
            return date_from, date_to
        except:
            pass
    return None, None

@app.route('/')
def index():
    fresh_news = filter_news_by_date(get_news(), days=3)
    generate_map(fresh_news)
    return render_template("website.html", news_list=fresh_news, selected_news_id=None)

@app.route('/search', methods=['POST'])
def search():
    query = (request.form.get('query', '') or '').strip().lower()
    lat, lon = None, None
    filtered_news = []
    date_info = None 
    
    all_news = get_news()

    date_from, date_to = parse_date_range(query)
    
    if date_from and date_to:
        for news in all_news:
            try:
                news_date = datetime.strptime(news.get('published_at', '').split('T')[0], '%Y-%m-%d').date()
                if date_from <= news_date <= date_to:
                    filtered_news.append(news)
            except:
                continue
        generate_map(filtered_news)
        date_info = f"{date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')}"
        
        return render_template(
            "website.html",
            news_list=filtered_news,
            search_query=query,
            selected_news_id=None,
            date_info=date_info
        )
    
    single_date = parse_single_date(query)
    
    if single_date:
        for news in all_news:
            try:
                news_date = datetime.strptime(news.get('published_at', '').split('T')[0], '%Y-%m-%d').date()
                if news_date == single_date:
                    filtered_news.append(news)
            except:
                continue
        generate_map(filtered_news)
        date_info = f"{single_date.strftime('%d.%m.%Y')}"
        
        return render_template(
            "website.html",
            news_list=filtered_news,
            search_query=query,
            selected_news_id=None,
            date_info=date_info
        )
    
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
        selected_news_id=None,
        date_info=None
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