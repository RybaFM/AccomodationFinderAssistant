import time
import logging
from db_interaction.publication_repository import PublicationRepository

logger = logging.getLogger(__name__)

SLEEP_INTERVAL_SECONDS = 7 * 86400
RETRY_INTERVAL_SECONDS = 30 * 60


class CrawlRunner:

    def __init__(self, repository, crawler):
        self._repository = repository
        self._crawler = crawler

    def crawl(self):
        while True:
            has_work = self.crawl_once()
            if not has_work:
                logger.warning(f"No pages found, possible block or failure. Retrying in {RETRY_INTERVAL_SECONDS // 60} minutes")
                time.sleep(RETRY_INTERVAL_SECONDS)
            else:
                logger.info(f"Crawl cycle finished, sleeping for {SLEEP_INTERVAL_SECONDS // 86400} days")
                time.sleep(SLEEP_INTERVAL_SECONDS)

    def crawl_once(self):
        total_saved = 0
        has_work = False

        for page_items in self._crawler.start_processing():
            if not page_items:
                continue
            has_work = True
            try:
                self._repository.insert_raw_publications(page_items)
            except Exception:
                logger.exception("Failed to insert into db")
                continue
            total_saved += 1
            logger.debug(f"Saved {len(page_items)} items in {total_saved} pages")

        logger.info(f"Total saved {total_saved} pages")
        return has_work