from google import genai
from google.genai import errors
from google.genai.errors import ServerError, ClientError
import time
from schemas.schemas import ApartmentLLMFeatures, DEFAULT_SLEEP_TIME
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

    def get_retry_delay(self, e: errors.ClientError) -> float | None:
        # e.details is the parsed JSON: {'error': {..., 'details': [...]}}
        body = e.details
        if isinstance(body, dict):
            body = body.get("error", body)
            for item in body.get("details", []):
                if item.get("@type", "").endswith("RetryInfo"):
                    delay = item.get("retryDelay")  # e.g. "33987s"
                    if delay:
                        return float(delay.rstrip("s"))
        return DEFAULT_SLEEP_TIME

    def default_exception(self, attempt, max_retries):
        if attempt < max_retries:    
            sleep_time = (attempt + 1) * 2 if attempt < max_retries - 1 else 60 
            logger.warning("AI API Error, retrying...")        
            time.sleep(sleep_time)
        else:
            logger.exception("AI API Error, all attempts failed for this post")

    def extract_info(self, posted_text, max_retries=3):
        if not posted_text: return None
        system_instruction = """
        You are a specialized data extraction tool for real estate listings.
        Analyze the provided apartment post and extract the key parameters.
        Do not hallucinate or invent data.
        """
        attempt = 0
        #for attempt in range(max_retries):
        while attempt < max_retries:
            try:
                response = self.generate_content_limiter(system_instruction, posted_text)
                logger.debug(f"--- AI RESPONSE ({self.model_id}) ---")
                logger.debug(response.text)
                return ApartmentLLMFeatures.model_validate_json(response.text.strip())
            except ServerError:
                sleep_time = 300
                logger.warning("AI API Server error. Waiting 5 minutes before retrying...")
                time.sleep(sleep_time)
                continue
            except ClientError as e:
                if e.code == 429:
                    sleep_time = self.get_retry_delay(e)
                    logger.warning(f"AI API Quota exceeded. Waiting {sleep_time} seconds before retrying...")
                    time.sleep(sleep_time)
                    continue
                else:
                    attempt+=1
                    self.default_exception(attempt, max_retries)
            except Exception:
                attempt+=1
                self.default_exception(attempt, max_retries)
        return None