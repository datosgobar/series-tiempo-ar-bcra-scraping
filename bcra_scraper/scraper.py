from datetime import date, timedelta

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .utils import get_most_recent_previous_business_day


class Scraper:

    url = 'http://www.bcra.gov.ar/PublicacionesEstadisticas/libor.asp'

    def fetch_content(self, start_date, end_date):
        contents = []
        day_count = (end_date - start_date).days + 1

        for single_date in (start_date + timedelta(n) for n in range(day_count)):
            contents.append(self.fetch_day_content(single_date))

        return contents

    def fetch_day_content(self, single_date):
        browser = webdriver.Chrome()
        browser.get(self.url)
        elem = browser.find_element_by_name('fecha')
        elem.send_keys(single_date.strftime("%d/%m/%Y") + Keys.RETURN)
        content = browser.page_source

        return content

    def parse(self, contents):
        parsed = []

        for content in contents:
            parsed.append(self.parse_day_content(content))

        return parsed

    def parse_day_content(self, contents):
        soup = BeautifulSoup(contents, "html.parser")
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

    def run(self, start_date, end_date):
        contents = self.fetch_content(start_date, end_date)
        parsed = self.parse(contents)

        return parsed