from csv import DictWriter
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import reduce
import logging

from bs4 import BeautifulSoup
import pandas as pd
import progressbar

from bcra_scraper.exceptions import InvalidConfigurationError
from bcra_scraper.scraper_base import BCRAScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


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

    def __init__(self, url, coins, intermediate_panel_path, types, *args, **kwargs):
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
        self.intermediate_panel_path = intermediate_panel_path
        self.types = types
        super(BCRASMLScraper, self)\
            .__init__(url, *args, **kwargs)

    def fetch_contents(self, start_date, end_date, intermediate_panel_data, fetched_contents):
        """
        Función que a traves de un loop llama a un método
        y regresa un diccionario con el html de cada moneda.

        Parameters
        ----------
        coins : Dict
            Diccionario que contiene las monedas
        """

        contents = {'peso_uruguayo': {}, 'real': {}}
        day_count = (end_date - start_date).days + 1
        cont = 0
        bar = progressbar.ProgressBar(max_value=day_count, redirect_stdout=True, \
            widgets=[progressbar.Bar('=', '[', ']'), '', progressbar.Percentage()])
        bar.start()
        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):
            if not self.day_in_fetched_contents(fetched_contents, single_date):
                in_panel, day_content = self.day_content_in_panel(intermediate_panel_data, single_date)
                if not in_panel:
                    for k, v in self.coins.items():
                        fetched = self.fetch_content(v)
                        if fetched:
                            contents[k][single_date] = fetched
            else:
                logging.warning(f'La fecha {single_date} fue descargada en el primer ciclo.')
            cont += 1
            bar.update(cont)
        bar.finish()
        return contents

    def day_in_fetched_contents(self, fetched_contents, single_date):
        """
        Chequea si la fecha se encuentra en los contenidos
        descargados en el primer ciclo,
        y devuelve el booleano correspondiente.
        """
        in_fetched_contents = False
        for coin in ['peso_uruguayo', 'real']:
            data = fetched_contents.get(coin, None)
            if data:
                if single_date in data:
                    in_fetched_contents = True
        return in_fetched_contents

    def day_content_in_panel(self, intermediate_panel_data, single_date):
        in_panel, day_content = False, {'peso_uruguayo': {}, 'real': {}}

        for coin in ['peso_uruguayo', 'real']:
            data = intermediate_panel_data.get(coin, None)
            if data:
                day_content[coin] = data.get(single_date, {})
                if day_content[coin]:
                    in_panel = True

        return in_panel, day_content

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

    def fetch_content(self, coin):
        """
        Ingresa al navegador y utiliza la moneda
        regresando el contenido que pertenece a la misma.

        Parameters
        ----------
        coins : String
            String que contiene el nombre de la moneda
        """
        content = ''
        counter = 1
        tries = self.tries

        while counter <= tries:
            try:
                browser_driver = self.get_browser_driver()
                browser_driver.get(self.url)
                element_present = EC.presence_of_element_located(
                    (By.NAME, 'moneda')
                )
                element = WebDriverWait(browser_driver, 0).until(element_present)

                options = element.find_elements_by_tag_name('option')
                valid = self.validate_coin_in_configuration_file(coin, options)
                if valid:
                    element.send_keys(coin)
                    content = browser_driver.page_source

            except NoSuchElementException:
                raise InvalidConfigurationError(
                    f'La conexion de internet ha fallado para la moneda {coin}'
                )
            except (TimeoutException, WebDriverException):
                if counter < tries:
                    logging.warning(
                        f'La conexion de internet ha fallado para la moneda {coin}. Reintentando...'
                    )
                    counter = counter + 1
                else:
                    logging.warning(
                        f'La conexion de internet ha fallado para la moneda {coin}'
                    )
                    raise InvalidConfigurationError(
                        f'La conexion de internet ha fallado para la moneda {coin}'
                    )

            break

        return content

    def parse_contents(self, contents, start_date, end_date, intermediate_panel_data):
        """
        Recorre un iterable que posee los html y llama a un método.
        Retorna un diccionario con las monedas como clave y como valor
        una lista con un diccionario.

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
        parsed_contents = {'peso_uruguayo': {}, 'real': {}}
        day_count = (end_date - start_date).days + 1

        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):
            in_panel, parsed = self.day_content_in_panel(intermediate_panel_data, single_date)

            if in_panel:
                parsed_contents['peso_uruguayo'][single_date] = parsed['peso_uruguayo']
                parsed_contents['real'][single_date] = parsed['real']
            else:
                for coin in self.coins.keys():
                    if contents[coin]:
                        parsed = self.parse_content(contents[coin][single_date], coin, single_date)
                        if parsed:
                            for p in parsed:
                                preprocess_dict = {}
                                preprocess_dict = self.preprocess_rows([p])
                                for d in preprocess_dict:
                                    for k, v in self.types[d['coin']].items():
                                        if d['indice_tiempo'] not in parsed_contents[coin].keys():
                                            parsed_contents[coin][d['indice_tiempo']] = {}
                                        parsed_contents[coin][d['indice_tiempo']][v] = d[k]
                                        parsed_contents[coin][d['indice_tiempo']]['indice_tiempo'] = d['indice_tiempo']

                                        if d['indice_tiempo'] not in intermediate_panel_data[coin].keys():
                                            intermediate_panel_data[coin][d['indice_tiempo']] = {}
                                        intermediate_panel_data[coin][d['indice_tiempo']][v] = d[k]
                                        intermediate_panel_data[coin][d['indice_tiempo']]['indice_tiempo'] = d['indice_tiempo']

        return parsed_contents, intermediate_panel_data

    def parse_content(self, content, coin, single_date):
        """
        Retorna un iterable con el contenido scrapeado cuyo formato
        posee la moneda, el indice de tiempo, y los tipo de cambio
        correspondientes a la moneda.

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

            head_rows = head.find_all('tr')
            parsed_content = []

            day = single_date.strftime("%d/%m/%Y")
            for header in head_rows:
                headers = header.find_all('th')
                parsed = {}
                parsed['coin'] = coin
                parsed['indice_tiempo'] = single_date
                parsed[headers[1].text] = ''
                parsed[headers[2].text] = ''
                parsed[headers[3].text] = ''
                parsed[headers[4].text] = ''

                if body.find('td', text=day):
                    row = body.find('td', text=day).parent
                    cols = row.find_all('td')
                    parsed['coin'] = coin
                    parsed['indice_tiempo'] = single_date
                    parsed[headers[1].text] = cols[1].text.strip()
                    parsed[headers[2].text] = cols[2].text.strip()
                    parsed[headers[3].text] = cols[3].text.strip()
                    parsed[headers[4].text] = cols[4].text.strip()
                parsed_content.append(parsed)

            return parsed_content
        except:
            return []

    def _preprocess_rows(self, parsed):
        parsed['peso_uruguayo'] = self.preprocess_rows(
            parsed['peso_uruguayo']
            )
        parsed['real'] = self.preprocess_rows(parsed['real'])

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
                if k != 'coin':
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
                        if row[k]:
                            preprocessed_row[k] = (
                                Decimal((row[k]).replace(',', '.'))
                                if isinstance(row[k], str)
                                else row[k]
                            )
                        else:
                            preprocessed_row[k] = row[k]
                else:
                    preprocessed_row[k] = row[k]

            preprocessed_rows.append(preprocessed_row)

        return preprocessed_rows

    def get_intermediate_panel_data_from_parsed(self, parsed):
        """
        Recorre parsed y por cada tipo de cambio genera un diccionario
        obteniendo por separado las claves que se utilizaran como headers,
        y sus valores.

        Parameters
        ----------
        parsed : lista de diccionarios por moneda
        """
        intermediate_panel_data = []
        if parsed:
            for currency in ["peso_uruguayo", "real"]:
                parsed_by_currency = parsed[currency]

                panel_by_currency = self.parsed_to_panel_dataframe(
                    parsed_by_currency, currency)

                intermediate_panel_data.extend(panel_by_currency)
        return intermediate_panel_data

    def parsed_to_panel_dataframe(self, parsed, coin):
        """
        Recibe una lista de diccionarios a partir de la cual crea el dataframe del panel.
        Devuelve una lista de diccionarios con los datos del panel a partir de lo que recibe.

        Parameters
        ----------
        parsed_by_currency: lista de diccionarios por día de una moneda.
        """
        df = pd.DataFrame(parsed.values()).set_index("indice_tiempo")
        df.sort_index(inplace=True)
        df_panel = df.stack([-1], dropna=False).reset_index()
        df_panel["coin"] = coin
        df_panel.columns = ["indice_tiempo", "type", "value", "coin"]
        df_panel = df_panel[["indice_tiempo", "coin", "type", "value"]]
        df_panel["indice_tiempo"] = df_panel[
            "indice_tiempo"].apply(lambda x: x)
        df_panel["value"] = df_panel["value"].apply(
            lambda x: x if x and x > 0 else None)
        panel_data = df_panel.to_dict(orient="records")

        return panel_data

    def parse_from_intermediate_panel(self):
        """
        Lee el dataframe del panel intermedio.
        Retorna un diccionario con las monedas como clave y como valor
        una lista con un diccionario.
        Parameters
        ----------
        start_date : date
            Fecha de inicio que toma como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """
        _parsed = {'peso_uruguayo': {}, 'real': {}}
        df_panel = self.read_intermediate_panel_dataframe()
        if not df_panel.empty:
            for coin in ['peso_uruguayo', 'real']:
                _parsed[coin] = self.get_parsed_by_currency(df_panel, coin)
        return _parsed

    def get_parsed_by_currency(self, df_panel, coin):
        """
        Recibe un dataframe a partir del cual genera una tabla pivot.
        Devuelve una lista de diccionarios.

        Parameters
        ----------
        df_panel: dataframe con los datos del panel intermedio.
        coin : string con el nombre de la moneda.
        """
        df_panel.columns = ['indice_tiempo', 'coin', 'type',
                            'value']
        df_pivot_coin = df_panel[df_panel.coin == coin].pivot_table(
            index="indice_tiempo",
            columns=["type"],
            values="value",
            aggfunc=sum,
            dropna=False
        )
        df_pivot_coin = df_pivot_coin.replace([0], [None])
        df_pivot_coin.reset_index(inplace=True)
        df_pivot_coin['indice_tiempo'] = pd.to_datetime(df_pivot_coin['indice_tiempo'], format="%Y-%m-%d", errors='ignore', infer_datetime_format=True)
        # Se pasa primero a datetime y después a date porque si se trata de pasar directo a date rompe.
        df_pivot_coin['indice_tiempo'] = df_pivot_coin['indice_tiempo'].dt.date
        df_pivot_coin['index'] = df_pivot_coin['indice_tiempo']
        df_pivot_coin.set_index(['index'], inplace=True)
        parsed_by_currency = df_pivot_coin.to_dict(orient="index")
        return parsed_by_currency

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

    def read_intermediate_panel_dataframe(self):
        """
        Lee el dataframe
        """
        intermediate_panel_dataframe = None

        try:
            intermediate_panel_dataframe = self.create_intermediate_panel_dataframe()

        except FileNotFoundError:
            self.create_intermediate_panel()
            intermediate_panel_dataframe = self.create_intermediate_panel_dataframe()
        return intermediate_panel_dataframe

    def create_intermediate_panel(self):
        rows = []
        self.write_intermediate_panel(rows, self.intermediate_panel_path)

    def create_intermediate_panel_dataframe(self):
        intermediate_panel_dataframe = pd.read_csv(
            self.intermediate_panel_path,
            converters={
                'serie_tiempo': lambda _: _,
                'coin': lambda _: str(_),
                'type': lambda _: str(_),
                'value': lambda _: Decimal(_) if _ else None
            }
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
        self.write_intermediate_panel(intermediate_panel_data, self.intermediate_panel_path)

    def delete_date_from_panel(self, intermediate_panel_data, single_date):
        for coin in ['peso_uruguayo', 'real']:
            del intermediate_panel_data[coin][single_date]
        return intermediate_panel_data

    def check_empty_date(self, parsed):
        """
        Chequea si hay datos en parsed para esa fecha.

        Parameters
        ----------
        parsed: diccionario con los datos del panel intermedio para un día.
        """

        def parsed_coin_is_empty(parsed_coin):
            is_empty = any(
                [parsed_coin[k]for k in parsed_coin.keys() - ['indice_tiempo']]
            )

            return is_empty

        return any(parsed_coin_is_empty(p) for p in parsed.values())

    def empty_refetch_data(self):
        return {'peso_uruguayo': {}, 'real': {}}

    def merge_parsed(self, parsed, refetched_parsed):
        merged_parsed = {'peso_uruguayo': {}, 'real': {}}
        for coin in ['peso_uruguayo', 'real']:
            merged_parsed[coin] = {**parsed[coin], **refetched_parsed[coin]}
        return merged_parsed