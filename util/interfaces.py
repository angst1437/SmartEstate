from abc import ABC, abstractmethod
from geopy.geocoders import Nominatim
from util.DBHelper import DBHelper


class GeocoderInterface(ABC):
    @abstractmethod
    def __init__(self):
        self.geolocator = Nominatim(user_agent="SmartEstateApp")

    @abstractmethod
    def get_cords_from_address(self, address: str):
        pass

class Parser(ABC):
    @abstractmethod
    def __init__(self, db_config: dict):
        self.helper = DBHelper(**db_config)

    @abstractmethod
    def parse_page(self, url: str):
        pass

