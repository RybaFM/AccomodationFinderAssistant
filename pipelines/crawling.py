import time
import logging
from db_interaction.publication_repository import PublicationRepository

logger = logging.getLogger(__name__)

SLEEP_INTERVAL_SECONDS = 7 * 86400


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
        processed_pages = 0

        for page_items in self._crawler.start_processing():
            if not page_items:
                continue
            try:
                self._repository.insert_raw_publications(page_items)
                processed_pages += 1
                logger.debug(f"Successfully processed page #{processed_pages} with {len(page_items)} items")
            except Exception:
                logger.exception("Failed to insert page items into db")
        logger.info(f"Cycle finished. Total processed pages: {processed_pages}")