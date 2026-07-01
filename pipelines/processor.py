import time
from database.publication_repository import PublicationRepository
from processing.extractor_llm import ExtractorLLM
import logging
logger = logging.getLogger(__name__)

class PublicationProcessor:
    def __init__(self, publication_repository: PublicationRepository, extractor_llm: ExtractorLLM):
        self.publication_repository = publication_repository
        self.extractor_llm = extractor_llm

    def process(self, batch_size=20):
        while True:
            has_work_llm = self.process_llm(batch_size)
            has_work_geo = self.process_geo(batch_size)
            has_work = has_work_llm or has_work_geo
            if not has_work: 
                logger.info("No publications to process, sleeping for 10 minutes")
                time.sleep(600)

    def process_llm(self, batch_size=20):
        publications = self.publication_repository.select_raw_publications(batch_size)
        if not publications: return False

        processed_publications = []
        for (publication_id, description) in publications:
            processed_publications.append((publication_id, self.extractor_llm.extract_info(description)))

        successfully_processed = len(processed_publications) - sum(1 for _, info in processed_publications if info is None)
        logger.info(f"LLM processed successfully {successfully_processed}/{len(processed_publications)} publications")
        self.publication_repository.update_raw_publications(processed_publications)
        return True

    def process_geo(self, batch_size=20):
        pass