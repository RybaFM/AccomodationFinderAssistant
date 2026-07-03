from datetime import datetime, timedelta
import time
import random
import requests
from bs4 import BeautifulSoup,SoupStrainer
from abc import ABC, abstractmethod
import logging

# In the main function of application create basicConfig() of logger before launch crawlers
logger = logging.getLogger(__name__)

class Crawler(ABC):
    def __init__(self, weeks_limit = 4):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.google.com/",
        }
        self.date_limit = datetime.now() - timedelta(weeks=weeks_limit)
        self._stop = False
        self._links = []

    def links(self):
        return self._links

    def start_processing(self):
        #Start crawing
        self._stop = False
        for main_link, sorted_link in self._links:
            yield from self._crawl(main_link, sorted_link)

    def add_links(self, main_link, sorted_link):
        #Can add more starer links
        self._links.append([main_link,sorted_link])

    def _crawl(self, main_link, sorted_link):
        try:
            session = requests.Session()
            session.headers.update(self.headers)
            #Simulating real action of user
            session.get(self._main_url())
            time.sleep(random.randint(1, 3))
            session.get(main_link)
            time.sleep(random.randint(1, 3))

            first_response = session.get(sorted_link)
            time.sleep(random.uniform(1, 2))

            #Count number of pages
            soup = BeautifulSoup(first_response.text, "lxml", parse_only=self._filter_main())
            total_pages =  self._count_pages(soup)

        except requests.exceptions.RequestException as e:
            logger.exception("Failed to connect to link %s: %s",main_link,e)
            return

        except Exception as e:
            logger.exception("Can not count number of pages:  %s: %s", main_link, e)
            return

        logger.info("Crawling %s with %d pages",sorted_link,total_pages)
        yield from self._process_main(session, sorted_link, first_response, total_pages)
    def _process_main(self, session,
                      start_url,
                      first_response,
                      total_pages):

        curr_page = start_url
        response = first_response
        previous_page = None
        #Processing all pages
        for pag_index in range(total_pages):
            logger.debug("Processing page %d",pag_index)
            if pag_index > 0:
                if previous_page:
                    session.headers.update({"Referer": previous_page})
                try:
                    response = session.get(curr_page, timeout=10)
                    response.raise_for_status()
                except Exception as e:
                    logger.exception("Can not connect to site %s: %s",curr_page,e)
                    continue
                time.sleep(random.uniform(1, 2))

            soup = BeautifulSoup(response.text, "lxml", parse_only=self._filter_main())

            yield self._process_page(session, soup, curr_page)

            if self._stop:
                break
            previous_page = curr_page
            next_page_url = self._next_main_page(soup)
            if not next_page_url:
                break
            curr_page = next_page_url

    def _process_page(self,session,
                      soup,
                      page_url):
        data = []
        publications_tags = self._iter_publications(soup)

        #Go into tag fo publication to get all date
        for publication_tag in publications_tags:
            if self._stop:
                break
            publication = self._process_publication(session, publication_tag, page_url)
            if publication:
                data.append(publication)
        logger.info("Page %s: collected %d publications",page_url,len(data))

        return data

    def _process_publication(self, session,
                             publication,
                             page_url):
        #posted time of publication
        date = self._date_of_post(publication)
        if date is None:
            return None
        #check for time limit
        if date < self.date_limit:
            self._stop = True
            logger.info("Reached date limit (%s), stopping crawl", self.date_limit.date())
            return None

        url_publication = self._get_publication_url(publication)

        if not url_publication:
            logger.warning("Skipping publication %s", page_url)
            return None

        session.headers.update({"Referer": page_url})

        #Detail SoupStrainer for optimization  and go into that page of publication
        detail_soup = self._fetch_tag_of_publication(session, url_publication)
        if detail_soup is None:
            return None

        try:
            #creates the output of correct format
            return self._build_output(publication,
                                      detail_soup,
                                      url_publication,
                                      date)
        except Exception as e:
            logger.exception("Can not parse data from publication %s: %s",url_publication,e)
            return None

    def _fetch_tag_of_publication(self,
                                  session,
                                  url_publication):
        #Getting into page of publication and optimazied by BeautifulSoup
        try:
            response = session.get(url_publication)
            time.sleep(random.uniform(1, 2))
            return BeautifulSoup(response.text, "lxml", parse_only=self._detail_strainer())
        except Exception as e:
            logger.warning("Can not connect to publication %s: %s", url_publication, e)
            return None

    @abstractmethod
    def _build_output(self,
                      publication,
                      detail_soup,
                      url_publication,
                      date):
        ...
    @abstractmethod
    def _detail_strainer(self):
        ...

    @abstractmethod
    def _filter_main(self):
        ...

    @abstractmethod
    def _count_pages(self, soup):
        ...

    @abstractmethod
    def _main_url(self):
        ...

    @abstractmethod
    def _next_main_page(self, soup):
        ...

    @abstractmethod
    def _iter_publications(self, soup):
        ...
    @abstractmethod
    def _date_of_post(self, soup):
        ...
    @abstractmethod
    def _get_publication_url(self, publication):
        ...