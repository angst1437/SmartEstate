import asyncio
import json
import random
import time
import re
import psycopg2
import requests
from selectolax.parser import HTMLParser
from playwright.async_api import async_playwright
from util.interfaces import Parser
from util.DBHelper import DBHelper
from util.geocoder import Geocoder


class AvitoParser(Parser):
    def __init__(self, db_config):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        # self.db_helper = DBHelper(db_config)
        self.geocoder = Geocoder()

    async def start_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        print("Браузер запущен")

    async def close_browser(self):
        await self.browser.close()
        await self.playwright.stop()
        # self.db_helper.close()

    async def price_range(self, base_url, start_val, end_val):
        await self.page.goto(base_url)
        try:
            await self.page.fill('input[data-marker="price-from/input"]', start_val)
            await self.page.fill('input[data-marker="price-to/input"]', end_val)
            await self.page.click('button[data-marker="search-filters/submit-button"]')
            await self.page.wait_for_timeout(3000)
            print(f"Установлен диапазон: {start_val} - {end_val}")
            return True
        except Exception as e:
            print(f"Ошибка в price_range: {e}")
            return False

    async def get_ads_urls(self):
        await self.page.wait_for_selector('[data-marker="item-title"]')
        html = await self.page.content()
        tree = HTMLParser(html)
        links = [
            f"https://www.avito.ru{a.attributes['href']}"
            for a in tree.css('a[data-marker="item-title"]')
            if a.attributes.get('href')
        ]
        return links

    async def parse_page(self, url):
        try:
            await self.page.goto(url)
            await self.page.wait_for_selector('h1[data-marker="item-view/title-info"]', timeout=15000)
            html = await self.page.content()
            tree = HTMLParser(html)

            title = tree.css_first('h1[data-marker="item-view/title-info"]')
            title = title.text(strip=True) if title else "Нет заголовка"

            price_tag = tree.css_first('span[itemprop="price"]')
            price = price_tag.attributes.get('content') if price_tag else "Нет цены"

            image_urls = [
                img.attributes.get('src')
                for img in tree.css('li[data-marker="image-preview/item"] img')
                if img.attributes.get('src')
            ]
            images_jsonb = json.dumps(image_urls, ensure_ascii=False)

            about_flat = {}
            for item in tree.css('li.params-paramsList__item-_2Y2O'):
                spans = item.css('span')
                if spans:
                    key = spans[0].text(strip=True).replace(':', '')
                    value = item.text(strip=True).replace(key, '').strip(': \xa0')
                    about_flat[key] = value
            about_flat_jsonb = json.dumps(about_flat, ensure_ascii=False)

            address_tag = tree.css_first('span.style-item-address__string-wt61A')
            address = address_tag.text(strip=True) if address_tag else 'Адрес не найден'

            description_tag = tree.css_first('div[data-marker="item-view/item-description"]')
            description = description_tag.text(separator=' ', strip=True) if description_tag else 'Описание не найдено'


            latitude, longitude = self.geocoder.get_cords_from_address(address)

            data = {
                'url': url,
                'title': title,
                'price': price,
                'images': images_jsonb,
                'about_flat': about_flat_jsonb,
                'address': address,
                'description': description,
                'latitude': latitude,
                'longitude': longitude
            }

            # self.db_helper.add_data(data)
            print(f"Сохранено: {data}")
        except Exception as e:
            print(f"Ошибка при парсинге {url}: {e}")


    async def process_price_range(self, base_url, start_val, end_val):
        if not await self.price_range(base_url, start_val, end_val):
            return
        urls = await self.get_ads_urls()
        for url in urls:
            await self.parse_page(url)
            await asyncio.sleep(random.uniform(2, 4))

    async def run_all(self, base_url, prices):
        await self.start_browser()
        try:
            for i in prices:
                start_val, end_val = prices[i], prices[i+1]
                print(f"\n=== Обработка диапазона {start_val}-{end_val} ===")
                await self.process_price_range(base_url, start_val, end_val)
        finally:
            await self.close_browser()


# Запуск
if __name__ == "__main__":
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'user',
        'password': 'password',
        'db_name': 'avito'
    }

    BASE_URL = 'https://www.avito.ru/all/kvartiry/prodam-ASgBAgICAUSSA8YQ?...'
    PRICE_LIST = ['1000000', '1500000', '1500001', '2000000']

    parser = AvitoParser(DB_CONFIG)
    asyncio.run(parser.run_all(BASE_URL, PRICE_LIST))
