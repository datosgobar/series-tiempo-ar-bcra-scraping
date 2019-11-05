from datetime import date, datetime
from decimal import Decimal
import unittest
from unittest.mock import patch, MagicMock
from unittest import mock
import io
import json
import pandas as pd

from bs4 import BeautifulSoup

from bcra_scraper import BCRALiborScraper
from bcra_scraper.utils import get_most_recent_previous_business_day
from bcra_scraper.bcra_scraper import validate_url_config
from bcra_scraper.bcra_scraper import validate_url_has_value
from bcra_scraper.bcra_scraper import validate_libor_rates_config
from bcra_scraper.bcra_scraper import validate_libor_rates_has_values
from bcra_scraper.exceptions import InvalidConfigurationError
from bcra_scraper.bcra_scraper import read_config


class BcraLiborScraperTestCase(unittest.TestCase):

    def test_get_last_business_day(self):
        """probar que la fecha obtenida sea correcta"""
        assert date(2019, 3, 15) == get_most_recent_previous_business_day(
            date(2019, 3, 18)
        )
        assert date(2019, 3, 18) == get_most_recent_previous_business_day(
            date(2019, 3, 19)
        )
        assert date(2019, 3, 22) == get_most_recent_previous_business_day(
            date(2019, 3, 24)
        )

    def test_fetch_contents_with_valid_dates(self):
        """comprueba, dependiendo de un rango de fechas,
        la cantidad de contenidos"""
        url = "http://www.bcra.gov.ar/PublicacionesEstadisticas/libor.asp"

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }
        with patch.object(
            BCRALiborScraper,
            'fetch_day_content',
            return_value=['a', 'b', 'c', 'd', 'e', 'f', 'g']
        ):

            scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)
            start_day = date(2019, 3, 4)
            end_day = date(2019, 3, 10)

            contents = scraper.fetch_contents(start_day, end_day)

            assert len(contents) == 7

    def test_fetch_content_with_invalid_dates(self):
        """comprueba, dependiendo de un rango invalido de fechas,
        que el contenido esté vacío."""
        url = "http://www.bcra.gov.ar/PublicacionesEstadisticas/libor.asp"

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)
        start_day = date(2019, 3, 10)
        end_day = date(2019, 3, 4)

        contents = scraper.fetch_contents(start_day, end_day)

        assert contents == []

    def test_html_is_not_valid(self):
        """Probar que el html no sea valido"""
        url = ""

        rates = {}

        with patch.object(
            BCRALiborScraper,
            'fetch_day_content',
            return_value='''
                <table class="table table-BCRA table-bordered table-hover
                    table-responsive">
                    <thead></thead>
                </table>
            '''
        ):
            scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)
            content_date = date.today()
            content = scraper.fetch_day_content(content_date)

            soup = BeautifulSoup(content, "html.parser")

            table = soup.find('table')
            head = table.find('thead') if table else None
            body = table.find('tbody') if table else None

            assert table is not None
            assert head is not None
            assert body is None

    def test_html_is_valid(self):
        """Probar que el html sea valido"""
        url = ""
        single_date = date(2019, 3, 4)

        rates = {}
        with patch.object(
            BCRALiborScraper,
            'fetch_day_content',
            return_value='''
                <table class="table table-BCRA table-bordered table-hover
                    table-responsive">
                <thead></thead>
                <tbody></tbody>
                </table>
            '''
        ):
            scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)
            content = scraper.fetch_day_content(single_date)

            soup = BeautifulSoup(content, "html.parser")

            table = soup.find('table')
            head = table.find('thead') if table else None
            body = table.find('tbody') if table else None

            assert table is not None
            assert head is not None
            assert body is not None

    def test_parse_for_empty_contents(self):
        start_date = datetime(2019, 4, 24)
        end_date = datetime(2019, 4, 24)

        url = ""

        rates = {}
        with patch.object(
            BCRALiborScraper,
            'parse_day_content',
            return_value={}
        ):
            scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)
            contents = []
            parsed = scraper.parse_contents(contents, start_date, end_date)

            assert parsed == []

    def test_parse_for_non_empty_contents(self):
        start_date = datetime(2019, 4, 24)
        end_date = datetime(2019, 4, 24)

        url = "http://www.bcra.gov.ar/PublicacionesEstadisticas/libor.asp"

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        rows = {
            'indice_tiempo': '2019-03-15',
            '30': '2,481750',
            '60': '2,558380',
            '90': '2,625250',
            '180': '2,671750',
            '360': '2,840500'
        }

        with patch.object(
            BCRALiborScraper,
            'parse_day_content',
            return_value=rows
        ):
            scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)

            contents = [{'indice_tiempo': start_date,
            'content': '''
            <table class="table table-BCRA table-bordered table-hover
                table-responsive">
            <thead>
                <tr>
                    <th colspan="2"
                    align="left">Tasa LIBOR al:  15/03/2019</th>
                </tr>
                <tr>
                    <th>Plazo en días</th>
                    <th>Tasa (T.N.A. %)</th>
                </tr>
            </thead>
            <tbody>
            <tr>
                <td>30</td>
                <td>2,481750</td>
            </tr>
            <tr>
                <td>60</td>
                <td>2,558380</td>
            </tr>
            <tr>
                <td>90</td>
                <td>2,625250</td>
            </tr>
            <tr>
                <td>180</td>
                <td>2,671750</td>
            </tr>
            <tr>
                <td>360</td>
                <td>2,840500</td>
            </tr>
            </tbody>
            </table>
            '''}]

            parsed = scraper.parse_contents(contents, start_date, end_date)

            assert parsed == [
                {
                    'indice_tiempo': '2019-03-15',
                    '30': '2,481750',
                    '60': '2,558380',
                    '90': '2,625250',
                    '180': '2,671750',
                    '360': '2,840500'
                }
            ]

    def test_scraper_with_empty_table(self):

        single_date = datetime(2019, 4, 24)

        url = "http://www.bcra.gov.ar/PublicacionesEstadisticas/libor.asp"

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        content = '''
        <table class="table table-BCRA table-bordered table-hover
        table-responsive">
            <thead>
                <tr><th>No existen registros</th></tr>
            </thead>
        </table>
        '''
        scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)

        result = scraper.parse_day_content(single_date, content)

        assert result == {
            '360': '',
            '180': '',
            '90': '',
            '60': '',
            '30': '',
            'indice_tiempo': datetime(2019, 4, 24, 0, 0)
            }

    def test_scraper_with_valid_table(self):

        single_date = datetime(2019, 3, 15)

        url = "http://www.bcra.gov.ar/PublicacionesEstadisticas/libor.asp"

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        content = {'indice_tiempo': single_date,
        'content': '''
            <table class="table table-BCRA table-bordered table-hover
                table-responsive">
            <thead>
                <tr>
                    <th colspan="2"
                    align="left">Tasa LIBOR al:  15/03/2019</th>
                </tr>
                <tr>
                    <th>Plazo en días</th>
                    <th>Tasa (T.N.A. %)</th>
                </tr>
            </thead>
            <tbody>
            <tr>
                <td>30</td>
                <td>2,481750</td>
            </tr>
            <tr>
                <td>60</td>
                <td>2,558380</td>
            </tr>
            <tr>
                <td>90</td>
                <td>2,625250</td>
            </tr>
            <tr>
                <td>180</td>
                <td>2,671750</td>
            </tr>
            <tr>
                <td>360</td>
                <td>2,840500</td>
            </tr>
            </tbody>
            </table>
        '''}
        scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)

        result = scraper.parse_day_content(single_date, content['content'])

        assert result.get('indice_tiempo') == single_date
        assert result.get('30') == '2,481750'
        assert result.get('60') == '2,558380'
        assert result.get('90') == '2,625250'
        assert result.get('180') == '2,671750'
        assert result.get('360') == '2,840500'

    def test_preprocessed_rows(self):

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        rows = [
            {
                'indice_tiempo': '2019-04-11',
                '30': '2,472630', '60': '2,536750',
                '90': '2,596750', '180': '2,631250',
                '360': '2,734130'
            }
        ]
        scraper = BCRALiborScraper(False, rates, intermediate_panel_path=None, use_intermediate_panel=False)

        result = scraper.preprocess_rows(rates, rows)

        assert result == [
            {
                'indice_tiempo': date.fromisoformat('2019-04-11'),
                'libor_30_dias': Decimal('0.0247263'),
                'libor_60_dias': Decimal('0.0253675'),
                'libor_90_dias': Decimal('0.0259675'),
                'libor_180_dias': Decimal('0.0263125'),
                'libor_360_dias': Decimal('0.0273413')
            }
        ]

    def test_preprocessed_header(self):

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        scraper = BCRALiborScraper(False, rates, intermediate_panel_path=None, use_intermediate_panel=False)

        result = scraper.preprocess_header(rates)

        assert result == [
            'indice_tiempo',
            'libor_30_dias',
            'libor_60_dias',
            'libor_90_dias',
            'libor_180_dias',
            'libor_360_dias'
        ]

    def test_get_intermediate_panel_date_from_parsed(self):

        parsed = [
            {
                'indice_tiempo': date.fromisoformat('2019-04-11'),
                'libor_30_dias': Decimal('0.0247263'),
                'libor_60_dias': Decimal('0.0253675'),
                'libor_90_dias': Decimal('0.0259675'),
                'libor_180_dias': Decimal('0.0263125'),
                'libor_360_dias': Decimal('0.0273413')
            }
        ]

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        scraper = BCRALiborScraper(False, rates, intermediate_panel_path=None, use_intermediate_panel=False)

        result = scraper.get_intermediate_panel_data_from_parsed(parsed)

        assert result == [
            {
                'indice_tiempo': date.fromisoformat('2019-04-11'),
                'type': '360', 'value': Decimal('0.0273413')
            },
            {
                'indice_tiempo': date.fromisoformat('2019-04-11'),
                'type': '180', 'value': Decimal('0.0263125')
            },
            {
                'indice_tiempo': date.fromisoformat('2019-04-11'),
                'type': '90', 'value': Decimal('0.0259675')
            },
            {
                'indice_tiempo': date.fromisoformat('2019-04-11'),
                'type': '60', 'value': Decimal('0.0253675')
            },
            {
                'indice_tiempo': date.fromisoformat('2019-04-11'),
                'type': '30', 'value': Decimal('0.0247263')
            }
        ]

    def test_get_intermediate_panel_data_from_empty_parsed(self):
        parsed = []

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        scraper = BCRALiborScraper(False, rates, intermediate_panel_path=None, use_intermediate_panel=False)

        result = scraper.get_intermediate_panel_data_from_parsed(parsed)

        assert result == []

    def test_run_not_using_intermediate_panel(self):

        start_date = datetime(2019, 4, 24)
        end_date = datetime(2019, 4, 24)

        url = '''
         http://www.bcra.gov.ar/PublicacionesEstadisticas/Tipo_de_cambio_sml.asp
        '''

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        parsed = [
            {
                'indice_tiempo': '2019-04-24',
                '30': '0.0248338',
                '60': '0.0254163',
                '90': '0.0258638',
                '180': '0.0261975',
                '360': '0.0272513'
            }
        ]

        with patch.object(BCRALiborScraper, 'fetch_contents', return_value=''):
            with patch.object(
                BCRALiborScraper,
                'parse_contents',
                return_value=parsed
            ):
                with patch.object(
                    BCRALiborScraper,
                    'preprocess_rows',
                    return_value=parsed
                ):
                    with patch.object(
                        BCRALiborScraper,
                        'save_intermediate_panel',
                        return_value=''
                    ):

                        scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)
                        result = scraper.run(start_date, end_date)

                        assert result == [
                            {
                                'indice_tiempo': '2019-04-24',
                                '30': '0.0248338',
                                '60': '0.0254163',
                                '90': '0.0258638',
                                '180': '0.0261975',
                                '360': '0.0272513'
                            }
                        ]

    def test_run_using_intermediate_panel(self):

        start_date = datetime(2019, 4, 24)
        end_date = datetime(2019, 4, 24)

        url = '''
         http://www.bcra.gov.ar/PublicacionesEstadisticas/Tipo_de_cambio_sml.asp
        '''

        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        parsed = [
            {
                'indice_tiempo': '2019-04-24',
                'libor_30_dias': Decimal('0.0248588'),
                'libor_60_dias': Decimal('0.0253013'),
                'libor_90_dias': Decimal('0.025790'),
                'libor_180_dias': Decimal('0.026120'),
                'libor_360_dias': Decimal('0.027130')
            },
        ]

        with patch.object(BCRALiborScraper, 'fetch_contents', return_value=''):
            with patch.object(
                BCRALiborScraper,
                'parse_from_intermediate_panel',
                return_value=parsed
            ):
                scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=True)
                result = scraper.run(start_date, end_date)

                assert result == [
                    {
                        'indice_tiempo': '2019-04-24',
                        'libor_30_dias': Decimal('0.0248588'),
                        'libor_60_dias': Decimal('0.0253013'),
                        'libor_90_dias': Decimal('0.025790'),
                        'libor_180_dias': Decimal('0.026120'),
                        'libor_360_dias': Decimal('0.027130')
                    }
                ]

    def test_read_valid_configuration(self):
        """Validar que el formato del archivo sea Json"""
        dict_config = "{"

        with mock.patch(
                'builtins.open',
                return_value=io.StringIO(dict_config)):

            with self.assertRaises(InvalidConfigurationError):
                read_config("config_general.json", "cmd")

    def test_rates_not_in_config(self):
        """Validar error en caso de que no exista
        el valor dentro del archivo de configuracion"""
        url = ''
        parsed = 'foo'
        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }

        scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)

        with self.assertRaises(InvalidConfigurationError):
            scraper.rates_config_validator(parsed, rates)

    def test_libor_configuration_has_url(self):
        """Validar la existencia de la clave url dentro de
        la configuración de libor"""
        dict_config = {'libor': {'foo': 'bar'}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config_general.json", "libor")
                validate_url_config(config)

    def test_libor_url_has_value(self):
        """Validar que la url sea valida"""
        dict_config = {'libor': {'url': ''}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config_general.json", "libor")
                validate_url_has_value(config)

    def test_libor_configuration_has_rates(self):
        """Validar la existencia de la clave rates dentro de
        la configuración de libor"""
        dict_config = {'libor': {'foo': 'bar'}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config_general.json", "libor")
                validate_libor_rates_config(config)

    def test_libor_rates_has_values(self):
        """Validar la existencia de valores dentro de rates"""
        dict_config = {'libor': {'rates': {}}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config_general.json", "libor")
                validate_libor_rates_has_values(config)

    def test_fetch_day_content_patching_driver(self):
        """Probar fetch day content"""
        single_date = date(2019, 3, 4)
        rates = {}
        url = ''

        mocked_driver = MagicMock()
        mocked_driver.page_source = "foo"
        mocked_driver.status_code = 200

        with patch.object(
            BCRALiborScraper,
            'get_browser_driver',
            return_value=mocked_driver
        ):
            scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False )
            content = scraper.fetch_day_content(single_date)
            assert content['content'] == "foo"

    def test_fetch_day_content_invalid_url_patching_driver(self):
        """Probar fetch day content con url invalida"""
        single_date = date(2019, 3, 4)
        rates = {}
        url = ''

        mocked_driver = MagicMock()
        mocked_driver.page_source = 400

        with patch.object(
            BCRALiborScraper,
            'get_browser_driver',
            return_value=mocked_driver
        ):
            scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=False)
            content = scraper.fetch_day_content(single_date)
            assert content['content'] == 400

    def test_parse_from_intermediate_panel(self):
        start_date = '2019-03-15'
        end_date = '2019-03-15'
        """Probar parseo desde el archivo intermedio"""
        rates = {
            "30": "libor_30_dias",
            "60": "libor_60_dias",
            "90": "libor_90_dias",
            "180": "libor_180_dias",
            "360": "libor_360_dias"
        }
        url = ''

        intermediate_panel_df = MagicMock()
        intermediate_panel_df = {
            'indice_tiempo': [
                '2019-03-15',
                '2019-03-15',
                '2019-03-15',
                '2019-03-15',
                '2019-03-15'
            ],
            'type': [
                '30', '60', '90', '180', '360'
            ],
            'value': [
                '0.0248175', '0.0255838', '0.0262525', '0.0267175', '0.028405'
            ]
        }

        with patch.object(
            BCRALiborScraper,
            'read_intermediate_panel_dataframe',
            return_value=pd.DataFrame(data=intermediate_panel_df)
        ):
            scraper = BCRALiborScraper(url, rates, intermediate_panel_path=None, use_intermediate_panel=True)
            content = scraper.parse_from_intermediate_panel(
                start_date, end_date,
                )

            assert content == [
                {
                    'indice_tiempo': '2019-03-15',
                    'libor_30_dias': '0.0248175',
                    'libor_60_dias': '0.0255838',
                    'libor_90_dias': '0.0262525',
                    'libor_180_dias': '0.0267175',
                    'libor_360_dias': '0.028405'
                }
            ]
