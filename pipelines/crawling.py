import time
import logging
from db_interaction.publication_repository import PublicationRepository

logger = logging.getLogger(__name__)

SLEEP_INTERVAL_SECONDS = 7 * 86400
BATCH_SIZE = 20


class CrawlRunner:

    def __init__(self, repository, crawler):
        self._repository = repository
        self._crawler = crawler

    def crawl(self):
        while True:
            self.crawl_once()
            logger.info(f"Crawl cycle finished, sleeping for {SLEEP_INTERVAL_SECONDS // 86400} days")
            time.sleep(SLEEP_INTERVAL_SECONDS)

    def crawl_once(self):
        total_saved = 0
        batch = []

        for publication in self._crawler.start_processing():
            batch.append(publication)

            if len(batch) >= BATCH_SIZE:
                total_saved += self._save_batch(batch)
                batch = []

        if batch:
            total_saved += self._save_batch(batch)

        logger.debug(f"Cycle finished. Total saved publications: {total_saved}")
        return total_saved

    def _save_batch(self, batch):
        try:
            self._repository.insert_raw_publications(batch)
            logger.debug(f"Successfully saved batch of {len(batch)} publications")
            return len(batch)
        except Exception:
            logger.exception("Failed to insert batch into db")
            return 0