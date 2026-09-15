import os
from dotenv import load_dotenv, find_dotenv
from data_engine.db_interaction.publication_repository import PublicationRepository
from data_engine.processing.extractor_llm import ExtractorLLM
from data_engine.processing.extractor_geo import ExtractorGEO
from data_engine.processing.infrastructure_service import InfrastructureService
from data_engine.pipelines.processor import PublicationProcessor

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