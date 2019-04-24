from csv import DictWriter
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import reduce

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd


class BCRAScraper:
    """
    Clase que representa un Scraper que funciona para las distintas
    publicaciones del BCRA (Banco Central de la República Argentina).


    Attributes
    ----------
    url : str
        Una cadena que representa una url válida, usada para obtener
        el contenido a ser scrapeado
    use_intermediate_panel : bool
        Flag para indicar si se debe generar o leer un archivo intermedio
        con formato panel

    Methods
    -------
    fetch_contents(start_date, end_date)
        Obtiene los contenidos a ser parseados

    parse_contents(start_date, end_date)
        Recibe un iterable de contenidos y devuelve un iterable con la
        información scrapeada

    run(start_date, end_date)
        Llama a los métodos que obtienen y scrapean los contenidos
        y los devuelve en un iterable
    """

    def __init__(self, url, use_intermediate_panel, *args, **kwargs):
        """
        Parameters
        ----------
        url : str
            Una cadena que representa una url válida, usada para obtener
            el contenido a ser scrapeado. Una URL se considera válida cuando su
            contenido no está vacio.
        use_intermediate_panel : bool
            Flag para indicar si se debe generar o leer un archivo intermedio
            con formato panel
        """
        self.browser_driver = None
        self.url = url
        self.use_intermediate_panel = use_intermediate_panel

        super(BCRAScraper, self).__init__(*args, **kwargs)

    def _create_browser_driver(self):
        """
        Método que crea el navegador y le pasa una opción
        para esconder la visualización del mismo.
        """
        options = webdriver.ChromeOptions()
        options.headless = True

        browser_driver = webdriver.Chrome(options=options)

        return browser_driver

    def get_browser_driver(self):
        """
        Método que verifica la existencia del navegador, en caso
        de que no exista llama a la función que lo crea.
        """
        if not self.browser_driver:
            self.browser_driver = self._create_browser_driver()

        return self.browser_driver

    def fetch_contents(self, start_date, end_date):
        """
        Retorna un iterable donde cada elemento es un String, o una lista
        vacía si no hay contenidos.

        Parameters
        ----------
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date: date
            fecha de fin que va a tomar como referencia el scraper
        Raises
        ------
        NotImplementedError
            si no se encuentra la función o sus parámetros dentro de la clase
        """

        raise NotImplementedError

    def parse_contents(self, start_date, end_date):
        """
        Retorna un iterable donde cada elemento es un String, o una lista
            vacía si no hay contenidos.

        Parameters
        ----------
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date: date
            fecha de fin que va a tomar como referencia el scraper
        Raises
        ------
        NotImplementedError
            si no se encuentra la función o sus parámetros dentro de la clase
        """

        raise NotImplementedError

    def run(self, start_date, end_date):
        """
        Obtiene los contenidos a ser parseados y devuelve un iterable con la
        información scrapeada

        Parameters
        ----------
        start_date : date
            fecha de inicio que va a tomar como referencia el scraper
        end_date: date
            fecha de fin que va a tomar como referencia el scraper
        """

        contents = self.fetch_contents(start_date, end_date)
        parsed = self.parse_contents(contents)

        return parsed


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

        # TODO: validate keys
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
                    (row[rate]).replace(',', '.')
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

    def parse_from_intermediate_panel(self):
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
            parsed = self.parse_from_intermediate_panel()
            parsed = self.preprocess_rows(self.rates, parsed)
        else:
            contents = self.fetch_contents(start_date, end_date)
            parsed = self.parse_contents(contents)

            parsed = self.preprocess_rows(self.rates, parsed)

            self.save_intermediate_panel(parsed)

        return parsed


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

    def fetch_contents(self, start_date):
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

    def parse_contents(self, contents, end_date=datetime.today()):
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
        for k, v in contents.items():

            parsed = self.parse_coin(v, end_date, k)

            if parsed:
                parsed_contents.extend(parsed)

        return parsed_contents

    def parse_coin(self, content, end_date, coin):
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
                datetime.strptime(cols[0].text[5:].strip(), '%d/%m/%Y')

            if row_indice_tiempo <= end_date:
                parsed['moneda'] = coin
                parsed['indice_tiempo'] = cols[0].text[5:].strip()
                parsed['tipo_pase'] = cols[1].text[5:].strip()
                parsed['tipo_cambio'] = cols[2].text[5:].strip()
                parsed_contents.append(parsed)

        return parsed_contents

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
            data = [[v for v in p.values()] for p in parsed]
            columns = ['indice_tiempo', 'coin', 'type', 'value']

            df = pd.DataFrame(
                data,
                columns=['coin', 'indice_tiempo', 'tipo_pase', 'tipo_cambio']
            )
            rate_dfs_panel = pd.DataFrame(data=[], columns=columns)

            pase_df = df[['coin', 'indice_tiempo', 'tipo_pase']].copy()
            pase_df['type'] = 'pase'
            pase_df.rename(columns={'tipo_pase': 'value'}, inplace=True)

            cambio_df = df[['coin', 'indice_tiempo', 'tipo_cambio']].copy()
            cambio_df['type'] = 'cambio'
            cambio_df.rename(columns={'tipo_cambio': 'value'}, inplace=True)

            rate_dfs_panel = rate_dfs_panel.append(pase_df, sort=True)
            rate_dfs_panel = rate_dfs_panel.append(cambio_df, sort=True)

        for r in rate_dfs_panel.to_records():
            _ = r[2].split('/')

            panel_row = {
                'indice_tiempo': '-'.join([_[2], _[1], _[0]]),
                'coin': r[1],
                'type': r[3],
                'value': Decimal(r[4].replace(',', '.')),
            }
            intermediate_panel_data.append(panel_row)

        return intermediate_panel_data

    def save_intermediate_panel(self, parsed):
        intermediate_panel_data = self.get_intermediate_panel_data_from_parsed(
            parsed
        )
        self.write_intermediate_panel(intermediate_panel_data)

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

        contents = self.fetch_contents(start_date)
        parsed = self.parse_contents(contents, end_date)

        self.save_intermediate_panel(parsed)

        return parsed


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

        for k, v in contents.items():

            parsed = self.parse_content(v, k, start_date, end_date)

            if parsed:
                parsed_contents.extend(parsed)

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
                    parsed["moneda"] = coin
                    parsed[headers[0].text] = cols[0].text
                    parsed[headers[1].text] = cols[1].text.strip()
                    parsed[headers[2].text] = cols[2].text.strip()
                    parsed[headers[3].text] = cols[3].text.strip()
                    parsed[headers[4].text] = cols[4].text.strip()
                    parsed_content.append(parsed)

        return parsed_content

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

        contents = self.fetch_contents(self.coins)
        parsed = self.parse_contents(contents, start_date, end_date)

        print(parsed)
        return parsed
