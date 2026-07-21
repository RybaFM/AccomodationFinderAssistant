import os
from dotenv import load_dotenv, find_dotenv
from db_interaction.publication_repository import PublicationRepository
from processing.extractor_llm import ExtractorLLM
from processing.extractor_geo import ExtractorGEO
from processing.infrastructure_service import InfrastructureService
from pipelines.processor import PublicationProcessor

load_dotenv(find_dotenv())
db_url = os.getenv("DATABASE_URL")
api_key = os.getenv("GEMINI_API_KEY")
liq_api_key = os.getenv("LIQ_API_KEY")

repository = PublicationRepository(db_url)
extractor_llm = ExtractorLLM(api_key)
infrastructure_service = InfrastructureService()
extractor_geo = ExtractorGEO(infrastructure_service, liq_api_key)
pipeline = PublicationProcessor(repository, extractor_llm, extractor_geo)

pipeline.process()