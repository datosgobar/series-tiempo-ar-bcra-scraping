from csv import DictWriter
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import reduce

from bs4 import BeautifulSoup
from pandas import pandas as pd

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

    def get_intermediate_panel_data_from_parsed(self, parsed):
        intermediate_panel_data = []

        for p in parsed:
            newd = dict.fromkeys(p)
            newd.pop('coin')
            newd.pop('indice_tiempo')
            coin = p.get('coin')
            indice_tiempo = p.get('indice_tiempo')

            for k in newd.keys():
                row = {}
                row['indice_tiempo'] = indice_tiempo
                row['coin'] = coin
                row['type'] = k
                row['value'] = p[k]

                intermediate_panel_data.append(row)

        return intermediate_panel_data

    def parse_from_intermediate_panel(self, start_date, end_date):
        parsed = {'dolar': [], 'euro': []}
        coin_dfs = {}

        intermediate_panel_df = self.read_intermediate_panel_dataframe()
        intermediate_panel_df.set_index(['indice_tiempo'], inplace=True)

        if not intermediate_panel_df.empty:
            coin_dfs = {'dolar': {}, 'euro': {}}

            for coin in ['dolar', 'euro']:
                for entity in self.entities:
                    for channel in ['mostrador', 'electronico']:
                        for flow in ['compra', 'venta']:
                            for hour in [11, 13, 15]:
                                type = f'tc_ars_{coin}_{entity}_{channel}_{flow}_{hour}hs'

                                for k in self.coins.keys():
                                    coin_dfs[k][type] = intermediate_panel_df.loc[
                                        (intermediate_panel_df['type'] == type) &
                                        (intermediate_panel_df['coin'] == k)
                                    ][['value']]
                                    coin_dfs[k][type].rename(
                                        columns={'value': f'{type}'}, inplace=True
                                    )
                                    if coin_dfs[k][type].empty:
                                        del(coin_dfs[k][type])

            coins_df = {}
            for coin in ['dolar', 'euro']:
                coins_df[coin] = reduce(
                    lambda df1, df2: df1.merge(
                        df2, left_on='indice_tiempo', right_on='indice_tiempo'
                    ),
                    coin_dfs[coin].values(),
                )

            for coin in ['dolar', 'euro']:
                for r in coins_df[coin].to_records():
                    if (start_date <= r[0] and
                       r[0] <= end_date):
                        parsed_row = {}

                        columns = ['indice_tiempo']
                        columns.extend([v for v in coin_dfs[coin].keys()])

                        for index, column in enumerate(columns):
                            parsed_row[column] = r[index]

                        if parsed_row:
                            parsed[coin].append(parsed_row)

        return parsed

    def write_intermediate_panel(self, rows):
        header = ['indice_tiempo', 'coin', 'type', 'value']

        with open('.tce-intermediate-panel.csv', 'w') as intermediate_panel:
            writer = DictWriter(intermediate_panel, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    def read_intermediate_panel_dataframe(self):
        intermediate_panel_dataframe = None

        try:
            intermediate_panel_dataframe = pd.read_csv(
                '.tce-intermediate-panel.csv',
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
        parsed_contents = {'dolar': [], 'euro': []}
        for content in contents:
            for k, v in content.items():
                parsed = self.parse_content(
                    v, start_date, end_date, k, entities
                )
                # kpoint()
                if parsed:
                    # for p in parsed:
                    parsed_contents[k].extend(parsed)
        # parsed_dolar, parsed_euro = {}, {}
        # parsed_contents = {'dolar': [], 'euro': []}

        # for content in contents:
        #     for k, v in content.items():

        #         parsed = self.parse_content(v, start_date, end_date, k, entities)
        #         breakpoint()
        #         if parsed:
        #             for p in parsed:
        #                 if p['coin'] == 'dolar':
        #                     if p['indice_tiempo'] not in(
        #                         parsed_dolar.keys()
        #                     ):
                                

        #                 else:
        #                     if p['indice_tiempo'] not in parsed_euro.keys():
                                

        # for k, v in parsed_dolar.items():

        #     v['indice_tiempo'] = k
        #     parsed_contents['peso_uruguayo'].append(v)

        # for k, v in parsed_euro.items():
        #     v['indice_tiempo'] = k
        #     parsed_contents['real'].append(v)

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
                            parsed['coin'] = coin
                            parsed['indice_tiempo'] = header[0].text[27:].strip()
                            parsed[f'tc_ars_{coin}_{k}_mostrador_compra_11hs'] =\
                                Decimal((cols[1].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_mostrador_compra_13hs'] =\
                                Decimal((cols[5].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_mostrador_compra_15hs'] =\
                                Decimal((cols[9].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_electronico_compra_11hs'] =\
                                Decimal((cols[3].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_electronico_compra_13hs'] =\
                                Decimal((cols[7].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_electronico_compra_15hs'] =\
                                Decimal((cols[11].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_mostrador_venta_11hs'] =\
                                Decimal((cols[2].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_mostrador_venta_13hs'] =\
                                Decimal((cols[6].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_mostrador_venta_15hs'] =\
                                Decimal((cols[10].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_electronico_venta_11hs'] =\
                                Decimal((cols[4].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_electronico_venta_13hs'] =\
                                Decimal((cols[8].text.strip() or '0.0').replace(',', '.'))
                            parsed[f'tc_ars_{coin}_{k}_electronico_venta_15hs'] =\
                                Decimal((cols[12].text.strip() or '0.0').replace(',', '.'))

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
                # elif 'tc_ars' in k:
                #     row[k] = row[k] if row[k] else '0.0'
                #     preprocessed_row[k] = Decimal(row[k].replace(',', '.'))
                else:
                    preprocessed_row[k] = row[k]

            preprocessed_rows.append(preprocessed_row)

        # breakpoint()
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
        parsed = {}

        if self.use_intermediate_panel:
            first_date = start_date.strftime("%d/%m/%Y")
            last_date = end_date.strftime("%d/%m/%Y")

            parsed = self.parse_from_intermediate_panel(first_date, last_date)
            # breakpoint()
            parsed['dolar'] = self.preprocess_rows(
                parsed['dolar']
                )
            parsed['euro'] = self.preprocess_rows(parsed['euro'])

        else:
            contents = self.fetch_contents(start_date, end_date, self.coins)
            parsed = self.parse_contents(
                contents, start_date, end_date, self.entities,
            )
            # breakpoint()


            # parsed['dolar'] = self.preprocess_rows(
            #     parsed['dolar']
            #     )
            # parsed['euro'] = self.preprocess_rows(parsed['euro'])

            _parsed = [p for p in parsed['dolar']] + [p for p in parsed['euro']]
            self.save_intermediate_panel(_parsed)

        return parsed
