import logging
import re
import math
import json
import requests
from datetime import datetime
from bs4 import SoupStrainer, BeautifulSoup
from scraping.tamplate_of_crawlers import Crawler
from schemas.schemas import PublicationState, PublicationSource, ApartmentRawFeatures

logger = logging.getLogger(__name__)


class NehnutelnostiCrawler(Crawler):
    def __init__(self):
        super().__init__(weeks_limit=1)
        self._filter_main_obj = SoupStrainer(
            name=lambda tag: tag not in ["script", "style", "noscript", "link", "head"]
        )

        self._detail_strainer_obj = SoupStrainer(
            name=lambda tag: tag not in ["script", "style", "noscript", "link", "head"]
        )

        self.add_links(
            "https://www.nehnutelnosti.sk/vysledky/prenajom",
            "https://www.nehnutelnosti.sk/vysledky/bratislava/prenajom?categories=2&categories=200000",
        )

    def _main_url(self):
        return "https://www.nehnutelnosti.sk/"

    def _filter_main(self):
        return self._filter_main_obj

    def _detail_strainer(self):
        return self._detail_strainer_obj

    def _count_pages(self, soup):
        page_buttons = soup.find_all("button", attrs={"aria-label": re.compile(r"^Go to page \d+")})
        if not page_buttons:
            return 1
        page_numbers = []
        for btn in page_buttons:
            aria_label = btn.get("aria-label", "")
            match = re.search(r"\d+", aria_label)
            if match:
                page_numbers.append(int(match.group()))
        print(max(page_numbers) if page_numbers else 1)
        return max(page_numbers) if page_numbers else 1

    def _iter_publications(self, soup):
        publications = soup.find_all("div", id=re.compile(r"^advertisement-"))
        return publications

    def _date_of_post(self, publication):
        return datetime.now()

    def _get_publication_url(self, publication):
        link_tag = publication.find("a", attrs={
                "href": re.compile(r"/detail/"),
                "target": "_blank"
         })

        if not link_tag:
            link_tag = publication.find("a", href=re.compile(r"/detail/"))

        if not link_tag:
            return None

        href = link_tag.get("href", "").strip()

        if href.startswith("/"):
            return self._main_url().rstrip("/") + href

        return href

    def _next_main_page(self, soup):
        next_button = soup.find("button", {"data-test-id": "showNextBtn"})
        if not next_button:
            return None
        parent_link = next_button.find_parent("a")
        if parent_link and parent_link.has_attr("href"):
            href = parent_link.get("href", "").strip()
            if href.startswith("/"):
                return self._main_url().rstrip("/") + href
            return href
        return None

    def _build_output(self, publication, detail_soup, url_publication, date):
        title_tag = detail_soup.find("h1", class_=re.compile(r"MuiTypography-h4"))
        title = title_tag.get_text().strip()

        price_tag = publication.find(string=re.compile(r"€/mes\."))
        price = price_tag.strip() if price_tag else ""

        loc_tag = publication.find(
            "p",
            {"data-test-id": "text", "class": re.compile(r"MuiTypography-noWrap")},
            string=re.compile(r"Bratislava|okres")
        )
        location = " ".join(loc_tag.get_text().split())

        desc_tag = detail_soup.find(
            "p",
            {
                "class": re.compile(r"MuiTypography-body2"),
                "data-test-id": "text"
            }
        )

        description = desc_tag.get_text().strip()


        final_description = (
            f"Title: {title}\n"
            f"{description}\n"
            f"Cena: {price}.\n"
            f"Lokalita: {location}."
        )

        return ApartmentRawFeatures(
            source=PublicationSource.NEHNUTELNOSTI,
            link=url_publication,
            description=final_description,
            state=PublicationState.RAW,
            scraping_date=datetime.now(),
            posted_date=date,
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    crawler = NehnutelnostiCrawler()
    for i in crawler.start_processing():
        print(i)