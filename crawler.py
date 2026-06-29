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

        self.date_limit = datetime.now() - timedelta(weeks=3)
        self._stop = False

    def start_processing(self):
        data = []
        self._stop = False
        for link in self.links:
            data.extend(self.crawl_bazos(link[0], link[1]))
        return data
    def crawl_bazos(self,link_first_main,link_with_sorted):
        session = requests.Session()
        session.headers.update(self.HEADERS)

        session.get(self.MAIN_URL)
        time.sleep(random.randint(1, 3))
        session.get(link_first_main)
        time.sleep(random.randint(1, 3))

        first_response = session.get(link_with_sorted)
        time.sleep(random.uniform(1, 2))

        total_pages = self.number_iteration_getter(first_response)
        return self.process_main(session, link_with_sorted, first_response, total_pages)

    def process_main(self,session,start_url,first_response,total_pages):
        data = []
        curr_page = start_url
        response = first_response
        previous_page = None
        for pag_index in range(total_pages):
            if pag_index > 0:
                if previous_page:
                    session.headers.update({"Referer": previous_page})
                response = session.get(curr_page)
                time.sleep(random.uniform(1, 2))
            soup = BeautifulSoup(response.text, "lxml", parse_only=self.filter_main)
            data.extend(self.process_page(session, soup, curr_page))
            if self._stop:
                break
            previous_page = curr_page
            next_page_url = self.next_main_page(soup)
            if not next_page_url:
                break
            curr_page = next_page_url
        return data
    def process_page(self,session,soup,page_url):
        data = []
        accommodations = self.all_advertisement_getter(soup)
        for accommodation in accommodations:
            if self._stop:
                break
            publication = self.process_publication(session, accommodation, page_url)
            if publication:
                data.append(publication)
        return data

    def process_publication(self,session,accommodation,page_url):
        url_publication = self.link_getter(accommodation)

        price = self.price_getter(accommodation)
        if price in self.exceptions:
            return
        location = self.location_getter(accommodation)
        session.headers.update({"Referer": page_url})

        soup_aparment = self.move_to_inzerat(session,url_publication)

        title = self.title_publication(soup_aparment)
        date = self.date_of_post(soup_aparment)
        if date < self.date_limit:
            self._stop = True
            return None
        description = self.description_publication(soup_aparment)
        price_text = f"Cena tohto bytu je {price}.\n" if price != "V texte" else ""

        final_text = (
            f"Title: {title}\n"
            f"{description}\n"
            f"{price_text}"
            f"Lokalita je {location}."
        )
        return self.construct_dict_input(
            source="Bazos",
            link=url_publication,
            description=final_text,
            state="Not proccessed",
            data_post=date.strftime("%Y-%m-%d"),
            data_crawler=datetime.now().strftime("%Y-%m-%d")
        )

    def number_iteration_getter(self, responce):
        #main_hub_once
        soup = BeautifulSoup(responce.text, "lxml", parse_only=self.filter_main)
        stats_tag = soup.find('div', class_='inzeratynadpis')
        stats_text = stats_tag.get_text().strip().split("z")
        cislo = int(stats_text[-1].strip().replace(" ", ""))
        return math.ceil(cislo / 20)

    def all_advertisement_getter(self,soup):
        #main_hub
        return soup.find_all('div', class_="inzeraty inzeratyflex")

    def link_getter(self,publication):
        #main_hub_publication
        link_publication_tag = publication.find('div', class_='inzeratynadpis')
        a_tag = link_publication_tag.find('a', href=True)
        raw_href = a_tag['href']
        return "https://reality.bazos.sk" + raw_href

    def price_getter(self,publication):
        #main_hub_publication
        price_tag = publication.find('div', class_='inzeratycena')
        return price_tag.text.strip()

    def location_getter(self,publication):
        #main_hub_publication
        location_tag = publication.find('div', class_='inzeratylok')
        location = location_tag.get_text(separator=" ").strip()
        return " ".join(location.split())

    def move_to_inzerat(self,session,url_publication):
        #from main to publication
        response_publication = session.get(url_publication)
        time.sleep(random.uniform(1, 2))
        soup_publication = BeautifulSoup(response_publication.text, "lxml",
                                     parse_only=self.descript_filter_publication)
        return soup_publication

    def title_publication(self,soup_publication):
        #title from publication
        h1_tag = soup_publication.find('h1', class_='nadpisdetail')
        return h1_tag.text.strip()

    def date_of_post(self,soup_publication):
        #date of post from publication
        date_tag = soup_publication.find('span', class_='velikost10')
        date = re.search(r'\[(.+?)\]', date_tag.text)
        date = date.group(1).replace(" ", "").strip().replace("-",".")
        parts = date.split(".")
        day,month,year = int(parts[0]),int(parts[1]),int(parts[2])
        return  datetime(year,month,day)

    def description_publication(self,soup_publication):
        paragraphs = soup_publication.select('div.popisdetail')
        return '\n'.join([paragraph.text.strip() for paragraph in paragraphs])

    def construct_dict_input(self,source,link,
                             description,state,
                             data_post,data_crawler):
        data = {"Source": source,
                "Link":link,
                "Description":description,
                "State": state,
                "Date of processing": data_post,
                "Date of publishing": data_crawler}
        return data

    def next_main_page(self,soup):
        #from main_hub
        pagination_div = soup.find('div', class_='strankovani')
        if not pagination_div:
            return None

        next_div = next((a for a in pagination_div.find_all('a') if 'alšia' in a.get_text()), None)
        if not next_div:
            return None

        return "https://reality.bazos.sk" + next_div['href']
    def add_links(self,default_link,sorted_link):
        self.links.append([default_link,sorted_link])

#if __name__ == "__main__":
    #crawler = Crawler()
    #data = crawler.start_processing()
    #for item in data:
        #print(item)