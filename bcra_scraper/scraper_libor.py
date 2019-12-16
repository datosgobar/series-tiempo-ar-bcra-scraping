from csv import DictWriter
from datetime import date, timedelta, datetime
from decimal import Decimal
from functools import reduce
import logging
import os

from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
import pandas as pd
import progressbar

from bcra_scraper.scraper_base import BCRAScraper
from bcra_scraper.exceptions import InvalidConfigurationError
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


class BCRALiborScraper(BCRAScraper):
    """
    Clase que representa un Scraper para la tasa Libor del
    BCRA (Banco Central de la República Argentina).


    Attributes
    ----------
    url : str
        Una cadena que representa una url válida, usada para obtener
        el contenido a ser scrapeado
    rates : Dict
        Diccionario que contiene los plazos en días de la tasa Libor

    Methods
    -------
    fetch_contents(start_date, end_date)
        Obtiene los contenidos a ser parseados

    fetch_day_content(single_date)
        Obtiene el contenido para una determinada fecha

    parse_contents(start_date, end_date)
        Recibe un iterable de contenidos y devuelve un iterable con la
        información scrapeada

    parse_day_content(content)
        Recibe un contenido, lo scrapea y lo devuelve como un iterable

    preprocess_rows(rates, rows)
        Recibe un diccionario con los valores para los plazos en días
        de la tasa y un iterable con los contenidos scrapeados, y devuelve
        un iterable con la información normalizada

    preprocess_header(self, rates, header)
        Recibe un diccionario con los valores para los plazos en días
        de la tasa y una lista con los header que seran estandarizados

    run(start_date, end_date)
        Llama a los métodos que obtienen y scrapean los contenidos
        y los devuelve en un iterable
    """

    def __init__(self, url, rates, intermediate_panel_path, *args, **kwargs):
        """
        Parameters
        ----------
        url : str
            Una cadena que representa una url válida, usada para obtener
            el contenido a ser scrapeado. Una URL se considera válida cuando su
            contenido no está vacio.
        rates : Dict
            Diccionario que contiene los plazos en días de la tasa Libor
        """
        self.rates = rates
        self.intermediate_panel_path = intermediate_panel_path

        super(BCRALiborScraper, self).__init__(url, *args, **kwargs)

    def fetch_contents(self, start_date, end_date, intermediate_panel_data, fetched_contents):
        """
        Recorre un rango de fechas y llama a un método.
        Retorna un iterable donde cada elemento es un String, o una lista
        vacía si no hay contenidos.

        Parameters
        ----------
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date: date
            fecha de fin que va a tomar como referencia el scraper
        """
        contents = {}
        day_count = (end_date - start_date).days + 1
        cont = 0
        bar = progressbar.ProgressBar(max_value=day_count, redirect_stdout=True, \
            widgets=[progressbar.Bar('=', '[', ']'), '', progressbar.Percentage()])
        bar.start()
        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):
            if single_date not in fetched_contents:
                in_panel, day_content = self.day_content_in_panel(intermediate_panel_data, single_date)
                if not in_panel:
                    contents[single_date] = self.fetch_day_content(single_date)
            else:
                logging.warning(f'La fecha {single_date} fue descargada en el primer ciclo.')
            cont += 1
            bar.update(cont)
        bar.finish()
        return contents

    def day_content_in_panel(self, intermediate_panel_data, single_date):
        """
        Recibe la data del panel intermedio y una fecha.
        Obtiene la data del panel para ese día.

        Parameters
        ----------
        single_date : date
        intermediate_panel_data: dict
        """
        in_panel, content = False, {}
        content = intermediate_panel_data.get(single_date, {})
        if content:
            in_panel = True
        return in_panel, content

    def fetch_day_content(self, single_date):
        """
        Ingresa al navegador y retorna un html correspondiente a la fecha
        que recibe

        Parameters
        ----------
        single_date : date
            fecha que va a tomar como referencia el scraper
        """
        content = ''
        counter = 1
        tries = self.tries

        while counter <= tries:
            try:
                browser_driver = self.get_browser_driver()
                browser_driver.get(self.url)
                element_present = EC.presence_of_element_located(
                    (By.NAME, 'fecha')
                )
                element = WebDriverWait(browser_driver, 0).until(element_present)
                element.send_keys(single_date.strftime("%d/%m/%Y") + Keys.RETURN)
                content = browser_driver.page_source
            
            except NoSuchElementException:
                raise InvalidConfigurationError(
                    f'La conexion de internet ha fallado para la fecha {single_date}'
                )
            except (TimeoutException, WebDriverException):
                if counter < tries:
                    logging.warning(
                        f'La conexion de internet ha fallado para la fecha {single_date}. Reintentando...'
                    )
                    counter = counter + 1
                else:
                    logging.warning(
                        f'La conexion de internet ha fallado para la fecha {single_date}'
                    )
                    raise InvalidConfigurationError(
                        f'La conexion de internet ha fallado para la fecha {single_date}'
                    )

            break

        return content

    def parse_contents(self, contents, start_date, end_date, intermediate_panel_data):
        """
        Retorna un iterable donde cada elemento es un String, o una lista
            vacía si no hay contenidos.

        Parameters
        ----------
        contents : Iterable
            Contenidos que van a ser parseados
        """
        parsed_contents = {}
        day_count = (end_date - start_date).days + 1

        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):
            in_panel, parsed = self.day_content_in_panel(intermediate_panel_data, single_date)
            if in_panel:
                parsed_contents[single_date] = parsed
            else:
                if single_date in contents:
                    parsed = self.parse_day_content(single_date, contents[single_date])
                    if parsed:
                        _parsed = self._preprocess_rows(parsed)
                        parsed_contents[single_date] = _parsed
                        intermediate_panel_data[single_date] = _parsed
        return parsed_contents, intermediate_panel_data

    def parse_day_content(self, single_date, content):
        """
        Retorna un iterable con el contenido scrapeado cuyo formato
        posee el indice de tiempo y los plazos en días de la tasa

        Parameters
        ----------
        content : str
            Recibe un string con la información que será parseada
        """
        soup = BeautifulSoup(content, "html.parser")
        parsed = {'indice_tiempo': single_date, '30': '', '60': '', '90': '', '180': '', '360': ''}
        try:
            table = soup.find('table')
            body = table.find('tbody')

            rows = body.find_all('tr')

            for row in rows:
                validation_list = {}
                cols = row.find_all('td')
                if cols[0].text in self.rates.keys():
                    validation_list[cols[0].text] = cols[1].text

                    for r in validation_list.keys():
                        valid = self.rates_config_validator(r, self.rates)
                        if valid:
                            parsed[cols[0].text] = cols[1].text
                        else:
                            continue
            return parsed
        except:
            return parsed

    def rates_config_validator(self, parsed, rates):
        """Valida que parsed exista dentro de
        los valores de rates en el archivo de
        configuración

        Parameters
        ----------
        parsed : String
            String con la clave correspondiente al plazo en días
        rates : Dict
            Diccionario que contiene los plazos en días de la tasa Libor
        """
        if f'libor_{parsed}_dias' in rates.values():
            return True
        else:
            raise InvalidConfigurationError(
                f'La clave libor_{parsed}_dias ' +
                'no se encuentra en el archivo de config'
            )

    def _preprocess_rows(self, parsed):
        parsed = self.preprocess_rows(self.rates, parsed)
        return parsed

    def preprocess_rows(self, rates, rows):
        """
        Retorna un iterable con el contenido estandarizado

        Parameters
        ----------
        rates : Dict
            Diccionario que contiene los plazos en días de la tasa Libor

        rows : Iterable
            Iterable que contiene la información scrapeada
        """
        preprocessed_row = {}
        if type(rows['indice_tiempo']) == str:
            preprocessed_row['indice_tiempo'] = date.fromisoformat(
                rows['indice_tiempo']
            )
        else:
            preprocessed_row['indice_tiempo'] = rows['indice_tiempo']

        for rate in rates:
            if rate in rows:
                if rows[rate]:
                    preprocessed_row[rates[rate]] = Decimal(
                        str(rows[rate]).replace(',', '.')
                    )/100
                else:
                    preprocessed_row[rates[rate]] = None
            else:
                preprocessed_row[rates[rate]] = rows[rates[rate]]

        return preprocessed_row

    def preprocess_header(self, rates):
        """
        Retorna un iterable con los encabezados estandarizados

        Parameters
        ----------
        rates : Dict
            Diccionario que contiene los plazos en días de la tasa Libor
        """
        preprocessed_header = []

        preprocessed_header.append('indice_tiempo')

        for value in rates.values():
            preprocessed_header.append(value)
        return preprocessed_header

    def get_intermediate_panel_data_from_parsed(self, parsed):
        """
        Recorre parsed y por cada plazo en días genera un diccionario
        obteniendo por separado las claves que se utilizaran como headers,
        y sus valores.

        Parameters
        ----------
        parsed : dict
        """
        intermediate_panel_data = self.parsed_to_panel_dataframe(parsed)
        return intermediate_panel_data

    def parsed_to_panel_dataframe(self, parsed):
        """
        Recibe un diccionario, y a partir de sus valores crea el dataframe del panel.
        Devuelve una lista de diccionarios con los datos del panel a partir de lo que recibe.

        Parameters
        ----------
        parsed: dict
        """
        def create_multi_index_column(field_title):
            """Crea multi index desarmando el título de un campo."""
            libor, day_type, days = field_title.split("_")
            return (day_type, days)

        df = pd.DataFrame(parsed.values()).set_index("indice_tiempo")
        df = df[['libor_30_dias', 'libor_60_dias', 'libor_90_dias', 'libor_180_dias', 'libor_360_dias']]
        df.sort_index(inplace=True)
        df.columns = pd.MultiIndex.from_tuples([create_multi_index_column(col) for col in df.columns])
        df.columns = df.columns.droplevel(level=1)
        df_panel = df.stack([-1], dropna=False).reset_index()
        df_panel.columns = ["indice_tiempo", "type", "value"]
        df_panel["indice_tiempo"] = df_panel["indice_tiempo"].apply(lambda x: x)
        df_panel["value"] = df_panel["value"].apply(lambda x: x if x and x > 0 else None)
        panel_data = df_panel.to_dict(orient='records')
        return panel_data

    def write_intermediate_panel(self, rows, intermediate_panel_path):
        """
        Escribe el panel intermedio.

        Parameters
        ----------
        rows: Iterable
        """
        header = ['indice_tiempo', 'type', 'value']

        with open(os.path.join(intermediate_panel_path), 'w') as intermediate_panel:
            writer = DictWriter(intermediate_panel, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

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
        Regresa una lista con un diccionario por cada fecha

        Parameters
        ----------
        start_date : date
            Fecha de inicio que toma como referencia el scraper
        end_date : date
            fecha de fin que va a tomar como referencia el scraper
        """
        parsed = {}
        df_panel = self.read_intermediate_panel_dataframe()
        parsed = self.get_parsed(df_panel)
        return parsed

    def get_parsed(self, df_panel):
        """
        Recibe un dataframe a partir del cual genera una tabla pivot.
        Devuelve un diccionario con el día como clave, y otro diccionario
        con los datos de ese día como valor.

        Parameters
        ----------
        df_panel: dataframe con los datos del panel intermedio.
        """
        def create_field_title(col_multi_index):
            """Convierte columnas multi index a nombre de campo plano."""
            type = col_multi_index
            field_title = "libor_{type}_dias".format(
                type=type
            )
            return field_title
        _parsed = {}
        columns = ['indice_tiempo']
        columns.extend([v for v in self.rates.values()])
        if not df_panel.empty:
            df_pivot = df_panel.pivot_table(
                index="indice_tiempo",
                columns=["type"],
                values="value",
                aggfunc=sum,
                dropna=False
            )
            df_pivot = df_pivot.replace([0], [None])
            flatten_columns = [create_field_title(col) for col in df_pivot.columns]
            df_pivot.columns = flatten_columns
            df_pivot.reset_index(inplace=True)
            df_pivot['indice_tiempo'] = pd.to_datetime(df_pivot['indice_tiempo'], format="%Y-%m-%d", errors='ignore', infer_datetime_format=True)
            # Se pasa primero a datetime y después a date porque si se trata de pasar directo a date rompe.
            df_pivot['indice_tiempo'] = df_pivot['indice_tiempo'].dt.date
            df_pivot['index'] = df_pivot['indice_tiempo']
            df_pivot.set_index(['index'], inplace=True)
            _parsed = df_pivot.to_dict(orient="index")
        return _parsed

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

    def delete_date_from_panel(self, intermediate_panel_data, single_date):
        del intermediate_panel_data[single_date]
        return intermediate_panel_data

    def check_empty_date(self, parsed):
        """
        Chequea si hay datos en parsed para esa fecha.

        Parameters
        ----------
        parsed: diccionario con los datos del panel intermedio para un día.
        """
        valid_keys = parsed.keys() - ['indice_tiempo']
        return any(parsed[k] for k in valid_keys)

    def empty_refetch_data(self):
        return {}

    def merge_parsed(self, parsed, refetched_parsed):
        merged_parsed = {}
        merged_parsed = {**parsed, **refetched_parsed}
        return merged_parsed