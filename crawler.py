import time
import random
import re
import math
import requests
from bs4 import BeautifulSoup,SoupStrainer

class Crawler:
    def __init__(self):
        self._data = []
        self.MAIN_URL = "https://reality.bazos.sk/"
        self.HEADERS=  {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
        }

        self.popis_filter_inzerat = SoupStrainer("div", class_="maincontent")
        self.filter_main = SoupStrainer("div", class_=["maincontent", "strankovani"])
        self.exceptions = {"Dohodou", "Zadarmo"}

        self.already_exist = set()


    def start_process(self):
        links = [
        ["https://reality.bazos.sk/prenajmu/byt/","https://reality.bazos.sk/prenajmu/byt/?hledat=&rubriky=reality&hlokalita=81101&humkreis=10&cenaod=&cenado=&order=&crp=&kitx=ano"]
        #["https://reality.bazos.sk/prenajmu/dom/","https://reality.bazos.sk/prenajmu/dom/?hledat=&rubriky=reality&hlokalita=81101&humkreis=10&cenaod=&cenado=&Submit=H%C4%BEada%C5%A5&order=&crp=&kitx=ano"]
        #["https://reality.bazos.sk/prenajmu/podnajom/","https://reality.bazos.sk/prenajmu/podnajom/?hledat=&rubriky=reality&hlokalita=81101&humkreis=10&cenaod=&cenado=&order=&crp=&kitx=ano"]
        ]
        for link in links:
            self.crawl_bazos(link[0],link[1])
    def add_inzerat(self, inzerat_dict):
        self._data.append(inzerat_dict)
    def get_data(self):
        return self._data
    def crawl_bazos(self,link_first_main,link_with_sorted):
        previous_page = None
        number = 0

        session = requests.Session()
        session.headers.update(self.HEADERS)

        session.get(self.MAIN_URL)
        time.sleep(random.randint(1,3))
        session.get(link_first_main)
        time.sleep(random.randint(1,3))
        curr_page = link_with_sorted

        response = session.get(curr_page)
        time.sleep(random.uniform(1, 2))

        pocet_iteracie = self.pocet_iteracie_getter(response)


        while pocet_iteracie > number:
            if previous_page:
                session.headers.update({"Referer": previous_page})
                response = session.get(curr_page)
                time.sleep(random.uniform(1, 2))

            soup = BeautifulSoup(response.text,"lxml",parse_only = self.filter_main)  #,parse_only = self.filter_main

            inzeraty = self.all_advertisement_getter(soup)
            for inzerat in inzeraty:

                url_inzerat = self.link_getter(inzerat)

                if url_inzerat in self.already_exist:
                    continue

                cena = self.cena_getter(inzerat)

                if cena in self.exceptions:
                    continue

                lokalita = self.lokalita_getter(inzerat)

                session.headers.update({"Referer": curr_page})


                soup_inzerat = self.move_to_inzerat(session,url_inzerat)

                title = self.title_inzerat(soup_inzerat)

                date = self.date_of_post(soup_inzerat)

                description = self.description_inzerat(soup_inzerat)

                cena_text = f"Cena tohto bytu je {cena}.\n" if cena != "V texte" else ""

                final_text = (
                    f"Title: {title}\n"
                    f"{description}\n"
                    f"{cena_text}"
                    f"Lokalita je {lokalita}."
                )

                current_time = time.localtime()
                formatted_data_curr_time = time.strftime("%d-%m-%Y", current_time)

                data_dict = self.construct_dict_input(source="Bazos",link=url_inzerat,
                             description=final_text,state="Not proccessed",
                             data_post=date,data_crawler=formatted_data_curr_time)

                self.add_inzerat(data_dict)
                self.already_exist.add(url_inzerat)
                print(data_dict)

            previous_page = curr_page

            next_page_url = self.next_main_page(soup)
            if not next_page_url:
                break
            print(number)
            number +=1
            curr_page = next_page_url

    def pocet_iteracie_getter(self, responce):
        #main_hub_once
        soup = BeautifulSoup(responce.text, "lxml", parse_only=self.filter_main)
        stats_tag = soup.find('div', class_='inzeratynadpis')
        stats_text = stats_tag.get_text().strip().split("z")
        cislo = int(stats_text[-1].strip().replace(" ", ""))
        return math.ceil(cislo / 20)

    def all_advertisement_getter(self,soup):
        #main_hub
        return soup.find_all('div', class_="inzeraty inzeratyflex")

    def link_getter(self,inzerat):
        #main_hub_inzerat
        link_inzer_tag = inzerat.find('div', class_='inzeratynadpis')
        a_tag = link_inzer_tag.find('a', href=True)
        raw_href = a_tag['href']
        return "https://reality.bazos.sk" + raw_href

    def cena_getter(self,inzerat):
        #main_hub_inzerat
        cena_tag = inzerat.find('div', class_='inzeratycena')
        return cena_tag.text.strip()

    def lokalita_getter(self,inzerat):
        #main_hub_inzerat
        lokalita_tag = inzerat.find('div', class_='inzeratylok')
        lokalita = lokalita_tag.get_text(separator=" ").strip()
        return " ".join(lokalita.split())

    def move_to_inzerat(self,session,url_inzerat):
        #from main to inzerat
        response_inzerat = session.get(url_inzerat)
        time.sleep(random.uniform(1, 2))
        soup_inzerat = BeautifulSoup(response_inzerat.text, "lxml",
                                     parse_only=self.popis_filter_inzerat)
        return soup_inzerat

    def title_inzerat(self,soup_inzerat):
        #title from inzerat
        h1_tag = soup_inzerat.find('h1', class_='nadpisdetail')
        return h1_tag.text.strip()

    def date_of_post(self,soup_inzerat):
        #date of post from inzerat
        date_tag = soup_inzerat.find('span', class_='velikost10')
        date = re.search(r'\[(.+?)\]', date_tag.text)
        return  date.group(1).replace(" ", "").strip().replace("-",".")

    def description_inzerat(self,soup_inzerat):
        paragraphs = soup_inzerat.select('div.popisdetail')
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


#if __name__ == '__main__':
    #s = Crawler()
    #s.start_process()
    #k = s.get_data()
    #for s in k:
        #print(s)