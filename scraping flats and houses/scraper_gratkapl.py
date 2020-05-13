import time
import requests
from slugify import slugify
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime


class PageScrapper:

    def __init__(self, url):

        self.url = url
        self.last_page = self.get_last_page_number()

        print(f"Total number of pages: {self.last_page}")
    
    def read_page_content(self, url):
        page = requests.get(url)
        return BeautifulSoup(page.content, "html.parser")

    def get_last_page_number(self):
        page = self.read_page_content(self.url)
        
        last_page_element = page.find('input', {'aria-label': 'Numer strony wyników'})
        return int((last_page_element["max"]))


    def parse_advertisement(self, url):

        data = {}
        page = self.read_page_content(url)
        
        container = page.find('div', {'class': 'sticker__container column small-12'}) 

        data['tytul'] = container.find('h1', {'class': 'sticker__title'}).get_text().strip()
        data['cena'] = int(container.find('div', {'class': 'priceInfo'}).find('span',{'class':"priceInfo__value"}).get_text().strip().replace('zł', '').replace(' ', '').replace(',','.'))
        data['cena_waluta'] = container.find('div', {'class': 'priceInfo'}).find('span',{'class':"priceInfo__currency"}).get_text().strip()
        data['cena_za_metr'] = float(container.find('div', {'class': 'priceInfo'}).find('span',{'class':"priceInfo__additional"}).get_text().strip().replace('zł/m2', '').replace(' ', '').replace(',','.'))

        container2 = page.find('div', {'class': 'offer__inner row'}) 
        
        data['id_ogloszenia'] = container2.find('p', {'class': 'contact__offerId'}).find('span').get_text().strip()
        data['tresc'] = container2.find('div', {'class': 'description'}).find('div', {'class': 'description__rolled ql-container'}).get_text().strip()

        if container2.find('div', {'class': 'gallery'}) is not None:
            data['zdjecie'] = True
        else:
            data['zdjecie'] = False

        parameters = container2.find('div', {'class': 'parameters__container'}).findAll('li')

        for item in range(len(parameters)):

            if parameters[item].find('div',{'class': 'dfp'}):
                break
            else:
                parameter_title = parameters[item].find('span')
                parameter_value = parameters[item].find('b',{'class':'parameters__value'})

                if parameter_value is not None:
                    data[slugify(parameter_title.get_text())] = parameter_value.get_text()
                
                if (parameters[item].find('span').get_text() == "Dostępność od"):
                    data['data_dostepne'] = parameters[item].find('b',{'class':'parameters__value'}).get_text().strip()
                    #print(data['data_dostepne'])

                if (parameters[item].find('span').get_text() == "Powierzchnia w m2"):
                    data['powierzchnia'] = float(parameters[item].find('b',{'class':'parameters__value'}).get_text().strip().replace('m2', '').replace(' ', '').replace(',','.'))
                    #print(data['powierzchnia'])

                if (parameters[item].find('span').get_text() == "Liczba pokoi"):
                    data['liczba_pokoi'] = parameters[item].find('b',{'class':'parameters__value'}).get_text().strip()
                    #print(data['liczba_pokoi'])

                if (parameters[item].find('span').get_text() == "Liczba pięter w budynku"):
                    data['liczba_pieter_budynku'] = parameters[item].find('b',{'class':'parameters__value'}).get_text().strip()
                    #print(data['liczba_pieter_budynku'])

                if (parameters[item].find('span').get_text() == "Typ zabudowy"):
                    data['rodzaj_zabudowy'] = parameters[item].find('b',{'class':'parameters__value'}).get_text().strip()
                    #print(data['rodzaj_zabudowy'])
                
                if (parameters[item].find('span').get_text() == "Rok budowy"):
                    data['rok_budowy'] = int(parameters[item].find('b',{'class':'parameters__value'}).get_text().strip())
                    #print(data['rok_budowy'])

                if (parameters[item].find('span').get_text() == "Lokalizacja"):
                    data['adres'] = parameters[item].find('b',{'class':'parameters__value'}).get_text().strip().replace(' ', '')
                    #print(data['adres'])

                if (parameters[item].find('span').get_text() == "Piętro"):
                    data['pietro'] = parameters[item].find('b',{'class':'parameters__value'}).get_text().strip()
                    #print(data['pietro'])

                if (parameters[item].find('span').get_text() == "Typ zabudowy"):
                    data['typ_domu'] = parameters[item].find('b',{'class':'parameters__value'}).get_text().strip()
                    #print(data['typ_domu'])

                if (parameters[item].find('span').get_text() == "Powierzchnia działki w m2"):
                    data['powierzchnia_dzialki'] = float(parameters[item].find('b',{'class':'parameters__value'}).get_text().strip().replace('m2', '').replace(' ', '').replace(',','.'))
                    #print(data['powierzchnia_dzialki'])

                if (parameters[item].find('span').get_text() == "Stan"):
                    data['wykonczenie'] = parameters[item].find('b',{'class':'parameters__value'}).get_text().strip()
                    #print(data['wykonczenie'])

                if (parameters[item].find('span').get_text() == "Forma kuchni"):
                    data['kuchnia'] = parameters[item].find('b',{'class':'parameters__value'}).get_text().strip()
                    #print(data['kuchnia'])

        return data
    

    def find_advertisements(self):
            all_data = []

            for page_number in range(self.last_page):

                print(f"Page {page_number+1}/{self.last_page} processing...")

                page = self.read_page_content(self.url.replace('?page=1',f'?page={page_number+1}'))
                advertisements = page.findAll('a', {'class': 'teaserEstate__anchor'})
                actualization_date = page.findAll('ul', {'class': 'teaserEstate__details'})
                
                for advertisement_index in range(len(advertisements)):
                    data = self.parse_advertisement(advertisements[advertisement_index]['href'])
                    data['data_aktualizacji'] =  datetime.strptime((actualization_date[advertisement_index].find('li',{'class':'teaserEstate__info'}).get_text().strip().replace('Aktualizacja:', '').replace(' ', '')),'%d.%m.%Y').date().strftime('%Y-%m-%d') 
                    data['typ_nieruchomosci'] = re.findall('mieszkania|domy', self.url)[0]
                    all_data.append(data)
                    print(data)
                    time.sleep(2)
            return all_data
                    

    def save_json(self):
        with open('gratkapl_mieszkania_sopot.json', 'w') as file:
            json.dump(self.find_advertisements(), file)



URL1 = 'https://gratka.pl/nieruchomosci/mieszkania/gdansk/sprzedaz'
URL2 = 'https://gratka.pl/nieruchomosci/mieszkania/gdynia/sprzedaz'
URL3 = 'https://gratka.pl/nieruchomosci/mieszkania/sopot/sprzedaz?page=1&cena-calkowita:min=100000'
URL4 = 'https://gratka.pl/nieruchomosci/domy/gdansk/sprzedaz'
URL5 = 'https://gratka.pl/nieruchomosci/domy/gdynia/sprzedaz'
URL6 = 'https://gratka.pl/nieruchomosci/domy/sopot/sprzedaz?page=1&cena-calkowita:min=100000'
scraper = PageScrapper(URL3)
#scraper.find_advertisements()
scraper.save_json()

# lokalizacja: miasto / dzielnica lub wojewodztwo / wojewodztow lub nan

