from csv import DictWriter
from datetime import date, datetime
from decimal import Decimal
from functools import reduce

from bs4 import BeautifulSoup

import pandas as pd

from bcra_scraper.scraper_base import BCRAScraper


class BCRASMLScraper(BCRAScraper):

    """
    Clase que representa un Scraper para la tasa SML
    del BCRA (Banco Central de la República Argentina).


    Attributes
    ----------
    url : str
        Una cadena que representa una url válida, usada para obtener
        el contenido a ser scrapeado
    coins : Dict
        Diccionario que contiene las monedas que serán utilizadas

    Methods
    -------
    fetch_contents(coins)
        Obtiene los contenidos a ser parseados

    fetch_content(coins)
        Retorna el contenido de la moneda

    parse_contents(contents, start_date, end_date)
        Recibe un iterable de contenidos y devuelve un iterable con la
        información scrapeada

    parse_content(content, coin, start_date, end_date)
        Regresa un iterable con el contenido parseado

    run(start_date, end_date)
        Llama a los métodos que obtienen y scrapean los contenidos
        y los devuelve en un iterable
    """

    def __init__(self, url, coins, *args, **kwargs):
        """
        Parameters
        ----------
        url : str
            Una cadena que representa una url válida, usada para obtener
            el contenido a ser scrapeado. Una URL se considera válida cuando su
            contenido no está vacio.
        coins : Dict
            Diccionario que contiene los nombres de las monedas
        """

        self.coins = coins
        super(BCRASMLScraper, self)\
            .__init__(url, *args, **kwargs)

    def fetch_contents(self, coins):
        """
        Función que a traves de un loop llama a un método
        y regresa un diccionario con el html de cada moneda.

        Parameters
        ----------
        coins : Dict
            Diccionario que contiene las monedas
        """

        contents = {}
        for k, v in self.coins.items():
            contents[k] = self.fetch_content(v)

        return contents

    def fetch_content(self, coins):
        """
        Ingresa al navegador y utiliza la moneda
        regresando el contenido que pertenece a la misma.

        Parameters
        ----------
        coins : String
            String que contiene el nombre de la moneda
        """

        browser_driver = self.get_browser_driver()
        browser_driver.get(self.url)
        field = browser_driver.find_element_by_name('moneda')
        field.send_keys(coins)

        content = browser_driver.page_source

        return content

    def parse_contents(self, contents, start_date, end_date):
        """
        Recorre un iterable que posee los html y llama a un método.
        Retorna una lista de diccionarios con los contenidos parseados

        Parameters
        ----------
        contents : Dict
            String con nombre de cada moneda como clave, string con cada html
            como valor
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """

        parsed_contents = []
        parsed_peso_uruguayo, parsed_real = {}, {}
        parsed_contents = {'peso_uruguayo': [], 'real': []}

        for k, v in contents.items():

            parsed = self.parse_content(v, k, start_date, end_date)

            if parsed:
                for p in parsed:
                    if p['coin'] == 'peso_uruguayo':
                        if p['indice_tiempo'] not in(
                            parsed_peso_uruguayo.keys()
                        ):
                            parsed_peso_uruguayo[p['indice_tiempo']] = {}
                        parsed_peso_uruguayo[p['indice_tiempo']][
                            'Tipo de cambio de Referencia'
                            ] = p['Tipo de cambio de Referencia']
                        parsed_peso_uruguayo[p['indice_tiempo']][
                            'Tipo de cambio URINUSCA'
                            ] = p['Tipo de cambio URINUSCA']
                        parsed_peso_uruguayo[p['indice_tiempo']][
                            'Tipo de cambio SML Peso Uruguayo'
                            ] = p['Tipo de cambio SML Peso Uruguayo']
                        parsed_peso_uruguayo[p['indice_tiempo']][
                            'Tipo de cambio SML Uruguayo Peso'
                            ] = p['Tipo de cambio SML Uruguayo Peso']

                    else:
                        if p['indice_tiempo'] not in parsed_real.keys():
                            parsed_real[p['indice_tiempo']] = {}
                        parsed_real[p['indice_tiempo']][
                            'Tipo de cambio de Referencia'
                            ] = p['Tipo de cambio de Referencia']
                        parsed_real[p['indice_tiempo']][
                            'Tipo de cambio PTAX'
                            ] = p['Tipo de cambio PTAX']
                        parsed_real[p['indice_tiempo']][
                            'Tipo de cambio SML Peso Real'
                            ] = p['Tipo de cambio SML Peso Real']
                        parsed_real[p['indice_tiempo']][
                            'Tipo de cambio SML Real Peso'
                            ] = p['Tipo de cambio SML Real Peso']

        for k, v in parsed_peso_uruguayo.items():

            v['indice_tiempo'] = k
            parsed_contents['peso_uruguayo'].append(v)

        for k, v in parsed_real.items():
            v['indice_tiempo'] = k
            parsed_contents['real'].append(v)

        return parsed_contents

    def parse_content(self, content, coin, start_date, end_date):
        """
        Retorna un iterable con el contenido scrapeado cuyo formato
        posee la moneda, el indice de tiempo, y los tipo de cambio de:
        Referencia, PTAX/URINUSCA (dependiendo la moneda),
        SML de peso a la moneda, SML de la moneda a peso.

        Parameters
        ----------
        content: str
            Html de la moneda
        coin : str
            Nombre de la moneda
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """

        soup = BeautifulSoup(content, "html.parser")

        table = soup.find('table')
        head = table.find('thead')
        body = table.find('tbody')

        head_rows = head.find_all('tr')
        rows = body.find_all('tr')
        parsed_content = []

        for header in head_rows:
            headers = header.find_all('th')
            for row in rows:
                cols = row.find_all('td')
                row_indice_tiempo = \
                    datetime.strptime(cols[0].text, '%d/%m/%Y')

                if (row_indice_tiempo <= end_date and
                        row_indice_tiempo >= start_date):
                    parsed = {}
                    parsed['coin'] = coin
                    parsed['indice_tiempo'] = cols[0].text
                    parsed[headers[1].text] = cols[1].text.strip()
                    parsed[headers[2].text] = cols[2].text.strip()
                    parsed[headers[3].text] = cols[3].text.strip()
                    parsed[headers[4].text] = cols[4].text.strip()
                    parsed_content.append(parsed)

        return parsed_content

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
                elif k == 'moneda':
                    preprocessed_row[k] = row[k]
                else:
                    preprocessed_row[k] = (
                        Decimal((row[k]).replace(',', '.'))
                        if isinstance(row[k], str)
                        else row[k]
                    )

            preprocessed_rows.append(preprocessed_row)

        return preprocessed_rows

    def get_intermediate_panel_data_from_parsed(self, parsed):
        intermediate_panel_data = []

        if parsed:
            for c in self.coins.keys():
                if c == 'peso_uruguayo':
                    types = [
                        'Tipo de cambio de Referencia',
                        'Tipo de cambio URINUSCA',
                        'Tipo de cambio SML Peso Uruguayo',
                        'Tipo de cambio SML Uruguayo Peso',
                    ]
                else:
                    types = [
                        'Tipo de cambio de Referencia',
                        'Tipo de cambio PTAX',
                        'Tipo de cambio SML Peso Real',
                        'Tipo de cambio SML Real Peso',
                    ]

                for r in parsed[c]:
                    for type in types:
                        if type in r.keys():
                            panel_row = {
                                'indice_tiempo': r['indice_tiempo'],
                                'coin': c,
                                'type': type,
                                'value': r[type],
                            }
                            intermediate_panel_data.append(panel_row)
        else:
            return []

        return intermediate_panel_data

    def parse_from_intermediate_panel(self, start_date, end_date):
        parsed = {'peso_uruguayo': [], 'real': []}
        coin_dfs = {}

        intermediate_panel_df = self.read_intermediate_panel_dataframe()
        intermediate_panel_df.set_index(['indice_tiempo'], inplace=True)

        if not intermediate_panel_df.empty:
            coin_dfs = {'peso_uruguayo': {}, 'real': {}}
            for k in self.coins.keys():
                if k == 'peso_uruguayo':
                    for type in [
                        'Tipo de cambio de Referencia',
                        'Tipo de cambio URINUSCA',
                        'Tipo de cambio SML Peso Uruguayo',
                        'Tipo de cambio SML Uruguayo Peso'
                    ]:
                        coin_dfs[k][type] = intermediate_panel_df.loc[
                            (intermediate_panel_df['type'] == type) &
                            (intermediate_panel_df['coin'] == k)
                        ][['value']]
                        coin_dfs[k][type].rename(
                            columns={'value': f'{k}_{type}'}, inplace=True
                        )
                        if coin_dfs[k][type].empty:
                            del(coin_dfs[k][type])
                else:
                    for type in [
                        'Tipo de cambio de Referencia',
                        'Tipo de cambio PTAX',
                        'Tipo de cambio SML Peso Real',
                        'Tipo de cambio SML Real Peso'
                    ]:
                        coin_dfs[k][type] = intermediate_panel_df.loc[
                            (intermediate_panel_df['type'] == type) &
                            (intermediate_panel_df['coin'] == k)
                        ][['value']]
                        coin_dfs[k][type].rename(
                            columns={'value': f'{k}_{type}'}, inplace=True
                        )
                        if coin_dfs[k][type].empty:
                            del(coin_dfs[k][type])

            coins_df = {}
            for type in ['peso_uruguayo', 'real']:
                coins_df[type] = reduce(
                    lambda df1, df2: df1.merge(
                        df2, left_on='indice_tiempo', right_on='indice_tiempo'
                    ),
                    coin_dfs[type].values(),
                )

            for type in ['peso_uruguayo', 'real']:
                for r in coins_df[type].to_records():
                    if (start_date <= r[0] and
                       r[0] <= end_date):
                        parsed_row = {}

                        columns = ['indice_tiempo']
                        columns.extend([v for v in coin_dfs[type].keys()])

                        for index, column in enumerate(columns):
                            parsed_row[column] = r[index]

                        if parsed_row:
                            parsed[type].append(parsed_row)

        return parsed

    def write_intermediate_panel(self, rows):
        header = ['indice_tiempo', 'coin', 'type', 'value']

        with open('.sml-intermediate-panel.csv', 'w') as intermediate_panel:
            writer = DictWriter(intermediate_panel, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    def read_intermediate_panel_dataframe(self):
        intermediate_panel_dataframe = None

        try:
            intermediate_panel_dataframe = pd.read_csv(
                '.sml-intermediate-panel.csv',
                converters={
                    'serie_tiempo': lambda _: _,
                    'coin': lambda _: str(_),
                    'type': lambda _: str(_),
                    'value': lambda _: str(_)
                }
            )

        except FileNotFoundError:
            # TODO: fix me
            pass

        return intermediate_panel_dataframe

    def save_intermediate_panel(self, parsed):
        intermediate_panel_data = self.get_intermediate_panel_data_from_parsed(
            parsed
        )
        self.write_intermediate_panel(intermediate_panel_data)

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

        if self.use_intermediate_panel:
            first_date = start_date.strftime("%Y-%m-%d")
            last_date = end_date.strftime("%Y-%m-%d")
            parsed = self.parse_from_intermediate_panel(first_date, last_date)

            parsed['peso_uruguayo'] = self.preprocess_rows(
                parsed['peso_uruguayo']
                )
            parsed['real'] = self.preprocess_rows(parsed['real'])

        else:
            contents = self.fetch_contents(self.coins)
            parsed = self.parse_contents(contents, start_date, end_date)

            parsed['peso_uruguayo'] = self.preprocess_rows(
                parsed['peso_uruguayo']
                )
            parsed['real'] = self.preprocess_rows(parsed['real'])

            self.save_intermediate_panel(parsed)

        return parsed
