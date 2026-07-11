import os
from dotenv import load_dotenv, find_dotenv
from db_interaction.publication_repository import PublicationRepository
from scraping.bazos_crawler import BazosCrawler
from pipelines.crawling import CrawlRunner

load_dotenv(find_dotenv())
db_url = os.getenv("DATABASE_URL")

repo = PublicationRepository(db_url)
crawler = BazosCrawler()
runner = CrawlRunner(repo, crawler)

has_work = runner.crawl_once()
print("Has work:", has_work)