from schemas.schemas import InfrastructureFeatures
import json
from geopy import distance
import os
import logging
logger = logging.getLogger(__name__)

class InfrastructureService:
    def __init__(self, geojson_path="bratislava_infra.geojson"):
        self.malls = []
        self.supermarkets = []
        self.transport = []
        self._load_local_geojson(geojson_path)

    def _load_local_geojson(self, path):
        logger.debug(f"Loading offline infrastructure dataset from {path}...")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for feature in data.get('features', []):
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
            
            if geometry.get('type') == 'Point':
                lon, lat = geometry['coordinates']
            else:
                continue
                
            name = properties.get('name') or properties.get('alt_name') or 'Unknown'
            infra_item = InfrastructureFeatures(name=name, latitude=lat, longitude=lon)
            
            shop_type = properties.get('shop')
            if shop_type == 'mall':
                self.malls.append(infra_item)
            elif shop_type in ['supermarket', 'convenience']:
                self.supermarkets.append(infra_item)
            elif 'highway' in properties or 'railway' in properties:
                self.transport.append(infra_item)
                
        logger.debug(
            f"Offline cache ready: {len(self.malls)} malls, "
            f"{len(self.supermarkets)} shops, {len(self.transport)} stops."
        )

    def get_shopping_malls(self, publication_coordinates: tuple, radius=2000):
        return [
            m for m in self.malls 
            if distance.distance(publication_coordinates, (m.latitude, m.longitude)).meters <= radius
        ]

    def get_supermarkets(self, publication_coordinates: tuple, radius=1000):
        return [
            s for s in self.supermarkets 
            if distance.distance(publication_coordinates, (s.latitude, s.longitude)).meters <= radius
        ]

    def get_transport_stops(self, publication_coordinates: tuple, radius=1000):
        return [
            t for t in self.transport 
            if distance.distance(publication_coordinates, (t.latitude, t.longitude)).meters <= radius
        ]