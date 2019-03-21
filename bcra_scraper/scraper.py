from datetime import date, timedelta

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .utils import get_most_recent_previous_business_day


class Scraper:

    url = 'http://www.bcra.gov.ar/PublicacionesEstadisticas/libor.asp'

    def fetch_content(self, content_date):
        browser = webdriver.Chrome()
        browser.get(self.url)
        elem = browser.find_element_by_name('fecha')
        elem.send_keys(content_date.strftime("%d/%m/%y") + Keys.RETURN)
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

        parsed['indice_tiempo'] = head.findAll('th')[0].text[14:].strip()

        for row in rows:
            cols = row.find_all('td')
            parsed[cols[0].text] = cols[1].text

        return parsed

    def run(self):
        scrape_date = get_most_recent_previous_business_day()
        content = self.fetch_content(scrape_date)
        parsed = self.parse(content)
        return parsed