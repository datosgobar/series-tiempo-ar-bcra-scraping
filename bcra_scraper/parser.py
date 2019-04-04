from datetime import date, timedelta, datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .utils import get_most_recent_previous_business_day


class ExchangeRateScraper:

    url = 'http://www.bcra.gov.ar/PublicacionesEstadisticas/Evolucion_moneda.asp'

    def fetch_content(self, start_date):
        browser = webdriver.Chrome()
        browser.get(self.url)
        elem = browser.find_element_by_name('Fecha')
        elem.send_keys(start_date.strftime("%d/%m/%Y"))
        coin = browser.find_element_by_name('Moneda')
        coin.send_keys('Peso')

        submit_button = browser.find_element_by_class_name('btn-primary')
        submit_button.click()

        content = browser.page_source
        return content

    def parse(self, contents, end_date):
        soup = BeautifulSoup(contents, "html.parser")
        
        table = soup.find('table')
        head = table.find('thead')
        body = table.find('tbody')

        rows = body.find_all('tr')
        parsed_contents = []
    
        for row in rows:
            cols = row.find_all('td')
            parsed = {}

            row_indice_tiempo = datetime.strptime(cols[0].text[5:].strip(), '%d/%m/%Y')

            if row_indice_tiempo <= end_date:
                parsed['indice_tiempo'] = cols[0].text[5:].strip()
                parsed['tipo_pase'] = cols[1].text[5:].strip()
                parsed['tipo_cambio'] = cols[2].text[5:].strip()
                parsed_contents.append(parsed)
                
        return parsed_contents

    def run(self, start_date, end_date):
        contents = self.fetch_content(start_date)
        parsed = self.parse(contents, end_date)
        print(parsed)
        return parsed
