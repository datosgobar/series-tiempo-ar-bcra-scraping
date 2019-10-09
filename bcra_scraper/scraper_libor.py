from csv import DictWriter
from datetime import date, timedelta, datetime
from decimal import Decimal
from functools import reduce
import logging
import os

from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
import pandas as pd

from bcra_scraper.scraper_base import BCRAScraper
from bcra_scraper.exceptions import InvalidConfigurationError
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


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

    def fetch_contents(self, start_date, end_date, intermediate_panel_data):
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
        contents = []
        day_count = (end_date - start_date).days + 1

        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):

            if not self.intermediate_panel_data_has_date(intermediate_panel_data, single_date):
                contents.append(self.fetch_day_content(single_date))
        return contents

    def intermediate_panel_data_has_date(self, intermediate_panel_data, single_date):
        content = []
        for data in intermediate_panel_data:
            if single_date.strftime("%Y-%m-%d") == data['indice_tiempo'].strftime("%Y-%m-%d"):
                content = data
        return content

    def fetch_day_content(self, single_date):
        """
        Ingresa al navegador y retorna un html correspondiente a la fecha
        que recibe

        Parameters
        ----------
        single_date : date
            fecha que va a tomar como referencia el scraper
        """
        content_dict = {}
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
                content_dict[f'{single_date.strftime("%Y-%m-%d")}'] = content
            except TimeoutException:
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
            except NoSuchElementException:
                raise InvalidConfigurationError(
                    f'La conexion de internet ha fallado para la fecha {single_date}'
                )

            break

        return content_dict

    def parse_contents(self, contents, start_date, end_date, intermediate_panel_data):
        """
        Retorna un iterable donde cada elemento es un String, o una lista
            vacía si no hay contenidos.

        Parameters
        ----------
        contents : Iterable
            Contenidos que van a ser parseados
        """
        parsed_contents = []
        day_count = (end_date - start_date).days + 1
        for single_date in (start_date + timedelta(n)
                            for n in range(day_count)):
            if not self.intermediate_panel_data_has_date(intermediate_panel_data, single_date):
                for content in contents:
                    if single_date.strftime("%Y-%m-%d") in content:
                        parsed = self.parse_day_content(single_date.strftime("%Y-%m-%d"), content[single_date.strftime("%Y-%m-%d")])
                        if parsed:
                            _parsed = self._preprocess_rows([parsed])
                            parsed_contents.extend(_parsed)
                            intermediate_panel_data.extend(_parsed)
            else:
                parsed_contents.append(self.intermediate_panel_data_has_date(intermediate_panel_data, single_date))
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
        preprocessed_rows = []
        for row in rows:
            preprocessed_row = {}
            if type(row['indice_tiempo']) == str:
                preprocessed_row['indice_tiempo'] = date.fromisoformat(
                    row['indice_tiempo']
                )
            else:
                preprocessed_row['indice_tiempo'] = row['indice_tiempo']

            for rate in rates:
                if rate in row:
                    if row[rate]:
                        preprocessed_row[rates[rate]] = Decimal(
                            str(row[rate]).replace(',', '.')
                        )/100
                    else:
                        preprocessed_row[rates[rate]] = None
                else:
                    preprocessed_row[rates[rate]] = row[rates[rate]]

            preprocessed_rows.append(preprocessed_row)
        return preprocessed_rows

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
        parsed : lista de diccionarios por moneda
        """
        intermediate_panel_data = []
        rate_dfs = {}
        data = []
        if parsed:
            data = [[v for v in p.values()] for p in parsed]
        columns = ['indice_tiempo']
        columns.extend([v for v in self.rates.keys()])

        rate_dfs_panel = pd.DataFrame(
            data=[],
            columns=['indice_tiempo', 'value', 'type']
        )

        df = pd.DataFrame(data, columns=columns)
        df = df.sort_values(['indice_tiempo'])
        df.drop_duplicates(subset="indice_tiempo", keep='first', inplace=True)

        for k in self.rates.keys():
            rate_dfs[k] = df[['indice_tiempo', k]].copy()
            rate_dfs[k]['type'] = k
            rate_dfs[k].rename(columns={k: 'value'}, inplace=True)
            rate_dfs_panel = rate_dfs_panel.append(rate_dfs[k])

        intermediate_panel_data = [
            {
                'indice_tiempo': r[1],
                'type': r[3],
                'value': r[2],
            }
            for r in rate_dfs_panel.to_records()
        ]
        return intermediate_panel_data

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
        _parsed = []
        rate_dfs = {}
        columns = ['indice_tiempo']
        columns.extend([v for v in self.rates.values()])

        intermediate_panel_df = self.read_intermediate_panel_dataframe()
        intermediate_panel_df.set_index(['indice_tiempo'], inplace=True)

        if not intermediate_panel_df.empty:
            for k, v in self.rates.items():
                rate_dfs[v] = intermediate_panel_df.loc[
                    intermediate_panel_df['type'] == k
                ][['value']]
                rate_dfs[v].rename(columns={'value': v}, inplace=True)
            rates_df = reduce(
                lambda df1, df2: df1.merge(
                    df2, left_on='indice_tiempo', right_on='indice_tiempo'
                ),
                rate_dfs.values(),
            )

            for r in rates_df.to_records():
                parsed_row = {}

                columns = ['indice_tiempo']
                columns.extend([v for v in self.rates.values()])

                for index, column in enumerate(columns):
                    if column == 'indice_tiempo':
                        parsed_row[column] = datetime.strptime(r[index], "%Y-%m-%d").date()
                    else:
                        parsed_row[column] = r[index]

                if parsed_row:
                    _parsed.append(parsed_row)
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
                    'type': lambda _: str(_),
                    'value': lambda _: Decimal(_) if _ else None
                }
            )

        except FileNotFoundError:
            raise InvalidConfigurationError(
                "El archivo panel no existe"
            )
        return intermediate_panel_dataframe
