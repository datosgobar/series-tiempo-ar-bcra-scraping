from csv import DictWriter
from datetime import date, timedelta
from decimal import Decimal
from functools import reduce

from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
import pandas as pd

from bcra_scraper.scraper_base import BCRAScraper


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

    def __init__(self, url, rates, *args, **kwargs):
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

        super(BCRALiborScraper, self).__init__(url, *args, **kwargs)

    def fetch_contents(self, start_date, end_date):
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

            contents.append(self.fetch_day_content(single_date))
        return contents

    def fetch_day_content(self, single_date):
        """
        Ingresa al navegador y retorna un html correspondiente a la fecha
        que recibe

        Parameters
        ----------
        single_date : date
            fecha que va a tomar como referencia el scraper
        """
        browser_driver = self.get_browser_driver()
        browser_driver.get(self.url)
        elem = browser_driver.find_element_by_name('fecha')
        elem.send_keys(single_date.strftime("%d/%m/%Y") + Keys.RETURN)
        content = browser_driver.page_source

        return content

    def parse_contents(self, contents):
        """
        Retorna un iterable donde cada elemento es un String, o una lista
            vacía si no hay contenidos.

        Parameters
        ----------
        contents : Iterable
            Contenidos que van a ser parseados
        """
        parsed_contents = []
        for content in contents:
            parsed = self.parse_day_content(content)

            if parsed:
                parsed_contents.append(parsed)

        return parsed_contents

    def parse_day_content(self, content):
        """
        Retorna un iterable con el contenido scrapeado cuyo formato
        posee el indice de tiempo y los plazos en días de la tasa

        Parameters
        ----------
        content : str
            Recibe un string con la información que será parseada
        """
        soup = BeautifulSoup(content, "html.parser")
        parsed = {}
        table = soup.find('table')
        head = table.find('thead')
        body = table.find('tbody')

        if not body:
            return parsed

        rows = body.find_all('tr')

        parsed['indice_tiempo'] = head.findAll('th')[0].text[14:].strip()
        splited = parsed['indice_tiempo'].split('/')
        parsed['indice_tiempo'] = '-'.join(
            [splited[2], splited[1], splited[0]]
        )

        for row in rows:
            cols = row.find_all('td')
            parsed[cols[0].text] = cols[1].text
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

            preprocessed_row['indice_tiempo'] = date.fromisoformat(
                row['indice_tiempo']
            )

            for rate in rates:
                preprocessed_row[rates[rate]] = Decimal(
                    str(row[rate]).replace(',', '.')
                )/100

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

        for key, value in rates.items():
            preprocessed_header.append(value)
        return preprocessed_header

    def get_intermediate_panel_data_from_parsed(self, parsed):
        intermediate_panel_data = []

        if parsed:
            rate_dfs = {}
            data = [[v for v in p.values()] for p in parsed]
            columns = ['indice_tiempo']
            columns.extend([v for v in self.rates.keys()])

            rate_dfs_panel = pd.DataFrame(
                data=[],
                columns=['indice_tiempo', 'value', 'type']
            )

            df = pd.DataFrame(data, columns=columns)

            for k in self.rates.keys():
                rate_dfs[k] = df[['indice_tiempo', k]].copy()
                rate_dfs[k]['type'] = k
                rate_dfs[k].rename(columns={k: 'value'}, inplace=True)
                rate_dfs_panel = rate_dfs_panel.append(rate_dfs[k])

        else:
            return []

        intermediate_panel_data = [
            {
                'indice_tiempo': r[1],
                'type': r[3],
                'value': r[2],
            }
            for r in rate_dfs_panel.to_records()
        ]
        return intermediate_panel_data

    def write_intermediate_panel(self, rows):
        header = ['indice_tiempo', 'type', 'value']

        with open('.libor-intermediate-panel.csv', 'w') as intermediate_panel:
            writer = DictWriter(intermediate_panel, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)

    def save_intermediate_panel(self, parsed):
        intermediate_panel_data = self.get_intermediate_panel_data_from_parsed(
            parsed
        )
        self.write_intermediate_panel(intermediate_panel_data)

    def parse_from_intermediate_panel(self, start_date, end_date):
        parsed = []
        rate_dfs = {}

        columns = ['indice_tiempo']
        columns.extend([v for v in self.rates.keys()])

        intermediate_panel_df = self.read_intermediate_panel_dataframe()
        intermediate_panel_df.set_index(['indice_tiempo'], inplace=True)

        if not intermediate_panel_df.empty:
            for k in self.rates.keys():
                rate_dfs[k] = intermediate_panel_df.loc[
                    intermediate_panel_df['type'] == k
                ][['value']]
                rate_dfs[k].rename(columns={'value': k}, inplace=True)
            rates_df = reduce(
                lambda df1, df2: df1.merge(
                    df2, left_on='indice_tiempo', right_on='indice_tiempo'
                ),
                rate_dfs.values(),
            )

            for r in rates_df.to_records():

                if (start_date <= r[0] and
                   r[0] <= end_date):
                    parsed_row = {}

                    columns = ['indice_tiempo']
                    columns.extend([v for v in self.rates.keys()])

                    for index, column in enumerate(columns):
                        parsed_row[column] = r[index]

                    if parsed_row:
                        parsed.append(parsed_row)
        return parsed

    def read_intermediate_panel_dataframe(self):
        intermediate_panel_dataframe = None

        try:
            intermediate_panel_dataframe = pd.read_csv(
                '.libor-intermediate-panel.csv',
                converters={
                    'serie_tiempo': lambda _: _,
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
        Función que evalua si es necesario usar un archivo intermedio.
        En base a esa validación llama a los métodos que serán utilizados
        para obtener y scrapear los datos, y los regresa como un iterable.

        Parameters
        ----------
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date: date
            fecha de fin que va a tomar como referencia el scraper
        """

        parsed = []

        if self.use_intermediate_panel:
            first_date = start_date.strftime("%Y-%m-%d")
            last_date = end_date.strftime("%Y-%m-%d")
            parsed = self.parse_from_intermediate_panel(first_date, last_date)
            parsed = self.preprocess_rows(self.rates, parsed)
        else:
            contents = self.fetch_contents(start_date, end_date)
            parsed = self.parse_contents(contents)
            parsed = self.preprocess_rows(self.rates, parsed)
            self.save_intermediate_panel(parsed)
        return parsed