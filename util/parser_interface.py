from abc import ABC, abstractmethod
from selenium import webdriver
import undetected_chromedriver as uc
import DBHelper

class ParserInterface(ABC):
    def __init__(self, helper, use_undetected=False):
        if use_undetected:
            options = uc.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36')

            self.browser = uc.Chrome(options=options)
        else:
            options = webdriver.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36')
            self.browser = webdriver.Chrome(options=options)

        self.dbhelper = helper
    @abstractmethod
    def parse_urls(self):
        pass



class UrlCollectorInterface(ABC):
    def __init__(self, helper, use_undetected=False, ):
        if use_undetected:
            options = uc.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36')

            self.browser = uc.Chrome(options=options)
        else:
            options = webdriver.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36')
            self.browser = webdriver.Chrome(options=options)

        self.dbhelper = helper

    @abstractmethod
    def paginate(self):
        pass

    @abstractmethod
    def get_urls(self):
        pass

