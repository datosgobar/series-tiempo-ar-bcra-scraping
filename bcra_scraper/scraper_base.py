from datetime import date, datetime, timedelta
from selenium import webdriver
from shutil import which

import string
import random


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

    def __init__(self, url, *args, **kwargs):
        """
        Parameters
        ----------
        url : str
            Una cadena que representa una url válida, usada para obtener
            el contenido a ser scrapeado. Una URL se considera válida cuando su
            contenido no está vacio.
        timeout : int
            Tiempo de intervalo para cada request.
        tries: int
            Cantidad de intentos de request para cada fecha.
        skip_intermediate_panel_data : bool
            Flag para indicar si se debe saltear o leer un archivo intermedio
            con formato panel.
        skip_clean_dates : bool
            Flag para indicar si se deben limpiar las últimas fechas del panel intermedio o no.
        """
        self.browser_driver = None
        self.url = url
        self.timeout = kwargs.get('timeout', None)
        self.tries = kwargs.get('tries', 1)
        self.skip_intermediate_panel_data = kwargs.get('skip_intermediate_panel_data')
        self.skip_clean_last_dates = kwargs.get('skip_clean_last_dates')

    def _create_browser_driver(self):
        """
        Método que crea el navegador y le pasa una opción
        para esconder la visualización del mismo.
        """
        if which("chromedriver"):
            options = webdriver.ChromeOptions()
            options.headless = True

            browser_driver = webdriver.Chrome(options=options)
            if self.timeout:
                browser_driver.set_page_load_timeout(self.timeout)

            return browser_driver
        else:
            print("El driver del navegador no se encuentra en el PATH")

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

    def preprocess_start_date(self, start_date, end_date):
        return start_date

    def preprocess_end_date(self, end_date):
        return end_date

    def clean_last_dates_values_in_panel(self, intermediate_panel_data, start_date, end_date, refetch_end_date):
        """
        Limpia las últimas fechas del panel intermedio, con respecto a la fecha de inicio y fecha de fin,
        que no tengan valores.
        Actualiza y devuelve refetch_end_date, de modo que la fecha de refetch_end_date
        no quede mayor a la fecha end_date.

        Parameters
        ----------
        intermediate_panel_data: dict
            Diccionario que posee la data del panel intermedio.

        start_date: date
            Fecha de inicio que toma como referencia el scraper.

        end_date : date
            Fecha de fin que va a tomar como referencia el scraper.

        refetch_end_date : date
            Fecha de fin que va a tomar como referencia el scraper.
        """
        endure = True
        single_date = end_date
        while endure and single_date >= start_date:
            in_panel, parsed = self.day_content_in_panel(intermediate_panel_data, single_date)
            if in_panel:
                if not self.check_empty_date(parsed):
                    intermediate_panel_data = self.delete_date_from_panel(intermediate_panel_data, single_date)
                    refetch_end_date = self.update_refetch_end_date(refetch_end_date, single_date)
                else:
                    endure = False
            single_date = single_date - timedelta(days=1)
        return intermediate_panel_data, refetch_end_date

    def update_refetch_end_date(self, refetch_end_date, single_date):
        if refetch_end_date == single_date:
            refetch_end_date = refetch_end_date - timedelta(days=1)
        return refetch_end_date

    def run(self, start_date, end_date, refetch_dates_range):
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

        parsed = []
        start_date = self.preprocess_start_date(start_date, end_date)
        end_date = self.preprocess_end_date(end_date)
        fetched_contents = self.empty_fetched_contents()
        refetch_intermediate_panel_data = self.empty_refetch_data()
        intermediate_panel_data = [] if self.skip_intermediate_panel_data else self.parse_from_intermediate_panel()
        refetch_start_date = refetch_dates_range[0] if refetch_dates_range else None
        refetch_end_date = refetch_dates_range[-1] if refetch_dates_range else None

        if not self.skip_clean_last_dates:
            intermediate_panel_data, refetch_end_date = self.clean_last_dates_values_in_panel(intermediate_panel_data, start_date, end_date, refetch_end_date)
        contents = self.fetch_contents(start_date, end_date, intermediate_panel_data, fetched_contents)
        parsed, intermediate_panel_data = self.parse_contents(contents, start_date, end_date, intermediate_panel_data)

        if refetch_dates_range:
            refetched_contents = self.fetch_contents(refetch_start_date, refetch_end_date, refetch_intermediate_panel_data, contents)
            refetched_parsed, refetch_intermediate_panel_data = self.parse_contents(refetched_contents, refetch_start_date, refetch_end_date, refetch_intermediate_panel_data)

            contents.update(refetched_contents)
            parsed = self.merge_parsed(parsed, refetched_parsed)
            intermediate_panel_data = self.merge_parsed(intermediate_panel_data, refetch_intermediate_panel_data)

        if not self.skip_intermediate_panel_data:
            self.save_intermediate_panel(intermediate_panel_data)
        return parsed
