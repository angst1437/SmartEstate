import folium
import psycopg2
import json
from collections import defaultdict
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import Optional
from pydantic import BaseModel
import numpy as np
from sklearn.cluster import DBSCAN
import uvicorn
app = FastAPI()

DB_CONFIG = {
    'dbname': 'cian',
    'user': 'postgres',
    'password': '1437',
    'host': 'localhost',
    'port': '5432'
}

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ClusterResponse(BaseModel):
    lat: float
    lon: float
    count: int
    properties: list

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def generate_map(zoom_level: int, ne_lat: Optional[float] = None, ne_lng: Optional[float] = None,
                 sw_lat: Optional[float] = None, sw_lng: Optional[float] = None):
    russia_map = folium.Map(
        location=[64.6863136, 97.7453061],
        zoom_start=zoom_level
    )

    clusters = get_clusters_from_db(zoom_level, ne_lat, ne_lng, sw_lat, sw_lng)

    for cluster in clusters:
        popup_content = format_popup_content(cluster)
        folium.CircleMarker(
            location=[cluster['lat'], cluster['lon']],
            radius=6 + min(cluster['count'], 20),
            color='red',
            fill=True,
            fill_opacity=0.6,
            popup=folium.Popup(popup_content, max_width=300)
        ).add_to(russia_map)

    map_path = f"static/map_zoom_{zoom_level}.html"
    russia_map.save(map_path)

    # Добавляем вывод зума в консоль браузера
    with open(map_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Встраиваем JavaScript перед закрывающим тегом </body>
    script = f"""
    <script>
        console.log("Текущий уровень зума: {zoom_level}");
    </script>
    """
    html_content = html_content.replace('</body>', f'{script}</body>')

    with open(map_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return map_path

def get_clusters_from_db(zoom_level: int, ne_lat=None, ne_lng=None, sw_lat=None, sw_lng=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT link, address, price, photos, latitude, longitude
            FROM info
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
        params = []
        if all([ne_lat, ne_lng, sw_lat, sw_lng]):
            query += " AND latitude BETWEEN %s AND %s AND longitude BETWEEN %s AND %s"
            params.extend([sw_lat, ne_lat, sw_lng, ne_lng])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        points = np.array([[row[-2], row[-1]] for row in rows])

        zoom_eps_map = {
            1: 5,
            2: 4,
            3: 3,
            4: 2,
            5: 1,
            6: 0.4,
            7: 0.2,
            8: 0.1,
            9: 0.04,
            10: 0.1,
            11: 0.01,
            12: 0.008,
            13: 0.006,
            14: 0.004,
            15: 0.002,
            16: 0.0005,
            17: 0.0001,
            18: 0.00005
        }

        eps = zoom_eps_map.get(zoom_level, 0.01)

        db = DBSCAN(eps=eps, min_samples=2).fit(points)
        labels = db.labels_

        clusters_dict = defaultdict(list)
        for label, row in zip(labels, rows):
            if label == -1:
                clusters_dict[f"noise_{row[0]}_{row[1]}"].append(row)
            else:
                clusters_dict[label].append(row)

        clusters = []
        for label, group in clusters_dict.items():
            lats = [float(g[-2]) for g in group if g[-2] is not None]
            lons = [float(g[-1]) for g in group if g[-1] is not None]

            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)

            properties = []
            for row in group:
                link, address, price, photos, latitude, longitude = row
                properties.append({
                    'lat': latitude,
                    'lon': longitude,
                    'price': price,
                    'address': address,
                    'photos': photos
                })

            clusters.append({
                'lat': center_lat,
                'lon': center_lon,
                'count': len(properties),
                'properties': properties[:5] if len(properties) > 1 else properties
            })

        return clusters

    finally:
        cursor.close()
        conn.close()

def format_popup_content(cluster):
    if cluster['count'] == 1 and cluster['properties']:
        prop = cluster['properties'][0]
        return create_popup_content(
            prop['price'],
            prop['address'],
            prop['photos']
        )
    else:
        popup_lines = [f"<b>{cluster['count']} объектов:</b><br>"]
        for prop in cluster['properties']:
            popup_lines.append(f"• хз — {prop['price']} ₽<br>")
        return "".join(popup_lines)

def create_popup_content(price, address, photos):
    lines = [
        f"<b>Цена:</b> {price} ₽" if price else "Цена: не указана",
        f"<b>Адрес:</b> {address or 'не указан'}",
        f"<b>Описание:</b> 'нет описания'"
    ]


    if photos:
        photos_list = json.loads(photos) if isinstance(photos, str) else photos
        if isinstance(photos_list, list) and photos_list:
            lines.append("<div style='margin-top: 10px;'><b>Фотографии:</b>")
            lines.append("<div style='display: flex; flex-wrap: wrap; gap: 5px; margin-top: 5px;'>")
            for photo in photos_list[:3]:
                lines.append(f"<img src='{photo}' style='width: 90px; height: 90px; object-fit: cover; border: 1px solid #ddd;'>")
            lines.append("</div></div>")

    return "<br>".join(lines)

@app.get("/api/clusters", response_model=list[ClusterResponse])
async def get_clusters_api(
    zoom: int = Query(6, ge=1, le=25),
    ne_lat: Optional[float] = Query(None),
    ne_lng: Optional[float] = Query(None),
    sw_lat: Optional[float] = Query(None),
    sw_lng: Optional[float] = Query(None)
):
    return get_clusters_from_db(zoom, ne_lat, ne_lng, sw_lat, sw_lng)

@app.get("/map", response_class=HTMLResponse)
async def show_map(
    zoom: int = Query(6, ge=1, le=25),
    ne_lat: Optional[float] = Query(None),
    ne_lng: Optional[float] = Query(None),
    sw_lat: Optional[float] = Query(None),
    sw_lng: Optional[float] = Query(None)
):
    map_path = generate_map(zoom, ne_lat, ne_lng, sw_lat, sw_lng)
    with open(map_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/interactive", response_class=HTMLResponse)
async def show_interactive_map():
    with open("static/interactive_map.html", 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
