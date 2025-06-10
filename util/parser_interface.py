from abc import ABC, abstractmethod
from selenium import webdriver
from fake_useragent import UserAgent
try:
    import undetected_chromedriver as uc
except ModuleNotFoundError:
    print("Undetected chromedriver not working")

class ParserInterface(ABC):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36')
        self.browser = webdriver.Chrome(options=options)

    @abstractmethod
    def parse_urls(self):
        pass



class UrlCollectorInterface(ABC):
    def __init__(self, use_undetected=True):
        if use_undetected:
            options = uc.ChromeOptions()

            # Настройки для обхода защиты
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--headless=new")  # Headless-режим
            options.add_argument("--disable-images")  # Без картинок
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-logging")

            options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36')

            self.browser = uc.Chrome(
                options=options,
                use_subprocess=True,
            )

        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36')
        self.browser = webdriver.Chrome(options=options)


    @abstractmethod
    def paginate(self):
        pass

    @abstractmethod
    def get_urls(self):
        pass

