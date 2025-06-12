from geopy import Nominatim

from util.interfaces import GeocoderInterface


class Geocoder(GeocoderInterface):
    def __init__(self):
        super().__init__()

    def get_cords_from_address(self, address: str) -> list:
        location = self.geolocator.geocode(address)
        if location:
            return [location.latitude, location.longitude]
        else:
            return [None, None]
