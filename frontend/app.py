from flask import *
import geo
import requests
from urllib import parse as urlifyer

app = Flask(__name__)


BACKEND_URL = "http://backend:8000"

def get_news(query: str = ''):
    url = f"{BACKEND_URL}/articles"
    if query:
        url += "?query=" + urlifyer.quote(query)
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

@app.route('/')
def index():
    news_list = get_news()
    geo.generate_map(news_list)
    return render_template("website.html", news_list=news_list, selected_news_id=None)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '').strip()
    news_list = get_news(query)
    geo.generate_map(news_list)
    return render_template("website.html", news_list=news_list, search_query=query, selected_news_id=None)

@app.route('/news/<int:news_id>')
def show_news(news_id):
    resp = requests.get(f"{BACKEND_URL}/articles/{news_id}")
    selected_news = resp.json()
    all_news = get_news()
    geo.generate_map(all_news, selected_news_id=news_id)
    return render_template("website.html", news_list=all_news, selected_news_id=news_id)

if __name__ == '__main__':
    app.run(debug=True)