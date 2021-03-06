from csv import DictWriter
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import reduce
import logging
import re

from bs4 import BeautifulSoup
from pandas import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import progressbar

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

    def __init__(self, url, coins, entities, intermediate_panel_path, *args, **kwargs):
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
        self.intermediate_panel_path = intermediate_panel_path
        super(BCRATCEScraper, self)\
            .__init__(url, *args, **kwargs)

    def fetch_contents(self, start_date, end_date, intermediate_panel_data, fetched_contents):
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
        contents = {'dolar': {}, 'euro': {}}
        day_count = (end_date - start_date).days + 1
        cont = 0
        bar = progressbar.ProgressBar(max_value=day_count, redirect_stdout=True,
                                      widgets=[progressbar.Bar('=', '[', ']'), '', progressbar.Percentage()])
        bar.start()
        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):
            if not self.day_in_fetched_contents(fetched_contents, single_date):
                in_panel, day_content = self.day_content_in_panel(intermediate_panel_data, single_date)
                if not in_panel:
                    for k, v in self.coins.items():
                        fetched = self.fetch_content(single_date, v)
                        contents[k][single_date] = fetched
            else:
                logging.warning(f'La fecha {single_date} fue descargada en el primer ciclo.')
            cont += 1
            bar.update(cont)
        bar.finish()

        return contents

    def empty_fetched_contents(self):
        return {'dolar': {}, 'euro': {}}

    def day_in_fetched_contents(self, fetched_contents, single_date):
        """
        Chequea si la fecha se encuentra en los contenidos
        descargados en el primer ciclo,
        y devuelve el booleano correspondiente.
        """
        in_fetched_contents = any([single_date in fetched_contents[coin] for coin in self.coins.keys()])
        return in_fetched_contents


    def day_content_in_panel(self, intermediate_panel_data, single_date):
        """
        Devuelve un diccionario con los valores para esa fecha en
        el panel intermedio.
        """
        in_panel, day_content = False, {'dolar': {}, 'euro': {}}
        for coin in ['dolar', 'euro']:
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

    def fetch_content(self, single_date, coin):
        """
        Ingresa al navegador y utiliza la moneda
        regresando el contenido que pertenece a la misma.

        Parameters
        ----------
        single_date : date
            Fecha de inicio que toma como referencia el scraper
        coin : String
            String que contiene el nombre de la moneda
        """
        content = ''
        counter = 1
        tries = self.tries

        while counter <= tries and not content:
            try:
                browser_driver = self.get_browser_driver()
                browser_driver.get(self.url)
                element_present = EC.presence_of_element_located(
                    (By.NAME, 'moneda')
                )
                element = WebDriverWait(
                    browser_driver, 0).until(element_present)

                options = element.find_elements_by_tag_name('option')
                valid = self.validate_coin_in_configuration_file(coin, options)

                if valid:
                    element.send_keys(coin)
                    browser_driver.execute_script(
                        'document.getElementsByName("fecha")\
                        [0].removeAttribute("readonly")')
                    elem = browser_driver.find_element_by_name('fecha')
                    elem.send_keys(single_date.strftime("%d/%m/%Y"))
                    submit_button = browser_driver.find_element_by_class_name(
                        'btn-primary')
                    submit_button.click()
                    content = browser_driver.page_source

            except NoSuchElementException:
                logging.warning(
                    f'No se encontró la moneda: {coin}. Reintentando...'
                )
                counter = counter + 1
            except (TimeoutException, WebDriverException):
                if counter < tries:
                    logging.warning(
                        f'La conexion de internet ha fallado para la moneda {coin}. Reintentando...'
                    )
                    counter = counter + 1
                else:
                    logging.warning(
                        f'Cantidad máxima de intentos alcanzada para la moneda {coin}'
                    )
                    return content
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
        for currency in ["dolar", "euro"]:
            parsed_by_currency = parsed[currency]

            panel_by_currency = self.parsed_to_panel_dataframe(
                parsed_by_currency)

            intermediate_panel_data.extend(panel_by_currency)

        return intermediate_panel_data

    def parsed_to_panel_dataframe(self, parsed):
        """
        Recibe una lista de diccionarios a partir de la cual crea el dataframe del panel.
        Devuelve una lista de diccionarios con los datos del panel a partir de lo que recibe.

        Parameters
        ----------
        parsed_by_currency: lista de diccionarios por día de una moneda.
        """

        def create_multi_index_column(field_title):
            """Crea multi index desarmando el título de un campo."""
            tc, ars, coin, entity, channel, flow, hour = field_title.split("_")
            return (coin, entity, channel, flow, hour)

        df = pd.DataFrame(parsed.values()).set_index("indice_tiempo")
        df.sort_index(inplace=True)
        df.columns = pd.MultiIndex.from_tuples(
            [create_multi_index_column(col) for col in df.columns])
        df_panel = df.stack([-5, -4, -3, -2, -1], dropna=False).reset_index()
        df_panel.columns = ["indice_tiempo", "coin",
                            "entity", "channel", "flow", "hour", "value"]
        df_panel.columns = ["indice_tiempo", "moneda",
                            "entidad_bancaria", "canal", "flujo", "hora", "valor"]
        df_panel["indice_tiempo"] = df_panel[
            "indice_tiempo"].apply(lambda x: x)
        df_panel["valor"] = df_panel["valor"].apply(
            lambda x: x if x and x > 0 else None)
        panel_data = df_panel.to_dict(orient="records")

        return panel_data

    def parse_from_intermediate_panel(self):
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
        _parsed = {'dolar': {}, 'euro': {}}

        df_panel = self.read_intermediate_panel_dataframe()

        if not df_panel.empty:
            for coin in ['dolar', 'euro']:
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
        def create_field_title(col_multi_index, coin):
            """Convierte columnas muli index a nombre de campo plano."""
            entity, channel, flow, hour = col_multi_index
            field_title = "tc_ars_{coin}_{entity}_{channel}_{flow}_{hour}".format(
                coin=coin,
                entity=entity,
                channel=channel,
                flow=flow,
                hour=hour
            )
            return field_title

        df_panel.columns = ['indice_tiempo', 'moneda', 'entidad_bancaria',
                            'canal', 'flujo', 'hora', 'valor']
        df_pivot_coin = df_panel[df_panel.moneda == coin].pivot_table(
            index="indice_tiempo",
            columns=["entidad_bancaria", "canal", "flujo", "hora"],
            values="valor",
            aggfunc=sum,
            dropna=False
        )
        df_pivot_coin = df_pivot_coin.replace([0], [None])
        flatten_columns = [create_field_title(
            col, coin) for col in df_pivot_coin.columns]
        df_pivot_coin.columns = flatten_columns
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
        header = [
            'indice_tiempo',
            'moneda',
            'entidad_bancaria',
            'canal',
            'flujo',
            'hora',
            'valor'
        ]
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
                'valor': lambda _: Decimal(_) if _ else None
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
        self.write_intermediate_panel(
            intermediate_panel_data, self.intermediate_panel_path)

    def parse_contents(self, contents, start_date, end_date, intermediate_panel_data):
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
        parsed_contents = {'dolar': {}, 'euro': {}}
        day_count = (end_date - start_date).days + 1
        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):
            in_panel, parsed = self.day_content_in_panel(intermediate_panel_data, single_date)
            if in_panel:
                parsed_contents['dolar'][single_date] = parsed['dolar']
                parsed_contents['euro'][single_date] = parsed['euro']
            else:
                for k in self.coins:
                    if contents[k]:
                        day_content = contents[k][single_date]
                        parsed = self.parse_content(
                            day_content, single_date, k, self.entities)
                        preprocess_dict = {}
                        preprocess_dict = self.preprocess_rows([parsed])
                        for d in preprocess_dict:
                            parsed_contents[k][single_date] = d
                            intermediate_panel_data[k][single_date] = d
        return parsed_contents, intermediate_panel_data

    def parse_content(self, content, single_date, coin, entities):
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
        parsed = self.get_parsed(single_date, coin, entities)
        try:
            table = soup.find(
                class_='table table-BCRA table-bordered table-hover ' +
                'table-responsive'
            )

            if not table:
                return parsed

            body = table.find('tbody')

            if not body:
                return parsed

            for k, v in entities.items():
                if body.find('td', text=re.compile(re.escape(v.get('name')))): 
                    row = body.find(
                        'td', text=re.compile(re.escape(v.get('name')))).parent
                    cols = row.find_all('td')
                    parsed[
                        'indice_tiempo'
                    ] = single_date
                    for hour in ['11', '13', '15']:
                        parsed = self.parse_hour(
                            v, k, hour, coin, parsed, cols)
            return parsed
        except:
            return parsed

    def parse_hour(self, config, entity, hour, coin, parsed, cols):
        mapping_values = {
            'mostrador_compra_11': 1,
            'mostrador_compra_13': 5,
            'mostrador_compra_15': 9,
            'electronico_compra_11': 3,
            'electronico_compra_13': 7,
            'electronico_compra_15': 11,
            'mostrador_venta_11': 2,
            'mostrador_venta_13': 6,
            'mostrador_venta_15': 10,
            'electronico_venta_11': 4,
            'electronico_venta_13': 8,
            'electronico_venta_15': 12
        }
        config = config['coins'].get(coin)
        for k in config[hour]['channels'].keys():
            for f in ['compra', 'venta']:
                parsed[
                    f'tc_ars_{coin}_{entity}_{k}_{f}_{hour}hs'
                ] =\
                    (cols[mapping_values[f'{k}_{f}_{hour}']].text.strip())
        return parsed

    def get_parsed(self, day, coin, entities):
        parsed = {}
        for k in entities.keys():
            parsed[
                'indice_tiempo'
            ] = day
            parsed[
                f'tc_ars_{coin}_{k}_mostrador_compra_11hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_mostrador_compra_13hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_mostrador_compra_15hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_electronico_compra_11hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_electronico_compra_13hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_electronico_compra_15hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_mostrador_venta_11hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_mostrador_venta_13hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_mostrador_venta_15hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_electronico_venta_11hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_electronico_venta_13hs'
            ] = ''
            parsed[
                f'tc_ars_{coin}_{k}_electronico_venta_15hs'
            ] = ''
        return parsed

    def _preprocess_rows(self, parsed):
        parsed['dolar'] = self.preprocess_rows(
            parsed['dolar']
        )
        parsed['euro'] = self.preprocess_rows(parsed['euro'])

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
                            preprocessed_date = row[k]
                    else:
                        preprocessed_date = row[k]
                    preprocessed_row['indice_tiempo'] = preprocessed_date
                else:
                    if row[k] == '':
                        preprocessed_row[k] = None
                    else:
                        preprocessed_row[k] = (
                            Decimal((row[k]).replace(',', '.'))
                            if isinstance(row[k], str)
                            else row[k]
                        )

            preprocessed_rows.append(preprocessed_row)

        return preprocessed_rows

    def delete_date_from_panel(self, intermediate_panel_data, single_date):
        for coin in ['dolar', 'euro']:
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
        return {'dolar': {}, 'euro': {}}

    def merge_parsed(self, parsed, refetched_parsed):
        merged_parsed = {'dolar': {}, 'euro': {}}
        for coin in ['dolar', 'euro']:
            merged_parsed[coin] = {**parsed[coin], **refetched_parsed[coin]}
        return merged_parsed
