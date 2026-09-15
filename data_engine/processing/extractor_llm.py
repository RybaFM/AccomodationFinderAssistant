from google import genai
import time
from schemas.schemas import ApartmentLLMFeatures
from ratelimit import limits, sleep_and_retry
import logging
logger = logging.getLogger(__name__)

class ExtractorLLM:
    def __init__(self, apiKey, model_id="gemini-3.1-flash-lite", calls=15, period=60):
        self.client = genai.Client(api_key=apiKey)
        self.model_id = model_id
        self.generate_content_limiter = sleep_and_retry(
            limits(calls=calls, period=period)(self.raw_llm_call)
        )

    def raw_llm_call(self, system_instruction, posted_text):
        return self.client.models.generate_content(
            model=self.model_id,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": ApartmentLLMFeatures,
            },
            contents=posted_text
        )

    def extract_info(self, posted_text, max_retries=3):
        if not posted_text: return None
        system_instruction = """
        You are a specialized data extraction tool for real estate listings.
        Analyze the provided apartment post and extract the key parameters.
        If listing is not an offer, but a demand, like "I am searching for a flat for ME, budget is 500 euro" return raw model with all Nones.
        Do not hallucinate or invent data. If a parameter is missing from the text, set it to null.
        """
        for attempt in range(max_retries):
            try:
                response = self.generate_content_limiter(system_instruction, posted_text)
                logger.debug(f"--- AI RESPONSE ({self.model_id}) ---")
                logger.debug(response.text)
                return ApartmentLLMFeatures.model_validate_json(response.text.strip())
            except Exception:
                if attempt < max_retries-1:
                    sleep_time = (attempt + 1) * 2 
                    logger.warning("AI API Error, retrying...")
                    time.sleep(sleep_time)
                else:
                    logger.exception("AI API Error, all attempts failed for this post")
        return None