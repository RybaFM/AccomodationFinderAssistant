from schemas.schemas import ApartmentGeoFeatures
import geopy
from geopy.geocoders import Nominatim
from geopy import distance
import time
import logging
logger = logging.getLogger(__name__)

class ExtractorGEO:
    def __init__(self, user_agent_):
        self.geocoder = Nominatim(user_agent=user_agent_)
        self.center_coordinates = {}

    def extract_info(self, publication_address: list[str]):
        building, street, district, city, country = publication_address
        publication_coordinates = self.get_accomodation_coordinates(
                                               building,
                                               street,
                                               district,
                                               city,
                                               country
                                           )
        if not publication_coordinates: 
            return None
        distance_to_center = self.get_distance_to_center(publication_coordinates, city, country)
        return ApartmentGeoFeatures(distance_to_center)

    def get_accomodation_coordinates(self, 
                                     building, 
                                     street, 
                                     district, 
                                     city, 
                                     country, 
                                     max_retries=3):
        queries = [
            f"{building}, {street}, {district}, {city}, {country}" if building else None,
            f"{street}, {district}, {city}, {country}" if street else None
        ]

        queries = [q for q in queries if q]

        if not queries: return None

        for query in queries:
            for attempt in range(max_retries):
                try:
                    location = self.geocoder.geocode(query)
                    if location is not None: return (location.latitude, location.longitude)
                except Exception:
                    if attempt < max_retries-1:
                        sleep_time = (attempt + 1) * 2 
                        logger.warning("Nominatim API Error, retrying...")
                        time.sleep(sleep_time)
                    else:
                        logger.exception("Nominatim API Error, all attempts failed for this post")
        return None
    
    def get_city_center_coordinates(self, city, country, max_retries=3):
        if (city, country) in self.center_coordinates: return self.center_coordinates[(city, country)]
        query = f"{city}, {country}"
        for attempt in range(max_retries):
            try:
                location = self.geocoder.geocode(query)
                if location is not None: 
                    self.center_coordinates[(city, country)] = ((location.latitude, location.longitude))
                    return (location.latitude, location.longitude)
            except Exception:
                if attempt < max_retries-1:
                    sleep_time = (attempt + 1) * 2 
                    logger.warning("Nominatim API Error, retrying...")
                    time.sleep(sleep_time)
                else:
                    logger.exception("Nominatim API Error, all attempts failed for this post")
        return None
    
    def get_distance(self, coordinates1: tuple, coordinates2: tuple):
        return distance.distance(coordinates1, coordinates2).meters
    
    def get_distance_to_center(self, accomodation_coordinates: tuple, city, country):
        if not accomodation_coordinates: return None
        city_center_coordinates = self.get_city_center_coordinates(city, country)
        if not city_center_coordinates: return None
        return self.get_distance(accomodation_coordinates, city_center_coordinates)