from google import genai
import json
import psycopg

class FeaturesExtractor:
    def __init__(self, apiKey, db_url):
        self.client = genai.Client(api_key=apiKey)
        self.db_url = db_url

    def extract_info(self, posted_text):
        if not posted_text:
            return

        model_id = "gemini-3.1-flash-lite"
        system_instruction = """
        You are a specialized data extraction tool for real estate listings.
        Analyze the provided apartment post and extract the key parameters.

        You MUST respond STRICTLY in JSON format matching the following structure:
        {
            "price": int or null,          // Apartment price (number only). If not specified, return null.
            "rooms": float or null,          // Number of rooms. If it's a studio, return 1. If not specified, return null.
            "area_sqm": float or null,     // Apartment area in square meters (number only). If not specified, return null.
            "address": string or null,     // Apartment address. If not specified, return null.
            "city": string or null,        // City where apartment is situated. If not specified, return null.
        }

        Rules:
        1. Do not hallucinate or invent data. If a parameter is missing from the text, set it to null.
        2. Output ONLY raw, clean JSON. Do not include any conversational filler, markdown formatting, or text outside the JSON object.
        """
        try:
            response = self.client.models.generate_content(
                model=model_id,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json"
                },
                contents=posted_text
            )
            print(f"--- AI SENTIMENT ({model_id}) ---")
            print(response.text)
            data = json.loads(response.text.strip())
            return data
        except Exception as e:
            print(f"AI API Error: {e}")
            return None

    def process(self):
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, raw_text FROM raw_listings WHERE state = 'raw' LIMIT 50;")
                apartment_postings = cursor.fetchall()
                for posting in apartment_postings:
                    extracted_features = self.extract_info(posting[1])
                    if extracted_features is None: continue
                    try:
                        with conn.transaction():
                            cursor.execute("""UPDATE raw_listings
                                            SET state = 'processed', price = %s, rooms = %s, area_sqm = %s, address = %s, city = %s
                                            WHERE id = %s""",
                                           (
                                                extracted_features['price'] if 'price' in extracted_features else None,
                                                extracted_features['rooms'] if 'rooms' in extracted_features else None,
                                                extracted_features['area_sqm'] if 'area_sqm' in extracted_features else None,
                                                extracted_features['address'] if 'address' in extracted_features else None,
                                                extracted_features['city'] if 'city' in extracted_features else None,
                                                posting[0]
                                            ))
                    except Exception as e:
                        print(f"DB UPDATE Error: {e}")
                conn.commit()