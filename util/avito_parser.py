import psycopg2
import DBHelper
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import re
import time
import random
import json



class PageParser:
    def __init__(self, url, db_config):

        self.url = url

        self.db_config = db_config
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()


    def parse_title(self, soup):
        title_tag = soup.find('h1', {'data-marker': 'item-view/title-info'})
        if title_tag:
            title = title_tag.get_text().replace('\xa0', ' ').strip()
        else:
            title = "Нет заголовка"

        return title

    def parse_single_ad(self, url):
        try:
            self.browser.get(url)

            WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)

            soup = BeautifulSoup(self.browser.page_source, 'html.parser')


            print(title)

            price_tag = soup.find('span', {'itemprop': 'price'})
            if price_tag and price_tag.has_attr('content'):
                price = price_tag['content']
            else:
                price = "Нет цены"
            print(price)

            image_tags = soup.find_all('li', {'data-marker': 'image-preview/item'})
            image_urls = []
            for el in image_tags:
                img_tag = el.find('img')
                if img_tag and img_tag.get('src'):
                    image_urls.append(img_tag['src'])
            images_jsonb = json.dumps(image_urls, ensure_ascii=False)
            print(images_jsonb)

            about_flat = {}
            about_flat_items = soup.find_all('li', class_='params-paramsList__item-_2Y2O')
            for item in about_flat_items:
                spans = item.find_all('span')
                if len(spans) >= 1:
                    key = spans[0].get_text(strip=True).replace(':', '')
                    value = item.get_text(strip=True).replace(key, '').strip(': \xa0')
                    about_flat[key] = value
            about_flat_jsonb = json.dumps(about_flat, ensure_ascii=False)
            print(about_flat_jsonb)

            address_tag = soup.find('span', class_='style-item-address__string-wt61A')
            if address_tag:
                address = address_tag.get_text(strip=True)
            else:
                address = 'Адрес не найден'
            print(address)

            description_tag = soup.find('div', {'data-marker': 'item-view/item-description'})
            if description_tag:
                description = description_tag.get_text(separator=' ', strip=True)
            else:
                description = 'Описание не найдено'
            print(description)

            self.cursor.execute("""
                INSERT INTO info (url, title, price, photos, about_flat_jsonb, address, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (url, title, price, images_jsonb, about_flat_jsonb, address, description))
            self.conn.commit()

        except Exception as e:
            print(f"Ошибка при парсинге {url}: {str(e)}")

    def parse_all_ads_from_db(self, limit=10):
        try:
            self.cursor.execute("""
                SELECT url FROM url_to_ads 
                WHERE url NOT IN (SELECT url FROM info)
                LIMIT %s;
            """, (limit,))
            urls = self.cursor.fetchall()

            print(f"\nНачинаем обработку {len(urls)} объявлений из БД\n")

            for idx, (url,) in enumerate(urls, 1):
                print(f"\n[{idx}/{len(urls)}] Парсим: {url}")
                self.parse_single_ad(url)
                time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"Ошибка при получении ссылок из БД: {str(e)}")



class AvitoParser:
    def __init__(self, url, db_config):
        self.helper = DBHelper.DBHelper(dbname='avito', dbpassword='Artem_17082003')
        chrome_version = 135
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36')

        self.browser = uc.Chrome(options=options)
    def get_pages_from_db(self):
