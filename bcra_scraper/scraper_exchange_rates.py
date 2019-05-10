from csv import DictWriter
from datetime import date, datetime
from decimal import Decimal
from functools import reduce

from bs4 import BeautifulSoup
import pandas as pd

from bcra_scraper.scraper_base import BCRAScraper


class BCRAExchangeRateScraper(BCRAScraper):
    """
    Clase que representa un Scraper para los tipos de cambio y tipos de pase
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
    fetch_contents(start_date, end_date)
        Obtiene los contenidos a ser parseados

    fetch_content(start_date, coins)
        Retorna el contenido de la moneda

    parse_contents(start_date, end_date)
        Recibe un iterable de contenidos y devuelve un iterable con la
        información scrapeada

    parse_coin(content, end_date, coin)
        Retorna el contenido scrapeado

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
            Diccionario que contiene los plazos en días de la tasa Libor
        """
        self.coins = coins
        super(BCRAExchangeRateScraper, self)\
            .__init__(url, *args, **kwargs)

    def fetch_contents(self, start_date, end_date):
        """
        A través de un loop llama a un método.
        Retorna un diccionario en donde las claves son las monedas y
        los valores son los html correspondientes a cada una

        Parameters
        ----------
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper

        """

        content = {}
        for k, v in self.coins.items():
            content[k] = self.fetch_content(start_date, v)

        return content

    def fetch_content(self, start_date, coins):
        """
        Ingresa al navegador utilizando la fecha y la moneda que recibe.
        La fecha por default es today, y en caso de pasarle otra fecha
        va a traer el contenido desde esa fecha hasta today.
        Retorna un string que contiene el html obtenido.

        Parameters
        ----------
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper

        coins: str
            Nombre de cada moneda
        """

        browser_driver = self.get_browser_driver()
        browser_driver.get(self.url)
        elem = browser_driver.find_element_by_name('Fecha')
        elem.send_keys(start_date.strftime("%d/%m/%Y"))
        coin = browser_driver.find_element_by_name('Moneda')

        coin.send_keys(coins)

        submit_button = browser_driver.find_element_by_class_name(
            'btn-primary'
        )
        submit_button.click()

        content = browser_driver.page_source

        return content

    def parse_contents(self, content, start_date, end_date):
        """
        Recorre un iterable que posee los html y llama a un método.
        Retorna una lista de diccionarios con los contenidos parseados

        Parameters
        ----------
        contents: Dict
            String con nombre de cada moneda como clave, string con cada html
            como valor

        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """
        parsed_contents = []
        parsed_tc_local, parsed_tp_usd = {}, {}
        parsed_contents = {'tc_local': [], 'tp_usd': []}

        for k, v in content.items():

            parsed = self.parse_coin(v, start_date, end_date, k)

            if parsed:
                for p in parsed:
                    if p['indice_tiempo'] not in parsed_tc_local.keys():
                        parsed_tc_local[p['indice_tiempo']] = {}
                    parsed_tc_local[p['indice_tiempo']][p['moneda']] =\
                        p['tc_local']
                    if p['indice_tiempo'] not in parsed_tp_usd.keys():
                        parsed_tp_usd[p['indice_tiempo']] = {}
                    parsed_tp_usd[p['indice_tiempo']][p['moneda']] =\
                        p['tp_usd']

        for k, v in parsed_tc_local.items():
            v['indice_tiempo'] = k
            parsed_contents['tc_local'].append(v)

        for k, v in parsed_tp_usd.items():
            v['indice_tiempo'] = k
            parsed_contents['tp_usd'].append(v)

        return parsed_contents

    def parse_coin(self, content, start_date, end_date, coin):
        """
        Retorna un iterable con el contenido scrapeado cuyo formato
        posee el indice de tiempo y los tipos de pase y cambio de cada moneda

        Parameters
        ----------
        content: str
            Html de la moneda

        end_date : date
            fecha de fin que va a tomar como referencia el scraper

        coin : str
            Nombre de la moneda
        """

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
                datetime.strptime(cols[0].text.strip(), '%d/%m/%Y')

            if (start_date <= row_indice_tiempo and
                    row_indice_tiempo <= end_date):
                parsed['moneda'] = coin
                parsed['indice_tiempo'] = cols[0].text.strip()
                parsed['tp_usd'] = cols[1].text[5:].strip()
                parsed['tc_local'] = cols[2].text[5:].strip()
                parsed_contents.append(parsed)

        return parsed_contents

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

    def write_intermediate_panel(self, rows):
        header = ['indice_tiempo', 'coin', 'type', 'value']
        file_name = '.exchange-rates-intermediate-panel.csv'

        with open(file_name, 'w') as intermediate_panel:
            writer = DictWriter(intermediate_panel, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    def get_intermediate_panel_data_from_parsed(self, parsed):
        intermediate_panel_data = []
        if parsed:
            for type in ['tc_local', 'tp_usd']:
                for r in parsed[type]:
                    for c in self.coins.keys():
                        if c in r.keys():
                            panel_row = {
                                'indice_tiempo': r['indice_tiempo'],
                                'coin': c,
                                'type': type,
                                'value': r[c],
                            }

                            intermediate_panel_data.append(panel_row)
        else:
            return []
        return intermediate_panel_data

    def save_intermediate_panel(self, parsed):
        intermediate_panel_data = self.get_intermediate_panel_data_from_parsed(
            parsed
        )
        self.write_intermediate_panel(intermediate_panel_data)

    def parse_from_intermediate_panel(self, start_date, end_date):
        parsed = {'tc_local': [], 'tp_usd': []}
        coin_dfs = {}

        intermediate_panel_df = self.read_intermediate_panel_dataframe()
        intermediate_panel_df.set_index(['indice_tiempo'], inplace=True)

        if not intermediate_panel_df.empty:
            coin_dfs = {'tc_local': {}, 'tp_usd': {}}
            for k in self.coins.keys():
                for type in ['tc_local', 'tp_usd']:
                    coin_dfs[type][k] = intermediate_panel_df.loc[
                        (intermediate_panel_df['type'] == type) &
                        (intermediate_panel_df['coin'] == k)
                    ][['value']]
                    coin_dfs[type][k].rename(
                        columns={'value': f'{k}_{type}'}, inplace=True
                    )
                    if coin_dfs[type][k].empty:
                        del(coin_dfs[type][k])

            coins_df = {}
            for type in ['tc_local', 'tp_usd']:
                coins_df[type] = reduce(
                    lambda df1, df2: df1.merge(
                        df2, left_on='indice_tiempo', right_on='indice_tiempo'
                    ),
                    coin_dfs[type].values(),
                )

            for type in ['tc_local', 'tp_usd']:
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

    def read_intermediate_panel_dataframe(self):
        intermediate_panel_dataframe = None

        try:
            intermediate_panel_dataframe = pd.read_csv(
                '.exchange-rates-intermediate-panel.csv',
                converters={
                    'serie_tiempo': lambda _: _,
                    'coin': lambda _: str(_),
                    'type': lambda _: str(_),
                    'value': lambda _: Decimal(_)
                }
            )

        except FileNotFoundError:
            # TODO: fix me
            pass

        return intermediate_panel_dataframe

    def run(self, start_date, end_date):
        """
        Inicializa una lista. Llama a los métodos para obtener y scrapear
        los contenidos, y los ingresa en la lista.
        Llama a un método para guardar el archivo intermedio.
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

            parsed['tc_local'] = self.preprocess_rows(parsed['tc_local'])
            parsed['tp_usd'] = self.preprocess_rows(parsed['tp_usd'])

        else:
            contents = self.fetch_contents(start_date, end_date)
            parsed = self.parse_contents(contents, start_date, end_date)

            parsed['tc_local'] = self.preprocess_rows(parsed['tc_local'])
            parsed['tp_usd'] = self.preprocess_rows(parsed['tp_usd'])

            self.save_intermediate_panel(parsed)

        return parsed
