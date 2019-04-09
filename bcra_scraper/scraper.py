from datetime import date, timedelta, datetime
from decimal import Decimal

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


class BCRAScraper:

    def __init__(self, url, *args, **kwargs):
        self.browser_driver = None
        self.url = url

    def _create_browser_driver(self):
        options = webdriver.ChromeOptions()
        options.headless = True

        browser_driver = webdriver.Chrome(options=options)

        return browser_driver

    def get_browser_driver(self):
        if not self.browser_driver:
            self.browser_driver = self._create_browser_driver()

        return self.browser_driver

    def fetch_contents(self, start_date, end_date):
        raise NotImplementedError

    def parse_contents(self, start_date, end_date):
        raise NotImplementedError

    def run(self, start_date, end_date):
        contents = self.fetch_contents(start_date, end_date)
        parsed = self.parse_contents(contents)

        print(parsed)
        return parsed


class BCRALiborScraper(BCRAScraper):

    def __init__(self, url, rates, *args, **kwargs):
        self.rates = rates

        super(BCRALiborScraper, self).__init__(url, *args, **kwargs)

    def fetch_contents(self, start_date, end_date):
        contents = []
        day_count = (end_date - start_date).days + 1

        for single_date in (start_date + timedelta(n) for
                            n in range(day_count)):
            contents.append(self.fetch_day_content(single_date))

        return contents

    def fetch_day_content(self, single_date):
        browser_driver = self.get_browser_driver()
        browser_driver.get(self.url)
        elem = browser_driver.find_element_by_name('fecha')
        elem.send_keys(single_date.strftime("%d/%m/%Y") + Keys.RETURN)
        content = browser_driver.page_source

        return content

    def parse_contents(self, contents):
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

    def preprocess_rows(self, rates, rows):
        preprocessed_rows = []

        for row in rows:
            preprocessed_row = {}
            for rate in rates:
                preprocessed_row[rates[rate]] = \
                    Decimal((row[rate]).replace(',', '.'))/100

            row_date = row['indice_tiempo'].split('/')
            preprocessed_row['indice_tiempo'] = date(
                int(row_date[2]), int(row_date[1]), int(row_date[0])
                )

            preprocessed_rows.append(preprocessed_row)

        return preprocessed_rows

    def preprocess_header(self, rates, header):
        preprocessed_header = []

        preprocessed_header.append('indice_tiempo')

        for key, value in rates.items():
            preprocessed_header.append(value)

        return preprocessed_header


