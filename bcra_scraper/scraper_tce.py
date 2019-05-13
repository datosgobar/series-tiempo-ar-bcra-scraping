from csv import DictWriter
from datetime import date, datetime, timedelta
from decimal import Decimal

from bs4 import BeautifulSoup

from bcra_scraper.exceptions import InvalidConfigurationError
from bcra_scraper.scraper_base import BCRAScraper


class BCRATCEScraper(BCRAScraper):

    """
    Clase que representa un Scraper para el tipo de cambio de entidades
    bancarias del BCRA (Banco Central de la República Argentina).

    Attributes
    ----------
    url : str
        Una cadena que representa una url válida, usada para obtener
        el contenido a ser scrapeado
    coins : Dict
        Diccionario que contiene las monedas que serán utilizadas
    entities : Dict
        Diccionario que contiene el nombre de los bancos

    Methods
    -------
    fetch_contents(start_date, end_date, coins)
        Devuelve una lista de diccionarios por cada moneda
        en cada fecha con el html correspondiente.

    fetch_content(single_date, coin)
        Retorna el contenido de la moneda

    parse_contents(contents, start_date, end_date)
        Recibe un iterable de contenidos y devuelve un iterable con la
        información scrapeada

    parse_content(content, start_date, end_date, coin)
        Retorna el contenido scrapeado

    run(start_date, end_date)
        Llama a los métodos que obtienen y scrapean los contenidos
        y los devuelve en un iterable
    """

    def __init__(self, url, coins, entities, *args, **kwargs):
        """
        Parameters
        ----------
        url : str
            Una cadena que representa una url válida, usada para obtener
            el contenido a ser scrapeado. Una URL se considera válida cuando su
            contenido no está vacio.
        coins : Dict
            Diccionario que contiene los nombres de las monedas
        entities : Dict
            Diccionario que contiene el nombre de los bancos
        """
        self.coins = coins
        self.entities = entities
        super(BCRATCEScraper, self)\
            .__init__(url, *args, **kwargs)

    def fetch_contents(self, start_date, end_date, coins):
        """
        Recorre rango de fechas y verifica que la fecha corresponda
        a un día habil. Devuelve una lista de diccionarios para cada moneda
        en cada fecha con el html correspondiente.

        Parameters
        ----------
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date: date
            fecha de fin que va a tomar como referencia el scraper
        coins : Dict
            Diccionario que contiene los nombres de las monedas
        """

        contents = []

        day_count = (end_date - start_date).days + 1

        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):
            if date.weekday(single_date) in [0, 1, 2, 3, 4]:
                for k, v in coins.items():
                    content = {}
                    content[k] = self.fetch_content(single_date, k)
                    contents.append(content)
        return contents

    def fetch_content(self, single_date, coins):
        """
        Ingresa al navegador y utiliza la moneda
        regresando el contenido que pertenece a la misma.

        Parameters
        ----------
        single_date : date
            Fecha de inicio que toma como referencia el scraper
        coins : String
            String que contiene el nombre de la moneda
        """

        browser_driver = self.get_browser_driver()
        browser_driver.get(self.url)
        coin = browser_driver.find_element_by_name('moneda')
        coin.send_keys(coins)
        browser_driver.execute_script(
            'document.getElementsByName("fecha")\
            [0].removeAttribute("readonly")'
        )
        elem = browser_driver.find_element_by_name('fecha')
        elem.send_keys(single_date.strftime("%d/%m/%Y"))

        submit_button = browser_driver.find_element_by_class_name(
            'btn-primary'
        )
        submit_button.click()

        content = browser_driver.page_source

        return content

    def write_intermediate_panel(self, rows):
        header = ['indice_tiempo', 'coin', 'type', 'value']

        with open('.tce-intermediate-panel.csv', 'w') as intermediate_panel:
            writer = DictWriter(intermediate_panel, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    def save_intermediate_panel(self, parsed):
        intermediate_panel_data = parsed

        self.write_intermediate_panel(intermediate_panel_data)

    def parse_contents(self, contents, start_date, end_date, entities):
        """
        Recorre un iterable que posee los html y llama a un método.
        Retorna una lista de diccionarios con los contenidos parseados

        Parameters
        ----------
        contents: Iterable
            Lista de diccionarios en la que cada diccionario tiene:
            string con nombre de cada moneda como clave, string con cada html
            como valor
        start_date : date
            Fecha de inicio que toma como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        entities : Dict
            Diccionario que contiene el nombre de los bancos
        """
        parsed_contents = []
        for content in contents:
            for k, v in content.items():
                parsed = self.parse_content(
                    v, start_date, end_date, k, entities
                )

                if parsed:
                    parsed_contents.extend(parsed)

        return parsed_contents

    def parse_content(self, content, start_date, end_date, coin, entities):
        """
        Retorna un iterable con el contenido scrapeado cuyo formato
        posee el indice de tiempo, las monedas y sus diferentes entidades

        Parameters
        ----------
        content: str
            Html de la moneda
        start_date : date
            Fecha de inicio que toma como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        coin : str
            Nombre de la moneda
        entities : Dict
            Diccionario que contiene el nombre de los bancos
        """
        soup = BeautifulSoup(content, "html.parser")

        table = soup.find(
            class_='table table-BCRA table-bordered table-hover ' +
                   'table-responsive'
        )

        if not table:
            return []

        head = table.find('thead')

        if not head:
            return []

        body = table.find('tbody')

        if not body:
            return []

        header = head.find_all('tr')
        rows = body.find_all('tr')

        parsed_contents = []

        try:
            for k, v in entities.items():
                for row in rows:
                    cols = row.find_all('td')
                    row_indice_tiempo = \
                        datetime.strptime(
                            header[0].text[27:].strip(), '%d/%m/%Y'
                        )
                    parsed = {}
                    if (start_date <= row_indice_tiempo and
                            row_indice_tiempo <= end_date):
                        if cols[0].text.strip() == v:
                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_mostrador_compra_11hs'
                            parsed['value'] = cols[1].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_mostrador_compra_13hs'
                            parsed['value'] = cols[5].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_mostrador_compra_15hs'
                            parsed['value'] = cols[9].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_electronico_compra_11hs'
                            parsed['value'] = cols[3].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_electronico_compra_13hs'
                            parsed['value'] = cols[7].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_electronico_compra_15hs'
                            parsed['value'] = cols[11].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_mostrador_venta_11hs'
                            parsed['value'] = cols[2].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_mostrador_venta_13hs'
                            parsed['value'] = cols[6].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_mostrador_venta_15hs'
                            parsed['value'] = cols[10].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_electronico_venta_11hs'
                            parsed['value'] = cols[4].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_electronico_venta_13hs'
                            parsed['value'] = cols[8].text.strip()
                            parsed_contents.append(parsed)

                            parsed = {}
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] =\
                                header[0].text[27:].strip()
                            parsed['type'] = f'{k}_electronico_venta_15hs'
                            parsed['value'] = cols[12].text.strip()
                            parsed_contents.append(parsed)

            return parsed_contents
        except InvalidConfigurationError:
            raise('Error en el content a scrapear')

    def preprocess_rows(self, rows):
        preprocessed_rows = []

        for row in rows:
            preprocessed_row = {}

            for k in row.keys():
                if k == 'indice_tiempo':
                    if '/' in row[k]:
                        _ = row[k].split('/')
                        preprocessed_date = date.fromisoformat(
                            '-'.join([_[2], _[1], _[0]])
                        )
                    else:
                        preprocessed_date = date.fromisoformat(row[k])
                    preprocessed_row['indice_tiempo'] = preprocessed_date
                elif k == 'coin':
                    preprocessed_row[k] = row[k]
                elif k == 'value':
                    row[k] = row[k] if row[k] else '0.0'
                    preprocessed_row[k] = Decimal(row[k].replace(',', '.'))
                else:
                    preprocessed_row[k] = row[k]

            preprocessed_rows.append(preprocessed_row)

        return preprocessed_rows

    def run(self, start_date, end_date):
        """
        Inicializa una lista. Llama a los métodos para obtener y scrapear
        los contenidos, y los ingresa en la lista.
        Retorna una lista de diccionarios con los resultados scrapeados

        Parameters
        ----------
        start_date: date
            fecha de inicio que toma como referencia el scraper

        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """
        parsed = []

        contents = self.fetch_contents(start_date, end_date, self.coins)
        parsed = self.parse_contents(
            contents, start_date, end_date, self.entities,
        )

        parsed = self.preprocess_rows(parsed)

        self.save_intermediate_panel(parsed)

        return parsed
