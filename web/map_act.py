import math
import folium
import psycopg2
import json
from collections import defaultdict
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import Optional
from pydantic import BaseModel
import uvicorn
from fastapi.templating import Jinja2Templates
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
templates = Jinja2Templates(directory="templates")

class ClusterResponse(BaseModel):
    lat: float
    lon: float
    count: int
    properties: list

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def latlng_to_world(lat, lng):
    """Преобразует координаты в мировые координаты (от 0 до 1)."""
    siny = math.sin(math.radians(lat))
    siny = min(max(siny, -0.9999), 0.9999)
    x = (lng + 180.0) / 360.0
    y = 0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)
    return x, y

def world_to_latlng(x, y):
    """Обратно преобразует мировые координаты в географические."""
    lng = x * 360.0 - 180.0
    n = math.pi - 2.0 * math.pi * y
    lat = math.degrees(math.atan(math.sinh(n)))
    return lat, lng

def get_clusters_from_db(zoom_level: int, ne_lat=None, ne_lng=None, sw_lat=None, sw_lng=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT title, description, factoids, summary, type, address, price, photos, latitude, longitude, link
            FROM info
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
        params = []
        if all([ne_lat, ne_lng, sw_lat, sw_lng]):
            query += " AND latitude BETWEEN %s AND %s AND longitude BETWEEN %s AND %s"
            params.extend([sw_lat, ne_lat, sw_lng, ne_lng])

        cursor.execute(query, params)
        rows = cursor.fetchall()


        cluster_radius_px = 32
        tiles_count = 2 ** zoom_level
        clusters_grid = {}

        for row in rows:
            lat, lon = row[-3], row[-2]
            world_x, world_y = latlng_to_world(lat, lon)

            px = world_x * tiles_count * 256
            py = world_y * tiles_count * 256

            grid_x = int(px // cluster_radius_px)
            grid_y = int(py // cluster_radius_px)
            key = (grid_x, grid_y)

            if key not in clusters_grid:
                clusters_grid[key] = []

            clusters_grid[key].append(row)

        clusters = []
        for group in clusters_grid.values():
            lats = [float(g[-3]) for g in group]
            lons = [float(g[-2]) for g in group]

            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)

            properties = []
            for row in group:
                title, description, factoids, summary, type, address, price, photos, latitude, longitude, link = row
                properties.append({
                    'lat': latitude,
                    'lon': longitude,
                    'price': price,
                    'description': description,
                    'factoids': factoids,
                    'summary': summary,
                    'type': type,
                    'address': address,
                    'photos': photos,
                    'title': title,
                    'link': link,
                })

            clusters.append({
                'lat': center_lat,
                'lon': center_lon,
                'count': len(properties),
                'properties': properties[:] if len(properties) > 1 else properties
            })

        return clusters
    finally:
        cursor.close()
        conn.close()


@app.get("/api/clusters", response_model=list[ClusterResponse])
async def get_clusters_api(
    zoom: int = Query(6, ge=1, le=25),
    ne_lat: Optional[float] = Query(None),
    ne_lng: Optional[float] = Query(None),
    sw_lat: Optional[float] = Query(None),
    sw_lng: Optional[float] = Query(None)
):
    return get_clusters_from_db(zoom, ne_lat, ne_lng, sw_lat, sw_lng)


@app.get("/interactive", response_class=HTMLResponse)
async def show_interactive_map(request: Request):
    return templates.TemplateResponse("interactive_map.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.2", port=8000)