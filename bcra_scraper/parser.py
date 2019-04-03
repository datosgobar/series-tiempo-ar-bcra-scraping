from datetime import date, timedelta

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .utils import get_most_recent_previous_business_day


class ExchangeRateScraper:

    url = 'http://www.bcra.gov.ar/PublicacionesEstadisticas/Evolucion_moneda.asp'

    def fetch_content(self, content_date):
        browser = webdriver.Chrome()
        browser.get(self.url)
        elem = browser.find_element_by_name('Fecha')
        elem.send_keys(content_date.strftime("%d/%m/%Y"))
        coin = browser.find_element_by_name('Moneda')
        coin.send_keys('Peso')

        submit_button = browser.find_element_by_class_name('btn-primary')
        submit_button.click()

        content = browser.page_source
        return content

    def parse(self, content=''):
        soup = BeautifulSoup(content, "html.parser")
        parsed = {}
        table = soup.find('table')
        head = table.find('thead')
        body = table.find('tbody')

        if not body:
            return parsed

        rows = body.find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            parsed['indice_tiempo'] = cols[0].text[5:].strip()
            parsed['tipo_pase'] = cols[1].text[5:].strip()
            parsed['tipo_cambio'] = cols[2].text[5:].strip()

        return parsed

    def run(self):
        scrape_date = get_most_recent_previous_business_day(
            date.today() - timedelta(days=1)
        )
        content = self.fetch_content(scrape_date)
        parsed = self.parse(content)
        print(parsed)
        return parsed
