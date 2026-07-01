from datetime import datetime, timedelta
import time
import random
import re
import math
import requests
from bs4 import BeautifulSoup,SoupStrainer



class Crawler:
    def __init__(self):
        self.MAIN_URL = "https://reality.bazos.sk/"
        self.HEADERS=  {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
        }

        self.descript_filter_publication = SoupStrainer("div", class_="maincontent")
        self.filter_main = SoupStrainer("div", class_=["maincontent", "strankovani"])
        self.exceptions = {"Dohodou", "Zadarmo"}
        self.links = [
        ["https://reality.bazos.sk/prenajmu/byt/","https://reality.bazos.sk/prenajmu/byt/?hledat=&rubriky=reality&hlokalita=81101&humkreis=10&cenaod=&cenado=&order=&crp=&kitx=ano"]
        #["https://reality.bazos.sk/prenajmu/dom/","https://reality.bazos.sk/prenajmu/dom/?hledat=&rubriky=reality&hlokalita=81101&humkreis=10&cenaod=&cenado=&Submit=H%C4%BEada%C5%A5&order=&crp=&kitx=ano"]
        #["https://reality.bazos.sk/prenajmu/podnajom/","https://reality.bazos.sk/prenajmu/podnajom/?hledat=&rubriky=reality&hlokalita=81101&humkreis=10&cenaod=&cenado=&order=&crp=&kitx=ano"]
        ]

        self.date_limit = datetime.now() - timedelta(weeks=4)
        self._stop = False

    def start_processing(self):
        self._stop = False
        for link in self.links:
             yield from self.crawl_bazos(link[0], link[1])
    def crawl_bazos(self,link_first_main, link_with_sorted):
        try:
            session = requests.Session()
            session.headers.update(self.HEADERS)
            #Simulating real action of user
            session.get(self.MAIN_URL)
            time.sleep(random.randint(1, 3))
            session.get(link_first_main)
            time.sleep(random.randint(1, 3))

            first_response = session.get(link_with_sorted)
            time.sleep(random.uniform(1, 2))

            #Count number of pages
            soup = BeautifulSoup(first_response.text, "lxml", parse_only=self.filter_main)
            stats_tag = soup.find('div', class_='inzeratynadpis')
            stats_text = stats_tag.get_text().strip().split("z")
            cislo = int(stats_text[-1].strip().replace(" ", ""))
            total_pages =  math.ceil(cislo / 20)
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to link : {e}")
            return
        except Exception as e:
            print(f"Can not count number of pages : {e}")
            return
        yield from self.process_main(session, link_with_sorted, first_response, total_pages)

    def process_main(self,session, start_url,
                     first_response, total_pages):
        curr_page = start_url
        response = first_response
        previous_page = None
        for pag_index in range(total_pages):
            if pag_index > 0:
                if previous_page:
                    session.headers.update({"Referer": previous_page})

                try:
                    response = session.get(curr_page, timeout=10)
                    response.raise_for_status()
                except Exception as e:
                    print(f"Can not connect to site {curr_page}: {e}")
                    continue
                time.sleep(random.uniform(1, 2))

            soup = BeautifulSoup(response.text, "lxml", parse_only=self.filter_main)

            yield self.process_page(session, soup, curr_page)

            if self._stop:
                break
            previous_page = curr_page
            next_page_url = self.next_main_page(soup)
            if not next_page_url:
                break
            curr_page = next_page_url

    def process_page(self,session, soup, page_url):
        data = []
        accommodations = soup.find_all('div', class_="inzeraty inzeratyflex")
        for accommodation in accommodations:
            if self._stop:
                break
            publication = self.process_publication(session, accommodation, page_url)
            if publication:
                data.append(publication)
        return data

    def process_publication(self,session,
                            accommodation,
                            page_url):

        date = self.date_of_post(accommodation)
        if date < self.date_limit:
            self._stop = True
            return None

        link_publication_tag = accommodation.find('div', class_='inzeratynadpis')
        a_tag = link_publication_tag.find('a', href=True)
        if a_tag is None:
            return
        raw_href = a_tag['href']
        url_publication = "https://reality.bazos.sk" + raw_href

        session.headers.update({"Referer": page_url})
        soup_aparment = self.move_to_inzerat(session, url_publication)

        if soup_aparment is None: return
        #Getting information
        try:
            price_tag = accommodation.find('div', class_='inzeratycena')
            price = price_tag.text.strip() if price_tag else "Не вказано"

            location_tag = accommodation.find('div', class_='inzeratylok')
            location = " ".join(location_tag.get_text(separator=" ").strip().split()) if location_tag else "Невідомо"

            title_tag = soup_aparment.find('h1', class_='nadpisdetail')
            title = title_tag.text.strip() if title_tag else "Без назви"

            paragraphs = soup_aparment.select('div.popisdetail')
            description = '\n'.join([paragraph.text.strip() for paragraph in paragraphs]) if paragraphs else ""
        except AttributeError as e:
            print(f"Can not parse data from publication {page_url}: {e}")
            return
        price_text = f"Cena tohto bytu je {price}.\n" if price != "V texte" else ""

        final_text = (
            f"Title: {title}\n"
            f"{description}\n"
            f"{price_text}"
            f"Lokalita je {location}."
        )
        return {"Source": "Bazos",
                "Link":url_publication,
                "Description":final_text,
                "State": "raw",
                "Date of processing": datetime.now().strftime("%Y-%m-%d"),
                "Date of publishing": date.strftime("%Y-%m-%d")}

    def move_to_inzerat(self,session, url_publication):
            #from main to publication
        try:
            response_publication = session.get(url_publication)
            time.sleep(random.uniform(1, 2))
            soup_publication = BeautifulSoup(response_publication.text, "lxml",
                                         parse_only=self.descript_filter_publication)
        except Exception as e:
            print(f"Can not connect to publication {url_publication}: {e}")
            return
        return soup_publication



    def date_of_post(self, soup_publication):
        #date of post from publication
        try:
            date_tag = soup_publication.find('span', class_='velikost10')
            if not date_tag:
                return None
            date_match = re.search(r'\[(.+?)\]', date_tag.text)
            if not date_match:
                return None
            date_str = date_match.group(1).replace(" ", "").strip().replace("-", ".")
            parts = date_str.split(".")
            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        except Exception as e:
            print(f"Failed to parse date: {e}")
            return

    def next_main_page(self, soup):
        #from main_hub
        pagination_div = soup.find('div', class_='strankovani')
        if not pagination_div:
            return None

        next_div = next((a for a in pagination_div.find_all('a') if 'alšia' in a.get_text()), None)
        if not next_div:
            return None

        return "https://reality.bazos.sk" + next_div['href']
    def add_links(self,default_link, sorted_link):
        self.links.append([default_link,sorted_link])

if __name__ == "__main__":
    crawler = Crawler()
    data = crawler.start_processing()
    for item in data:
        print(item)