class BCRAExchangeRateScraper(BCRAScraper):

    url = \
        'http://www.bcra.gov.ar/PublicacionesEstadisticas/Evolucion_moneda.asp'

    coins = {
        "bolivar_venezolano": "Bolívar Venezolano",
        "chelin_austriaco": "Chelín Austríaco",
        "cordoba_nicaraguense": "Cordoba Nicaraguense",
        "corona_checa": "Corona Checa",
        "corona_danesa": "Corona Danesa",
        "corona_noruega": "Corona Noruega",
        "corona_sueca": "Corona Sueca",
        "derecho_especial_de_giro": "Derecho Especial de Giro",
        "dinar_serbia": "Dinar Serbia",
        "dolar_comercial_unico": "Dolar Comercial Unico",
        "dolar_australiano": "Dolar Australiano",
        "dolar_canadiense": "Dolar Canadiense",
        "dolar_de_singapur": "Dolar de Singapur",
        "dolar_estadounidense": "Dolar Estadounidense",
        "dolar_fin_exp_imp_compra": "Dolar Fin.Exp.Imp. Compra",
        "dolar_fin_exp_imp_venta": "Dolar Fin.Exp.Imp. Venta",
        "dolar_finan_esp_compra": "Dolar Finan. Esp. Compra",
        "dolar_finan_esp_venta": "Dolar Finan. Esp. Venta",
        "dolar_financiero_compra": "Dolar Financiero-Compra",
        "dolar_financiero_venta": "Dolar Financiero-Venta",
        "dolar_hong_kong": "Dolar Hong Kong",
        "dolar_libre_compra": "Dolar Libre (Compra)",
        "dolar_libre_venta": "Dolar Libre (Venta)",
        "dolar_neozelandes": "Dolar Neozelandes",
        "dolar_oficial_compra": "Dolar Oficial (Compra)",
        "dolar_oficial_venta": "Dolar Oficial (Venta)",
        "dolar_oficial_tipo_unico": "Dolar Oficial Tipo Unico",
        "dolar_prom_men_1935_69": "Dolar Prom. Men. 1935/69",
        "dolar_referencia_com_3500": "Dolar Referencia Com 3500",
        "dolar_tipo_unico": "Dolar Tipo Unico",
        "dong_vietnam_1000_c_u": "Dong Vietnam (c/1.000 u.)",
        "drachma_griego": "Drachma Griego",
        "ecu": "Ecu",
        "escudo_portugues": "Escudo Portugués",
        "euro": "Euro",
        "florin_antillas_holande": "Florín (Antillas Holande",
        "florin_holandes": "Florín Holandés",
        "franco_belga": "Franco Belga",
        "franco_frances": "Franco Francés",
        "franco_suizo": "Franco Suizo",
        "guarani_paraguayo": "Guaraní Paraguayo",
        "libra_esterlina": "Libra Esterlina",
        "lira_italiana": "Lira Italiana",
        "lira_turca": "Lira Turca",
        "marco_aleman": "Marco Alemán",
        "marco_finlandes": "Marco Finlandés",
        "nuevo_sol_peruano": "Nuevo Sol Peruano",
        "oro_onza_troy": "Oro - Onza Troy",
        "peseta_españa": "Peseta (España)",
        "peso": "Peso",
        "peso_boliviano": "Peso Boliviano",
        "peso_chileno": "Peso Chileno",
        "peso_colombiano": "Peso Colombiano",
        "peso_mexicano": "Peso Mexicano",
        "peso_uruguayo": "Peso Uruguayo",
        "plata_onza_troy": "Plata - Onza Troy",
        "rang_sudafricano": "Rand Sudafricano",
        "real_brasil": "Real (Brasil)",
        "rublo_rusia": "Rublo (Rusia)",
        "rupia_india": "Rupia (India)",
        "shekel_israel": "Shekel (Israel)",
        "sucre_ecuatoriano": "Sucre Ecuatoriano",
        "tipo_de_cambio_especial": "Tipo de Cambio Especial",
        "yen_japon": "Yen (Japón)",
        "yuan_china_cny": "Yuan - China CNY",
        "yuan_china_off_shore_cnh": "Yuan-China Off Shore CNH"
    }

    def __init__(self, *args, **kwargs):
        super(BCRAExchangeRateScraper, self)\
            .__init__(url=self.url, *args, **kwargs)

    def fetch_contents(self, start_date, end_date):
        content = {}
        for k, v in self.coins.items():
            content[k] = self.fetch_content(start_date, v)
        return content

    def fetch_content(self, start_date, coins):
        browser = webdriver.Chrome()
        browser.get(self.url)
        elem = browser.find_element_by_name('Fecha')
        elem.send_keys(start_date.strftime("%d/%m/%Y"))
        coin = browser.find_element_by_name('Moneda')

        coin.send_keys(coins)

        submit_button = browser.find_element_by_class_name('btn-primary')
        submit_button.click()

        content = browser.page_source

        browser.close()
        return content

    def parse_contents(self, content, end_date=datetime.today()):
        parsed_contents = []
        for k, v in content.items():

            parsed = self.parse_coin(v, end_date, k)

            if parsed:
                parsed_contents.extend(parsed)

        return parsed_contents

    def parse_coin(self, content, end_date, coin):
        soup = BeautifulSoup(content, "html.parser")

        table = soup.find('table')
        body = table.find('tbody')

        if not body:
            return []

        rows = body.find_all('tr')
        parsed_contents = []

        for row in rows:
            cols = row.find_all('td')
            parsed = {}

            row_indice_tiempo = \
                datetime.strptime(cols[0].text[5:].strip(), '%d/%m/%Y')

            if row_indice_tiempo <= end_date:
                parsed['moneda'] = coin
                parsed['indice_tiempo'] = cols[0].text[5:].strip()
                parsed['tipo_pase'] = cols[1].text[5:].strip()
                parsed['tipo_cambio'] = cols[2].text[5:].strip()
                parsed_contents.append(parsed)

        return parsed_contents
