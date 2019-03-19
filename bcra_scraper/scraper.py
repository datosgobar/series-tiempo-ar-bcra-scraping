from bs4 import BeautifulSoup

class Scraper:
    
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