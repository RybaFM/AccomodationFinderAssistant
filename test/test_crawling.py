import os
from dotenv import load_dotenv, find_dotenv
from db_interaction.publication_repository import PublicationRepository
from scraping.bazos_crawler import BazosCrawler
from pipelines.crawling import CrawlRunner

load_dotenv(find_dotenv())
db_url = os.getenv("DATABASE_URL")

if not db_url:
    raise RuntimeError("DATABASE_URL not found in .env")

repo = PublicationRepository(db_url)

seen_urls = repo.select_all_links()

crawler = BazosCrawler(seen_urls=seen_urls)
runner = CrawlRunner(repo, crawler)

has_work = runner.crawl_once()
