from google import genai
import json
from pydantic import BaseModel, Field
from typing import Optional
import time

class ApartmentFeatures(BaseModel):
    price: Optional[int] = Field(None, description="Apartment price (number only). If not specified, return null.")
    rooms: Optional[float] = Field(None, description="Number of rooms. If it's a studio, return 1. If not specified, return null.")
    area_sqm: Optional[float] = Field(None, description="Apartment area in square meters (number only). If not specified, return null.")
    address: Optional[str] = Field(None, description="Apartment address. If not specified, return null.")
    city: Optional[str] = Field(None, description="City where apartment is situated. If not specified, return null.")

class ExtractorLLM:
    def __init__(self, apiKey, model_id="gemini-3.1-flash-lite"):
        self.client = genai.Client(api_key=apiKey)
        self.model_id = model_id

    def extract_info(self, posted_text, max_retries=3):
        if not posted_text: return None
        system_instruction = """
        You are a specialized data extraction tool for real estate listings.
        Analyze the provided apartment post and extract the key parameters.
        Do not hallucinate or invent data. If a parameter is missing from the text, set it to null.
        """
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    config={
                        "system_instruction": system_instruction,
                        "response_mime_type": "application/json",
                        "response_schema": ApartmentFeatures,
                    },
                    contents=posted_text
                )
                print(f"--- AI SENTIMENT ({self.model_id}) ---")
                print(response.text)
                return json.loads(response.text.strip())
            except Exception as e:
                print(f"AI API Error: {e}")
                if attempt < max_retries-1:
                    sleep_time = (attempt + 1) * 2 
                    print("Retrying...")
                    time.sleep(sleep_time)
                else:
                    print("All attempts failed for this post.")
        return None