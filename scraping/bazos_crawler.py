import logging
import re
import math
from datetime import datetime
from bs4 import SoupStrainer,BeautifulSoup
from scraping.tamplate_of_crawlers import Crawler
from schemas.schemas import PublicationState,PublicationSource,ApartmentRawFeatures
logger = logging.getLogger(__name__)



class BazosCrawler(Crawler):
    def __init__(self):
        super().__init__(weeks_limit=1)
        self._exceptions = {"Dohodou", "Zadarmo"}
        self._detail_strainer_obj = SoupStrainer("div", class_="maincontent")
        self._filter_main_obj = SoupStrainer("div", class_=["maincontent", "strankovani"])
        self.add_links(
            "https://reality.bazos.sk/prenajmu/byt/",
            "https://reality.bazos.sk/prenajmu/byt/?hledat=&rubriky=reality&hlokalita=81101"
            "&humkreis=10&cenaod=&cenado=&order=&crp=&kitx=ano",
        )
    def _main_url(self):
        #main url
        return "https://reality.bazos.sk/"

    def _filter_main(self):
        #SoupStrainer for main
        return self._filter_main_obj

    def _detail_strainer(self):
        #SoupStrainer for publication
        return self._detail_strainer_obj

    def _count_pages(self, soup):
        #count all pages of publication
        stats_tag = soup.select_one("div.inzeratynadpis")
        stats_text = stats_tag.get_text().strip().split("z")
        number = int(stats_text[-1].strip().replace(" ", ""))
        return  math.ceil(number / 20)

    def _iter_publications(self,soup):
        #Getting all publication div
        return soup.select("div.inzeraty.inzeratyflex")

    def _date_of_post(self, publication):
        #Getting data of posting that publication
        date_tag = publication.select_one('span.velikost10')
        if not date_tag:
            return None

        date = re.search(r'\[(.+?)\]', date_tag.text)
        if not date:
            return None

        date_str = date.group(1).replace(" ", "").strip().replace("-",".")

        try:
            day, month, year = date_str.split(".")
            return datetime(int(year), int(month), int(day))

        except Exception as e:
            logger.warning("Failed to parse date %r: %s", date_str, e)
            return None

    def _get_publication_url(self, publication):
        #Getting url publication
        link_tag = publication.select_one("div.inzeratynadpis")
        a_tag = link_tag.select_one("a[href]") if link_tag else None
        if a_tag is None:
            return None

        return self._main_url().rstrip("/") + a_tag.get("href")

    def _next_main_page(self, soup):
        #Finding the next main_page
        pagination_div = soup.select_one('div.strankovani')
        if not pagination_div:
            return None
        #Choose correct div by text
        next_div = next((a for a in pagination_div.find_all('a') if 'alšia' in a.get_text()), None)
        if not next_div:
            return None
        return self._main_url().rstrip("/") + next_div.get("href")

    def _build_output(self,
                      publication,
                      detail_soup,
                      url_publication,
                      date):
        #Creating output for publication

        price = publication.select_one("div.inzeratycena").text.strip()
        if price in self._exceptions:
            logger.debug("Skipping publication %s: price is %r", url_publication, price)
            return None

        location = " ".join(publication.select_one('div.inzeratylok').get_text(separator=" ").strip().split())


        title = detail_soup.select_one('h1.nadpisdetail').text.strip()

        paragraphs = detail_soup.select('div.popisdetail')
        description = '\n'.join(p.text.strip() for p in paragraphs) if paragraphs else ""

        price_text = f"Cena tohto bytu je {price}.\n" if price != "V texte" else ""

        final_text = (
            f"Title: {title}\n"
            f"{description}\n"
            f"{price_text}"
            f"Lokalita je {location}."
        )

        return ApartmentRawFeatures(
            source=PublicationSource.BAZOS,
            link=url_publication,
            description=final_text,
            state=PublicationState.RAW,
            scraping_date=datetime.now(),
            posted_date=date,
        )


