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
        Devuelve una lista de diccionarios para cada moneda
        en cada fecha con el html correspondiente.

    fetch_content(single_date, coin)
        Regresa un string  con el contenido que pertenece a la moneda.

    parse_contents(contents, start_date, end_date)
        Retorna un diccionario que tiene como clave cada moneda
        y como valor una lista con un diccionario que tiene los
        contenidos parseados.

    parse_content(content, start_date, end_date, coin)
        Retorna un iterable con un diccionario.

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
                for k in coins.keys():
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
        """
        Recorre parsed y por cada registro genera un diccionario
        obteniendo por separado las claves que se utilizaran como headers,
        y sus valores.

        Parameters
        ----------
        parsed : lista de diccionarios por moneda
        """
        intermediate_panel_data = []

        parsed_contents = {'dolar': [], 'euro': []}

        for p in parsed:
            for k, v in p.items():
                if k == 'indice_tiempo':
                    time = p['indice_tiempo']
                else:
                    result = k.split("_")
                    if result[2] == 'dolar':
                        panel = {}
                        panel['indice_tiempo'] = time
                        panel['coin'] = result[2]
                        panel['entity'] = result[3]
                        panel['channel'] = result[4]
                        panel['flow'] = result[5]
                        panel['hour'] = result[6]
                        panel['value'] = v
                        parsed_contents['dolar'].append(panel)
                    elif result[2] == 'euro':
                        panel = {}
                        panel['indice_tiempo'] = time
                        panel['coin'] = result[2]
                        panel['entity'] = result[3]
                        panel['channel'] = result[4]
                        panel['flow'] = result[5]
                        panel['hour'] = result[6]
                        panel['value'] = v
                        parsed_contents['euro'].append(panel)
        intermediate_panel_data.extend(
            parsed_contents['dolar'] + parsed_contents['euro']
        )
        return intermediate_panel_data

    def parse_from_intermediate_panel(self, start_date, end_date):
        """
        Lee el dataframe del panel intermedio.
        Unifica los valores de coin, entity, channel, flow, hour,
        convirtiendolos en clave y como valor se asigna el dato
        de la clave value.
        Regresa un diccionario con las monedas como claves, y como valor
        una lista con un diccionario que contiene la fecha y los registros.

        Parameters
        ----------
        start_date : date
            Fecha de inicio que toma como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """
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
                                for k in self.coins.keys():
                                    type =\
                                        (
                                            f'tc_ars_{k}_{entity}_{channel}_'
                                            f'{flow}_{hour}hs'
                                        )
                                    coin_dfs[k][type] =\
                                        intermediate_panel_df.loc[
                                        (intermediate_panel_df[
                                            'coin'] == k) &
                                        (intermediate_panel_df[
                                            'entity'] == entity) &
                                        (intermediate_panel_df[
                                            'channel'] == channel) &
                                        (intermediate_panel_df[
                                            'flow'] == flow) &
                                        (intermediate_panel_df[
                                            'hour'] == f'{hour}hs')
                                    ][['value']]

                                    coin_dfs[k][type].rename(
                                        columns={'value': f'{type}'},
                                        inplace=True
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
        """
        Escribe el panel intermedio.

        Parameters
        ----------
        rows: Iterable
        """
        header = [
            'indice_tiempo',
            'coin',
            'entity',
            'channel',
            'flow',
            'hour',
            'value'
        ]

        with open('.tce-intermediate-panel.csv', 'w') as intermediate_panel:
            writer = DictWriter(intermediate_panel, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    def read_intermediate_panel_dataframe(self):
        """
        Lee el dataframe
        """
        intermediate_panel_dataframe = None

        try:
            intermediate_panel_dataframe = pd.read_csv(
                '.tce-intermediate-panel.csv',
                converters={
                    'serie_tiempo': lambda _: _,
                    'coin': lambda _: str(_),
                    'value': lambda _: str(_)
                }
            )

        except FileNotFoundError:
            raise InvalidConfigurationError(
                "El archivo panel no existe"
            )
        return intermediate_panel_dataframe

    def save_intermediate_panel(self, parsed):
        """
        Llama a un método para obtener la data del panel intermedio
        y a otro método pasandole esa data para que la escriba.

        Parameters
        ----------
        parsed: Iterable
        """
        intermediate_panel_data = self.get_intermediate_panel_data_from_parsed(
            parsed
        )
        self.write_intermediate_panel(intermediate_panel_data)

    def parse_contents(self, contents, start_date, end_date, entities):
        """
        Retorna un diccionario que tiene como clave cada moneda
        y como valor una lista con un diccionario que tiene los
        contenidos parseados.

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

                if parsed:
                    parsed_contents[k].extend(parsed)
        return parsed_contents

    def parse_content(self, content, start_date, end_date, coin, entities):
        """
        Parsea el contenido y agrega los registros a un diccionario,
        retornando un iterable con el diccionario.

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

        result = {}

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
                            parsed[
                                'indice_tiempo'
                                ] = header[0].text[27:].strip()
                            parsed[
                                f'tc_ars_{coin}_{k}_mostrador_compra_11hs'
                                ] =\
                                (cols[1].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_mostrador_compra_13hs'
                                ] =\
                                (cols[5].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_mostrador_compra_15hs'
                                ] =\
                                (cols[9].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_electronico_compra_11hs'
                                ] =\
                                (cols[3].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_electronico_compra_13hs'
                                ] =\
                                (cols[7].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_electronico_compra_15hs'
                                ] =\
                                (cols[11].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_mostrador_venta_11hs'
                                ] =\
                                (cols[2].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_mostrador_venta_13hs'
                                ] =\
                                (cols[6].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_mostrador_venta_15hs'
                                ] =\
                                (cols[10].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_electronico_venta_11hs'
                                ] =\
                                (cols[4].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_electronico_venta_13hs'
                                ] =\
                                (cols[8].text.strip() or '0.0').replace(
                                    ',', '.')
                            parsed[
                                f'tc_ars_{coin}_{k}_electronico_venta_15hs'
                                ] =\
                                (cols[12].text.strip() or '0.0').replace(
                                    ',', '.')

                            result.update(parsed)

            parsed_contents.append(result)
            return parsed_contents

        except InvalidConfigurationError:
            raise('Error en el content a scrapear')

    def preprocess_rows(self, rows):
        """
        Regresa un iterable donde la fecha y los valores son parseados.

        Parameters
        ----------
        rows : list
        """
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
        Inicializa un iterable. Llama a los métodos para obtener y scrapear
        los contenidos, y los ingresa en el iterable.
        Retorna un diccionario que tiene como clave cada moneda
        y como valor una lista con un diccionario que tiene los
        contenidos parseados.

        Parameters
        ----------
        start_date: date
            fecha de inicio que toma como referencia el scraper

        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """
        parsed = {}

        if self.use_intermediate_panel:
            first_date = start_date.strftime("%Y-%m-%d")
            last_date = end_date.strftime("%Y-%m-%d")

            parsed = self.parse_from_intermediate_panel(first_date, last_date)

            parsed['dolar'] = self.preprocess_rows(
                parsed['dolar']
                )
            parsed['euro'] = self.preprocess_rows(parsed['euro'])

        else:
            contents = self.fetch_contents(start_date, end_date, self.coins)
            parsed = self.parse_contents(
                contents, start_date, end_date, self.entities,
            )

            parsed['dolar'] = self.preprocess_rows(
                parsed['dolar']
                )
            parsed['euro'] = self.preprocess_rows(parsed['euro'])

            _parsed = (
                [p for p in parsed['dolar']] + [p for p in parsed['euro']]
            )
            self.save_intermediate_panel(_parsed)

        return parsed
