from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import sqlite3
import html
import psycopg2

class EstatePageParser:
    def __init__(self, link, driver):
        self.driver = driver
        self.driver.get(link)

    def parse_address(self):
        addresses = self.driver.find_elements(By.XPATH, '//a[@data-name="AddressItem"]')
        if not addresses:
            return None
        else:
            address = " ".join([html.unescape(address.text) for address in addresses])

            return address.strip()

    def parse_price(self):
        try:
            price = self.driver.find_element(By.XPATH, '//div[@data-testid="price-amount"]/span').text
            clean_price = ''.join([elem for elem in html.unescape(price) if elem.isnumeric()])
        except NoSuchElementException:
            return None


        return clean_price

    def parse_photos(self):
        imgs = self.driver.find_elements(By.XPATH, '//div[@data-name="OfferGallery"]//img')
        if not imgs:
            return None
        else:
            img_links = [img.get_attribute('src') for img in imgs]

            return img_links[:-1]


    def parse_description(self):
        try:
            desc = self.driver.find_element(By.XPATH, '//div[@data-name="Description"]//span').text
            clean_desc = html.unescape(desc)
        except NoSuchElementException:
            return None

        return clean_desc

    def parse_factoids(self):
        factoid_divs = self.driver.find_elements(By.XPATH, '//div[@data-name="ObjectFactoidsItem"]//div[contains(@class, "text")]')
        if not factoid_divs:
            return None
        else:
            factoids = []
            for div in factoid_divs:
                div_spans = div.find_elements(By.TAG_NAME, 'span')
                factoid = ' '.join([html.unescape(div_span.text) for div_span in div_spans])
                factoids.append(factoid)

            return factoids


    def parse_summary(self):
        offer_summaries = self.driver.find_elements(By.XPATH, '//div[@data-name="OfferSummaryInfoItem"]')
        if not offer_summaries:
            return None
        else:
            summaries = []
            for summary in offer_summaries:
                summary_p = summary.find_elements(By.TAG_NAME, 'p')
                summary = ' '.join([html.unescape(summary.text) for summary in summary_p])
                summaries.append(summary.strip())
            return summaries

    def parse_page(self):
        return {
            "link": self.driver.current_url,
            "address": self.parse_address(),
            "price": self.parse_price(),
            "photos": self.parse_photos(),
            "description": self.parse_description(),
            "factoids": self.parse_factoids(),
            "summary": self.parse_summary()
        }

class UrlCollector:
    def __init__(self):
        pass

class CianParser:
    def __init__(self):
        self.driver = webdriver.Chrome()

    def parse_page(self):
        pass



if __name__ == '__main__':
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    parser = EstatePageParser("https://ekb.cian.ru/sale/flat/316983516/", driver)
    print(parser.parse_page())
    driver.quit()