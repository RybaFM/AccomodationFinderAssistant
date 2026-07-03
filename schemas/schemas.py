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
    price: Optional[int] = Field(None, description="Apartment price (number only). If not specified, return null.")
    rooms: Optional[float] = Field(None, description="Number of rooms. If it's a studio, return 1. If not specified, return null.")
    area_sqm: Optional[float] = Field(None, description="Apartment area in square meters (number only). If not specified, return null.")
    building: Optional[str] = Field(None, description="Building where apartment is situated. If not specified, return null.")
    street: Optional[str] = Field(None, description="Street where apartment is situated. If not specified, return null.")
    district: Optional[str] = Field(None, description="District where apartment is situated. If not specified, return null.")
    city: Optional[str] = Field(None, description="City where apartment is situated. If not specified, return null.")
    country: Literal["Slovakia"] = "Slovakia"

class ApartmentGeoFeatures(BaseModel):
    distance_to_center: Optional[float]