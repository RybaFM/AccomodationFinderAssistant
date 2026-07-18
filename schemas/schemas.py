from enum import Enum
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

# ENUMS
class PublicationState(str, Enum):
    RAW = "raw"
    LLM_PROCESSED = "llm_processed"
    FULLY_PROCESSED = "fully_processed"
    ERROR = "error"

class PublicationSource(str, Enum):
    BAZOS = "bazos"
    NEHNUTELNOSTI = "nehnutelnosti"

# MODELS
class ApartmentRawFeatures(BaseModel):
    source: PublicationSource
    link: str
    description: str
    state: PublicationState = PublicationState.RAW
    scraping_date: datetime
    posted_date: datetime

class ApartmentLLMFeatures(BaseModel):
    price: Optional[int] = Field(None, description="Total apartment price per month (number only). If price and utilities are listed separately (e.g., 600 + 150), return the SUM (750). If not specified, return null.")
    rooms: Optional[float] = Field(None, description="Number of rooms (e.g., 1, 2, 3.5). If it's a studio (garzonka), return 1. If not specified, return null.")
    area_sqm: Optional[float] = Field(None, description="Apartment area in square meters (number only). If not specified, return null.")
    building_name: Optional[str] = Field(None, description="Specific residential complex or project name (e.g., SKYPARK, NUPPU, Klingerka, Eurovea). Do NOT put house numbers or generic words like 'novostavba' here.")
    building_type: Optional[Literal["novostavba", "rekonštrukcia", "pôvodný stav"]] = Field(None, description="Condition/type of the building if mentioned (e.g., new building, renovated, original condition).")
    building: Optional[str] = Field(None, description="The orientation or descriptive number of the building/house (e.g., '12', '4A', '1'). Extract this if it is attached to the street or building. If not specified, return null.")
    street: Optional[str] = Field(None, description="Street where apartment is situated (e.g., Bajkalská). Do not include house numbers if they mess up the street name. If not specified, return null.")
    district: Optional[str] = Field(None, description="Borough/District name (e.g., Ružinov, Petržalka, Staré Mesto). DO NOT return postal codes (like 85104) or city names here. If only postal code is found, leave as null.")
    city: Optional[str] = Field(None, description="City where apartment is situated. If not specified, return null.")
    country: Literal["Slovakia", "Austria", "Hungary"] = Field(None, description="Country where the apartment is located. Set to Austria if the city is Wolfsthal/Kittsee, or Hungary if Rajka.")

class ApartmentGeoFeatures(BaseModel):
    distance_to_center: Optional[float]
    distance_to_shopping_mall: Optional[float]
    nearest_shopping_mall_name: Optional[str]
    distance_to_supermarket: Optional[float]
    nearest_supermarket_name: Optional[str]
    distance_to_transport_stop: Optional[float]
    nearest_transport_stop_name: Optional[str]

class InfrastructureFeatures(BaseModel):
    name: Optional[str]
    latitude: float
    longitude: float