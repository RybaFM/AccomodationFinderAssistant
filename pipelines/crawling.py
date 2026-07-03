import logging
from scraping.bazos_crawler import BazosCrawler
from db_interaction.publication_repository import PublicationRepository

logger = logging.getLogger(__name__)

class CrawlRunner:

    def __init__(self, repository):
        self._repository = repository

    def crawl(self):
        crawler = BazosCrawler()
        total_saved = 0

        for page_items in crawler.start_processing():
            if not page_items:
                continue
            try:
                self._repository.insert(page_items)
            except Exception as e:
                logger.exception("Failed to insert into db")
                continue
            total_saved += 1
            logger.debug(f"Saved {len(page_items)} items in {total_saved} pages")

        logger.info(f"Total saved {len(total_saved)} pages")
        return total_saved