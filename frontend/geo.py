import folium
from folium.plugins import MarkerCluster
import os
import sys

def generate_map(news_list, selected_news_id=None,center_lat=None, center_lon=None, center_zoom=6, save_path="static/map.html"):
    if not news_list:
        m = folium.Map(location=[55.75, 37.61], zoom_start=6)
        os.makedirs("static", exist_ok=True)
        m.save(save_path)
        return False

    # центр карты
    if center_lat is not None and center_lon is not None:
        lat, lon = center_lat, center_lon
        zoom = center_zoom
    elif selected_news_id:
        for news in news_list:
            if news.get('id') == selected_news_id and news.get('latitude'):
                lat = news['latitude']
                lon = news['longitude']
                zoom = 12
                break
        else:
            lat, lon = 55.75, 37.61
            zoom = 6
    else:
        lat, lon = 55.75, 37.61
        zoom = 6
    offset = 0.002 # сдвиг для координат
    # карта
    m = folium.Map(location=[lat, lon], zoom_start=zoom)
    # метки
    offset = 0.002
    shifted_positions = {}
    used_counts = {}

    for news in news_list:
        if news.get('latitude') is None or news.get('longitude') is None:
            continue

        key = (news['latitude'], news['longitude'])
        count = used_counts.get(key, 0)
        used_counts[key] = count + 1

        shifted_positions[news['id']] = (
            news['latitude'] + count * offset,
            news['longitude'] + count * offset
        )

    # если выбрана новость
    if selected_news_id:
        for news in news_list:
            if news.get('latitude') is None or news.get('longitude') is None:
                continue
            if news['id'] == selected_news_id:
                continue

            marker_lat, marker_lon = shifted_positions[news['id']]
            popup_text = f"""
                    <b>{news['title'][:100]}</b><br>
                    📍 {news['position']}<br>
                    🕐 {news['date']}<br>
                    <a href="{news['url']}" target="_blank">Читать</a>
                """

            folium.Marker(
                location=[marker_lat, marker_lon],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=news['title'][:50],
                icon=folium.Icon(color='blue', icon='info-sign', prefix='glyphicon')
            ).add_to(m)

        for news in news_list:
            if news.get('id') != selected_news_id:
                continue
            if news.get('latitude') is None or news.get('longitude') is None:
                continue

            marker_lat, marker_lon = shifted_positions[news['id']]
            popup_text = f"""
                    <b>{news['title'][:100]}</b><br>
                    📍 {news['position']}<br>
                    🕐 {news['date']}<br>
                    <a href="{news['url']}" target="_blank">Читать</a>
                """

            folium.Marker(
                location=[marker_lat, marker_lon],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=news['title'][:50],
                icon=folium.Icon(color='red', icon='info-sign', prefix='glyphicon'),
                z_index_offset=1000
            ).add_to(m)
            break

    else:
        marker_cluster = MarkerCluster().add_to(m)

        for news in news_list:
            if news.get('latitude') is None or news.get('longitude') is None:
                continue

            marker_lat, marker_lon = shifted_positions[news['id']]
            popup_text = f"""
                    <b>{news['title'][:100]}</b><br>
                    📍 {news['position']}<br>
                    🕐 {news['date']}<br>
                    <a href="{news['url']}" target="_blank">Читать</a>
                """

            folium.Marker(
                location=[marker_lat, marker_lon],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=news['title'][:50],
                icon=folium.Icon(color='blue', icon='info-sign', prefix='glyphicon')
            ).add_to(marker_cluster)

    os.makedirs("static", exist_ok=True)
    m.save(save_path)
    return True


