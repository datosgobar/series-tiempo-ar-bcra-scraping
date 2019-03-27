from datetime import date, timedelta

import json

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .utils import get_most_recent_previous_business_day


class Scraper:

    def __init__(self, url, rates, *args, **kwargs):
        self.browser_driver = None
        self.url = url
        self.rates = rates

        super(Scraper, self).__init__(*args, **kwargs)

    def _create_browser_driver(self):
        options = webdriver.ChromeOptions()
        options.headless = True

        browser_driver = webdriver.Chrome(options=options)

        return browser_driver

    def get_browser_driver(self):
        if not self.browser_driver:
            self.browser_driver = self._create_browser_driver()

        return self.browser_driver

    def fetch_content(self, start_date, end_date):
        contents = []
        day_count = (end_date - start_date).days + 1

        for single_date in (start_date + timedelta(n) for n in range(day_count)):
            contents.append(self.fetch_day_content(single_date))

        return contents

    def fetch_day_content(self, single_date):
        browser_driver = self.get_browser_driver()
        browser_driver.get(self.url)
        elem = browser_driver.find_element_by_name('fecha')
        elem.send_keys(single_date.strftime("%d/%m/%Y") + Keys.RETURN)
        content = browser_driver.page_source

        return content

    def parse(self, contents):
        parsed_contents = []
        for content in contents:
            parsed = self.parse_day_content(content)

            if parsed:
                parsed_contents.append(parsed)

        return parsed_contents

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

        # TODO: validate keys
        for row in rows:
            cols = row.find_all('td')
            parsed[cols[0].text] = cols[1].text

        return parsed

    def run(self, start_date, end_date):
        contents = self.fetch_content(start_date, end_date)
        parsed = self.parse(contents)

        return parsed
