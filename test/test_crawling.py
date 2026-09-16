import os
from dotenv import load_dotenv, find_dotenv
from data_engine.db_interaction.publication_repository import PublicationRepository
from data_engine.scraping.bazos_crawler import BazosCrawler
from data_engine.pipelines.crawling import CrawlRunner

load_dotenv(find_dotenv())
db_url = os.getenv("DATABASE_URL")

if not db_url:
    raise RuntimeError("DATABASE_URL not found in .env")

repo = PublicationRepository(db_url)

repo.delete_old_publication()
seen_urls = repo.select_all_links()

crawler = BazosCrawler(seen_urls=seen_urls)
runner = CrawlRunner(repo, crawler)

has_work = runner.crawl_once()
