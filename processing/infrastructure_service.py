from schemas.schemas import InfrastructureFeatures
import requests
import time
import logging
logger = logging.getLogger(__name__)

class InfrastructureService:
    def __init__(self, url="https://overpass-api.de/api/interpreter"):
        self.api_url = url
        self.headers = {
            "User-Agent": "AccomodationFinderAssistant/1.0 (contact: rjbikov.yaroslav@gmail.com)",
            "Accept": "*/*"
        }

    def fetch_query(self, query, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url, 
                    data={'data': query}, 
                    headers=self.headers,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                if attempt < max_retries - 1:
                    sleep_time = (attempt + 1) * 2 
                    logger.warning("HTTP Error, retrying...")
                    time.sleep(sleep_time)
                else:
                    logger.exception("HTTP Error, all attempts failed for this post")
        return None
    
    def extract_info(self, elements: list[dict]):
        coordinates = []
        for element in elements:
            lat, lon = (element.get('lat'), element.get('lon')) if (
                element.get('type') == 'node') else (
                    (element.get('center', {}).get('lat'), element.get('center', {}).get('lon')))
            if lat is None or lon is None: continue
            tags = element.get('tags') or {}
            name = tags.get('name') or tags.get('alt_name') or 'Unknown'
            coordinates.append(InfrastructureFeatures(name=name, latitude=lat, longitude=lon))
        return coordinates

    def get_shopping_malls(self, publication_coordinates: tuple, radius=2000):
        latitude, longitude = publication_coordinates
        query = f"""
        [out:json][timeout:25];
        (
            node["shop"="mall"](around:{radius}, {latitude}, {longitude});
            way["shop"="mall"](around:{radius}, {latitude}, {longitude});
        );
        out center;
        """
        data = self.fetch_query(query)
        if not data: return []
        elements = data.get('elements', [])
        if not elements: return []

        return self.extract_info(elements)

    def get_supermarkets(self, publication_coordinates: tuple, radius=1000):
        latitude, longitude = publication_coordinates
        query = f"""
        [out:json][timeout:25];
        (
            node["shop"="supermarket"](around:{radius}, {latitude}, {longitude});
            way["shop"="supermarket"](around:{radius}, {latitude}, {longitude});
            node["shop"="convenience"](around:{radius}, {latitude}, {longitude});
            way["shop"="convenience"](around:{radius}, {latitude}, {longitude});
        );
        out center;
        """
        data = self.fetch_query(query)
        if not data: return []
        elements = data.get('elements', [])
        if not elements: return []

        return self.extract_info(elements)

    def get_transport_stops(self, publication_coordinates: tuple, radius=1000):
        latitude, longitude = publication_coordinates
        query = f"""
        [out:json][timeout:25];
        (
            node["highway"="bus_stop"](around:{radius}, {latitude}, {longitude});
            node["railway"="tram_stop"](around:{radius}, {latitude}, {longitude});
        );
        out center;
        """
        data = self.fetch_query(query)
        if not data: return []
        elements = data.get('elements', [])
        if not elements: return []

        return self.extract_info(elements)