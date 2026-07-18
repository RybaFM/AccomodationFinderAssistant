from schemas.schemas import ApartmentGeoFeatures, InfrastructureFeatures
from processing.infrastructure_service import InfrastructureService
import geopy
from geopy.geocoders import Nominatim
from geopy import distance
import time
import logging
logger = logging.getLogger(__name__)

class ExtractorGEO:
    def __init__(self, infrastructure_service: InfrastructureService):
        self.geocoder = Nominatim(user_agent="AccomodationFinderAssistant/1.0 (contact: rjbikov.yaroslav@gmail.com)")
        self.infrastructure_service = infrastructure_service
        self.center_coordinates = {}

    def extract_info(self, publication_address: list[str]):
        if len(publication_address) != 6: return None
        building, street, district, city, country, building_name = publication_address
        publication_coordinates = self.get_accomodation_coordinates(
                                               building,
                                               street,
                                               district,
                                               city,
                                               country,
                                               building_name
                                           )
        if not publication_coordinates: 
            return None
        distance_to_center = self.get_distance_to_center(publication_coordinates, city, country)

        shopping_malls = self.infrastructure_service.get_shopping_malls(publication_coordinates)
        shopping_mall_name, shopping_mall_dist = self.get_nearest_spots(publication_coordinates, shopping_malls)

        supermarkets = self.infrastructure_service.get_supermarkets(publication_coordinates)
        supermarket_name, supermarket_dist = self.get_nearest_spots(publication_coordinates, supermarkets)

        transport_stops = self.infrastructure_service.get_transport_stops(publication_coordinates)
        transport_stop_name, transport_stop_dist = self.get_nearest_spots(publication_coordinates, transport_stops)

        return ApartmentGeoFeatures(distance_to_center=distance_to_center, 
                                    distance_to_shopping_mall=shopping_mall_dist, 
                                    nearest_shopping_mall_name=shopping_mall_name,
                                    distance_to_supermarket=supermarket_dist,
                                    nearest_supermarket_name=supermarket_name,
                                    distance_to_transport_stop=transport_stop_dist,
                                    nearest_transport_stop_name=transport_stop_name)

    def get_accomodation_coordinates(self, 
                                     building, 
                                     street, 
                                     district, 
                                     city, 
                                     country, 
                                     building_name,
                                     max_retries=3):
        queries = [
            ', '.join(x for x in [building, street, district, city, country] if x) if building else None,
            ', '.join(x for x in [building_name, street, district, city, country] if x) if building_name else None,
            ', '.join(x for x in [street, district, city, country] if x) if street else None
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
    
    def get_nearest_spots(self, coordinates, spots: list[InfrastructureFeatures]):
        spots_with_distance = [
            (spot.name, self.get_distance(coordinates, (spot.latitude, spot.longitude))) 
            for spot in spots
        ]
        if not spots_with_distance: return (None, None)
        return min(spots_with_distance, key=lambda item: item[1])