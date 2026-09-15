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
    def __init__(self, seen_urls, max_consecutive_duplicates):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.google.com/",
        }
        self._links = []
        self._seen_urls = set(seen_urls) if seen_urls is not None else set()
        self._max_consecutive_duplicates = max_consecutive_duplicates

    def links(self):
        return self._links


    def add_links(self, main_link, sorted_link):
        #Can add more starer links
        self._links.append([main_link,sorted_link])

    def start_processing(self):
        #Start crawing
        for main_link, sorted_link in self._links:
            yield from self._crawl(main_link, sorted_link)

    def start_processing(self):
        for main_link, sorted_link in self._links:
            yield from self._crawl(main_link, sorted_link)

    def _crawl(self, main_link, sorted_link):
        try:
            session = requests.Session()
            session.headers.update(self.headers)
            session.get(self._main_url())
            time.sleep(random.randint(1, 3))
            session.get(main_link)
            time.sleep(random.randint(1, 3))

            first_response = session.get(sorted_link)
            time.sleep(random.uniform(1, 2))

            soup = BeautifulSoup(first_response.text, "lxml", parse_only=self._filter_main())
            total_pages = self._count_pages(soup)

        except requests.exceptions.RequestException as e:
            logger.exception("Failed to connect to link %s: %s", main_link, e)
            return
        except Exception as e:
            logger.exception("Can not count number of pages: %s: %s", main_link, e)
            return

        logger.info("Crawling %s with %d pages", sorted_link, total_pages)

        queue = self._collect_links(session, sorted_link, first_response, total_pages)
        queue.reverse()

        logger.info("Collected %d new publications to process", len(queue))

        yield from self._process_pending(session, queue)


    def _collect_links(self, session, start_url, first_response, total_pages):
        curr_page = start_url
        response = first_response
        previous_page = None
        queue = []
        consecutive_duplicates = 0

        for pag_index in range(total_pages):
            if pag_index > 0:
                if previous_page:
                    session.headers.update({"Referer": previous_page})
                try:
                    response = session.get(curr_page, timeout=10)
                    response.raise_for_status()
                except Exception as e:
                    logger.exception("Can not connect to site %s: %s", curr_page, e)
                    break
                time.sleep(random.uniform(1, 2))

            soup = BeautifulSoup(response.text, "lxml", parse_only=self._filter_main())

            reached_limit = self._scan_page_for_links(soup, curr_page, queue, consecutive_duplicates)
            if reached_limit is not None:
                consecutive_duplicates = reached_limit
            if consecutive_duplicates >= self._max_consecutive_duplicates:
                logger.info(
                    "Reached %d consecutive known publications",
                    self._max_consecutive_duplicates,
                )
                break

            previous_page = curr_page
            next_page_url = self._next_main_page(soup)
            if not next_page_url:
                break
            curr_page = next_page_url

        return queue

    def _scan_page_for_links(self, soup, page_url, queue, consecutive_duplicates):
        for publication_tag in self._iter_publications(soup):
            url_publication = self._get_publication_url(publication_tag)
            if not url_publication:
                continue

            if url_publication in self._seen_urls:
                consecutive_duplicates += 1
                if consecutive_duplicates >= self._max_consecutive_duplicates:
                    return consecutive_duplicates
            else:
                consecutive_duplicates = 0
                queue.append((publication_tag, url_publication, page_url))

        return consecutive_duplicates

    def _process_pending(self, session, queue):
        for publication_tag, url_publication, page_url in queue:
            session.headers.update({"Referer": page_url})

            detail_soup = self._fetch_tag_of_publication(session, url_publication)
            if detail_soup is None:
                continue

            try:
                result = self._build_output(publication_tag, detail_soup, url_publication)
            except Exception as e:
                logger.exception("Can not parse data from publication %s: %s", url_publication, e)
                continue

            if result is None:
                continue
            self._seen_urls.add(url_publication)
            yield result

    def _fetch_tag_of_publication(self, session, url_publication):
        try:
            response = session.get(url_publication, timeout=10)
            response.raise_for_status()
            time.sleep(random.uniform(1, 2))
            return BeautifulSoup(response.text, "lxml", parse_only=self._detail_strainer())
        except Exception as e:
            logger.warning("Can not connect to publication %s: %s", url_publication, e)
            return None

    @abstractmethod
    def _build_output(self,
                      publication,
                      detail_soup,
                      url_publication):
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
    def _get_publication_url(self, publication):
        ...