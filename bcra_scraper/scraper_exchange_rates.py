from csv import DictWriter
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import reduce
import logging
import re

from bs4 import BeautifulSoup
import pandas as pd

from bcra_scraper.scraper_base import BCRAScraper
from bcra_scraper.exceptions import InvalidConfigurationError
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


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

    def __init__(self, url, coins, intermediate_panel_path, *args, **kwargs):
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
        self.intermediate_panel_path = intermediate_panel_path
        super(BCRAExchangeRateScraper, self)\
            .__init__(url, *args, **kwargs)

    def fetch_contents(self, start_date, end_date, intermediate_panel_data):
        """
        A través de un loop llama a un método.
        Retorna un diccionario en donde las claves son las monedas y
        los valores son los html correspondientes a cada una

        Parameters
        ----------
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """
        content = {}
        day_count = (end_date - start_date).days + 1

        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):

            if not self.intermediate_panel_data_has_date(intermediate_panel_data, single_date):
                for k, v in self.coins.items():
                    fetched = self.fetch_content(start_date, v)
                    if fetched:
                        content[k] = fetched
        return content

    def intermediate_panel_data_has_date(self, intermediate_panel_data, single_date):
        _content = {}
        if intermediate_panel_data:
            for k, v in intermediate_panel_data.items():
                for d in v:
                    if single_date.strftime("%Y-%m-%d") == d['indice_tiempo'].strftime("%Y-%m-%d"):
                        _content[k] = d
        return _content

    def validate_coin_in_configuration_file(self, coin, options):
        """
        Valida que el valor de la moneda en el archivo de configuración
        se corresponda con los valores de las opciones del select en la página
        """
        select_options = [select_option.text for select_option in options]
        if coin in select_options:
            return True
        else:
            return False

    def fetch_content(self, start_date, coin):
        """
        Ingresa al navegador utilizando la fecha y la moneda que recibe.
        La fecha por default es hoy, en caso de pasarle otra fecha
        va a traer el contenido desde esa fecha hasta hoy.
        Retorna un string que contiene el html obtenido.

        Parameters
        ----------
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper

        coin: str
            Nombre de cada moneda
        """
        content = ''
        counter = 1
        tries = self.tries

        while counter <= tries:
            try:
                browser_driver = self.get_browser_driver()
                browser_driver.get(self.url)
                element_present = EC.presence_of_element_located(
                    (By.NAME, 'Fecha')
                )
                elem = WebDriverWait(browser_driver, 0).until(element_present)

                elem.send_keys(start_date.strftime("%d/%m/%Y"))
                element = browser_driver.find_element_by_name('Moneda')
                options = element.find_elements_by_tag_name('option')

                valid = self.validate_coin_in_configuration_file(coin, options)
                if valid:
                    element.send_keys(coin)
                    submit_button = browser_driver.find_element_by_class_name(
                        'btn-primary')
                    submit_button.click()
                    content = browser_driver.page_source

            except TimeoutException:
                if counter < tries:
                    logging.warning(
                        f'La conexion de internet ha fallado para la fecha {start_date}. Reintentando...'
                    )
                    counter = counter + 1
                else:
                    logging.warning(
                        f'La conexion de internet ha fallado para la fecha {start_date}'
                    )
                    raise InvalidConfigurationError(
                        f'La conexion de internet ha fallado para la fecha {start_date}'
                    )
            except NoSuchElementException:
                raise InvalidConfigurationError(
                    f'La conexion de internet ha fallado para la fecha {start_date}'
                )

            break

        return content

    def parse_contents(self, content, start_date, end_date, intermediate_panel_data):
        """
        Recorre un iterable que posee los html y llama a un método.
        Retorna una lista de diccionarios con los contenidos parseados

        Parameters
        ----------
        content: Dict
            String con nombre de cada moneda como clave, string con cada html
            como valor
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """
        parsed_contents = []
        parsed_tc_local, parsed_tp_usd = {}, {}
        parsed_contents = {'tc_local': [], 'tp_usd': []}
        day_count = (end_date - start_date).days + 1

        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):
            if not self.intermediate_panel_data_has_date(intermediate_panel_data, single_date):
                for k, v in content.items():
                    parsed = self.parse_coin(v, single_date, k)
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
            else:
                parsed = self.intermediate_panel_data_has_date(intermediate_panel_data, single_date)
                parsed_contents['tc_local'].append(parsed['tc_local'])
                parsed_contents['tp_usd'].append(parsed['tp_usd'])

        for k, v in parsed_tc_local.items():
            preprocess_dict = {}
            v['indice_tiempo'] = k
            preprocess_dict = self.preprocess_rows([v])
            for p in preprocess_dict:
                parsed_contents['tc_local'].append(p)
                if not type(intermediate_panel_data) == list:
                    intermediate_panel_data['tc_local'].append(p)

        for k, v in parsed_tp_usd.items():
            preprocess_dict = {}
            v['indice_tiempo'] = k
            preprocess_dict = self.preprocess_rows([v])
            for p in preprocess_dict:
                parsed_contents['tp_usd'].append(p)
                if not type(intermediate_panel_data) == list:
                    intermediate_panel_data['tp_usd'].append(p)

        return parsed_contents, intermediate_panel_data

    def parse_coin(self, content, single_date, coin):
        """
        Retorna un iterable con el contenido scrapeado cuyo formato
        posee el indice de tiempo y los tipos de pase y cambio de cada moneda

        Parameters
        ----------
        content: str
            Html de la moneda
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        coin : str
            Nombre de la moneda
        """

        soup = BeautifulSoup(content, "html.parser")
        try:
            table = soup.find('table')

            if not table:
                return []

            head = table.find('thead')

            if not head:
                return []

            body = table.find('tbody')

            if not body:
                return []

            parsed_contents = []

            day = single_date.strftime("%d/%m/%Y")
            parsed = {}
            parsed['moneda'] = coin
            parsed['indice_tiempo'] = day
            parsed['tp_usd'] = ''
            parsed['tc_local'] = ''
            
            if body.find('td', text=re.compile(day)):
                if day == body.find('td', text=re.compile(day)).text.strip():
                    row = body.find('td', text=re.compile(day)).parent
                    cols = row.find_all('td')
                    parsed['moneda'] = coin
                    parsed['indice_tiempo'] = cols[0].text.strip()
                    parsed['tp_usd'] = cols[1].text[5:].strip()
                    parsed['tc_local'] = cols[2].text[5:].strip()
                parsed_contents.append(parsed)
            return parsed_contents
        except:
            return parsed_contents

    def _preprocess_rows(self, parsed):
        parsed['tc_local'] = self.preprocess_rows(parsed['tc_local'])
        parsed['tp_usd'] = self.preprocess_rows(parsed['tp_usd'])
        return parsed

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
                    if type(row[k]) == str:
                        if '/' in row[k]:
                            _ = row[k].split('/')
                            preprocessed_date = date.fromisoformat(
                                '-'.join([_[2], _[1], _[0]])
                            )
                        else:
                            preprocessed_date = date.fromisoformat(row[k])
                    else:
                        preprocessed_date = row[k]
                    preprocessed_row['indice_tiempo'] = preprocessed_date
                else:
                    if '-' in str(row[k]):
                        preprocessed_row[k] = None
                    else:
                        if row[k]:
                            if not type(row[k]) == Decimal:
                                if '.' in row[k]:
                                    row[k] = row[k].replace('.', '')
                                preprocessed_row[k] = (
                                        Decimal((row[k]).replace(',', '.'))
                                        if isinstance(row[k], str)
                                        else row[k]
                                    )
                        else:
                            preprocessed_row[k] = row[k]

            preprocessed_rows.append(preprocessed_row)

        return preprocessed_rows

    def write_intermediate_panel(self, rows, intermediate_panel_path):
        """
        Escribe el panel intermedio.

        Parameters
        ----------
        rows: Iterable
        """
        header = ['indice_tiempo', 'coin', 'type', 'value']

        with open(intermediate_panel_path, 'w') as intermediate_panel:
            writer = DictWriter(intermediate_panel, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    def get_intermediate_panel_data_from_parsed(self, parsed):
        """
        Recorre parsed y por cada moneda genera un diccionario
        obteniendo por separado las claves que se utilizaran como headers,
        y sus valores.

        Parameters
        ----------
        parsed : lista de diccionarios por moneda
        """
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
            l = len(intermediate_panel_data)
            for i in range(0, l):
                for j in range(0, l-i-1):
                    if (intermediate_panel_data[j]['indice_tiempo'] > intermediate_panel_data[j + 1]['indice_tiempo']):
                        tempo = intermediate_panel_data[j]
                        intermediate_panel_data[j]= intermediate_panel_data[j + 1]
                        intermediate_panel_data[j + 1]= tempo
        else:
            return []
        return intermediate_panel_data

    def reorder_parsed(self, parsed):
        l = len(parsed)
        for i in range(0, l): 
            for j in range(0, l-i-1):
                if parsed and len(parsed) > 1:
                    if (parsed[j]['indice_tiempo'] > parsed[j + 1]['indice_tiempo']):
                        tempo = parsed[j]
                        parsed[j] = parsed[j + 1]
                        parsed[j + 1] = tempo
        return parsed

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
        self.write_intermediate_panel(intermediate_panel_data, self.intermediate_panel_path)

    def parse_from_intermediate_panel(self):
        """
        Lee el dataframe del panel intermedio.
        Regresa un diccionario con las monedas como claves, y como valor
        una lista con un diccionario que contiene la fecha y los registros.

        Parameters
        ----------
        start_date : date
            Fecha de inicio que toma como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """
        _parsed = {'tc_local': [], 'tp_usd': []}
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
                    parsed_row = {}

                    columns = ['indice_tiempo']
                    columns.extend([v for v in coin_dfs[type].keys()])

                    for index, column in enumerate(columns):
                        if column == 'indice_tiempo':
                            parsed_row[column] = datetime.strptime(r[index], "%Y-%m-%d").date()
                        else:
                            parsed_row[column] = r[index]

                    if parsed_row:
                        _parsed[type].append(parsed_row)
        return _parsed

    def read_intermediate_panel_dataframe(self):
        """
        Lee el dataframe
        """
        intermediate_panel_dataframe = None

        try:
            intermediate_panel_dataframe = pd.read_csv(
                self.intermediate_panel_path,
                converters={
                    'serie_tiempo': lambda _: _,
                    'coin': lambda _: str(_),
                    'type': lambda _: str(_),
                    'value': lambda _: Decimal(_) if _ else None
                }
            )

        except FileNotFoundError:
            raise InvalidConfigurationError(
                "El archivo panel no existe"
            )

        return intermediate_panel_dataframe

    def preprocess_start_date(self, start_date):
        browser_driver = self.get_browser_driver()
        browser_driver.get(self.url)
        element_present = EC.presence_of_element_located(
            (By.NAME, 'Fecha')
        )
        elem = WebDriverWait(browser_driver, 0).until(element_present)

        if not start_date.strftime("%d/%m/%Y") in elem.text:
            logging.warning(f'La fecha {start_date.strftime("%d/%m/%Y")} no existe')

        return start_date
