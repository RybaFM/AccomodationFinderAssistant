from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class PublicationState(str, Enum):
    RAW = "raw"
    LLM_PROCESSED = "llm_processed"
    FULLY_PROCESSED = "fully_processed"
    ERROR = "error"

class ApartmentFeatures(BaseModel):
    price: Optional[int] = Field(None, description="Apartment price (number only). If not specified, return null.")
    rooms: Optional[float] = Field(None, description="Number of rooms. If it's a studio, return 1. If not specified, return null.")
    area_sqm: Optional[float] = Field(None, description="Apartment area in square meters (number only). If not specified, return null.")
    address: Optional[str] = Field(None, description="Apartment address. If not specified, return null.")
    city: Optional[str] = Field(None, description="City where apartment is situated. If not specified, return null.")