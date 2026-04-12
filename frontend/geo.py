import folium
import os



def generate_map(news_list, selected_news_id=None, save_path="static/map.html"):
    if not news_list:
        return False

    # центр карты
    center_lat, center_lon = 55.75, 37.61
    if selected_news_id:
        for news in news_list:
            if news.get('id') == selected_news_id and news.get('latitude'):
                center_lat = news['latitude']
                center_lon = news['longitude']
                break
    else:
        for news in news_list: #центрировать по  IP
            if news.get('latitude'):
                center_lat = news['latitude']
                center_lon = news['longitude']
                break

    # карта
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

    # метки
    for news in news_list:
        if not news.get('latitude'):
            continue

        is_selected = (selected_news_id is not None and news['id'] == selected_news_id)
        icon_color = 'red' if is_selected else 'blue'

        popup_text = f"""
        <b>{news['title'][:100]}</b><br>
        📍 {news['place']}<br>
        🕐 {news['date']}<br>
        <a href="{news['url']}" target="_blank">Читать</a>
        """

        folium.Marker(
            location=[news['latitude'], news['longitude']],
            popup=popup_text,
            tooltip=news['title'][:50],
            icon=folium.Icon(color=icon_color, icon='info-sign', prefix='glyphicon')
        ).add_to(m)

    os.makedirs("static", exist_ok=True)
    m.save(save_path)
    return True
