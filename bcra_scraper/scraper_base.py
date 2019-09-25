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
        self.timeout = kwargs.get('timeout', None)
        self.tries = kwargs.get('tries', 1)
        self.use_intermediate_panel = use_intermediate_panel

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

    def preprocess_start_date(self, start_date):
        return start_date

    def preprocess_end_date(self, end_date):
        return end_date

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
        parsed = []
        _parsed = []
        first_missing_part = []
        last_missing_part = []
        start_date = self.preprocess_start_date(start_date)
        start_date = start_date if type(start_date) == date else start_date.date()
        end_date = self.preprocess_end_date(end_date)
        end_date = end_date if type(end_date) == date else end_date.date()

        if self.use_intermediate_panel:
            first_date = start_date.strftime("%Y-%m-%d")
            last_date = end_date.strftime("%Y-%m-%d")

            parsed, original_panel_data = self.parse_from_intermediate_panel(first_date, last_date)

            if start_date < self.get_first_parsed_date(parsed):
                last_date_missing = self.get_first_parsed_date(parsed) - timedelta(days=1)
                first_missing_part = self.get_missing_date_parsed(start_date, last_date_missing)
                first_missing_part = self._preprocess_rows(first_missing_part)
                parsed = self.merge_two_parsed_sections(first_missing_part, parsed)

            if end_date < self.get_last_parsed_date(parsed):
                first_date_missing = self.get_last_parsed_date(parsed) + timedelta(days=1)
                last_missing_part = self.get_missing_date_parsed(first_date_missing, end_date)
                last_missing_part = self._preprocess_rows(last_missing_part)

                parsed = self.merge_two_parsed_sections(parsed, last_missing_part)

            parsed_parts = self.merge_three_parsed_sections(
                first_missing_part, original_panel_data, last_missing_part
            )
            self.save_intermediate_panel(parsed_parts)
            
        else:
            contents = self.fetch_contents(start_date, end_date)
            _parsed = self.parse_contents(contents, start_date, end_date)

            parsed = self._preprocess_rows(_parsed)

        return parsed

    def get_missing_date_parsed(self, start_date, end_date):
        contents = self.fetch_contents(start_date, end_date)
        parsed = self.parse_contents(contents, start_date, end_date)
        return parsed

    def get_first_parsed_date(self, parsed):
        first_parsed_date = (
            parsed[[k for k in parsed.keys()][0]][0]['indice_tiempo']
            if (type(parsed) == dict)
            else parsed[0]['indice_tiempo']
        )
        
        return datetime.strptime(first_parsed_date, '%Y-%m-%d').date()

    def get_last_parsed_date(self, parsed):
        last_parsed_date = (
            parsed[[k for k in parsed.keys()][0]][-1]['indice_tiempo']
            if (type(parsed) == dict)
            else parsed[-1]['indice_tiempo']
        )
        
        return datetime.strptime(last_parsed_date, '%Y-%m-%d').date()

    def merge_three_parsed_sections(self, previous_section, existing_section, next_section):
        merged_sections = {} if type(existing_section) == dict else []

        if type(existing_section) == dict:
            for key in existing_section.keys():
                merged_sections[key] = (
                    (previous_section[key] if type(previous_section) == dict else [])
                    + (existing_section[key] if type(existing_section) == dict else [])
                    + (next_section[key] if type(next_section) == dict else [])
                )
        else:
            merged_sections = (
                previous_section + existing_section + next_section
            )
        
        return merged_sections

    def merge_two_parsed_sections(self, section_one, section_two):
        merged_sections = {} if type(section_one) == dict else []

        if type(section_one) == dict:
            for key in section_one.keys():
                merged_sections[key] = (
                    (section_one[key] if type(section_one) == dict else [])
                    + (section_two[key] if type(section_two) == dict else [])
                )
        else:
            merged_sections = section_one + section_two
        
        return merged_sections
