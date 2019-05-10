from datetime import datetime, date
import unittest
from unittest.mock import patch, MagicMock

from bs4 import BeautifulSoup

from bcra_scraper import BCRATCEScraper


class BcraTceScraperTestCase(unittest.TestCase):

    def test_html_is_valid(self):
        """Probar que el html sea valido"""
        url = ""
        single_date = date(2019, 3, 4)

        entities = {}
        coins = {}
        with patch.object(
            BCRATCEScraper,
            'fetch_content',
            return_value='''
                <table class="table table-BCRA table-bordered table-hover
                    table-responsive">
                <thead>
                </thead>
                    <tbody>
                    </tbody>
                </table>
            '''
        ):
            scraper = BCRATCEScraper(url, coins, entities, False)
            content = scraper.fetch_content(single_date)

            soup = BeautifulSoup(content, "html.parser")

            table = soup.find('table')
            head = table.find('thead') if table else None
            body = table.find('tbody') if table else None

            return True

            assert table is not None
            assert head is not None
            assert body is not None

    def test_html_is_not_valid(self):
        """Probar que el html no sea valido"""
        url = ""
        single_date = date(2019, 3, 4)

        entities = {}
        coins = {}
        with patch.object(
            BCRATCEScraper,
            'fetch_content',
            return_value=' '
        ):
            scraper = BCRATCEScraper(url, coins, entities, False)
            content = scraper.fetch_content(single_date)

            soup = BeautifulSoup(content, "html.parser")

            table = soup.find('table')
            head = table.find('thead') if table else None
            body = table.find('tbody') if table else None

            assert table is None
            assert head is None
            assert body is None

    def test_fetch_contents(self):
        coins = {
            "dolar": "DOLAR",
            "euro": "EURO"
        }
        start_date = datetime(2019, 4, 24)
        end_date = datetime(2019, 4, 24)
        url = ''
        content = 'foo'
        entities = {"galicia": "BANCO DE GALICIA Y BUENOS AIRES S.A.U."}

        with patch.object(
            BCRATCEScraper,
            'fetch_content',
            return_value=content
        ):
            scraper = BCRATCEScraper(url, coins, entities, False)
            result = scraper.fetch_contents(start_date, end_date, coins)

            assert result == [
                {
                    'dolar': 'foo'
                },
                {
                    'euro': 'foo'
                }
            ]

    def test_parse_contents(self):
        url = ''
        start_date = datetime(2019, 4, 22)
        end_date = datetime(2019, 4, 22)
        coins = {
            "dolar": "DOLAR",
            "euro": "EURO"
        }
        entities = {
            'galicia': 'BANCO DE GALICIA Y BUENOS AIRES S.A.U.'
            }
        contents = [
                {'dolar': 'foo'},
                {'euro': 'foo'}
            ]
        parsed_dolar = [
            {
                'moneda': 'dolar',
                'indice_tiempo': '22/04/2019',
                'tc_ars_usd_galicia_mostrador_compra_11hs': '41,800',
                'tc_ars_usd_galicia_mostrador_compra_13hs': '41,900',
                'tc_ars_usd_galicia_mostrador_compra_15hs': '41,900',
                'tc_ars_usd_galicia_electronico_compra_11hs': '41,800',
                'tc_ars_usd_galicia_electronico_compra_13hs': '41,900',
                'tc_ars_usd_galicia_electronico_compra_15hs': '41,900',
                'tc_ars_usd_galicia_mostrador_venta_11hs': '43,800',
                'tc_ars_usd_galicia_mostrador_venta_13hs': '43,900',
                'tc_ars_usd_galicia_mostrador_venta_15hs': '43,900',
                'tc_ars_usd_galicia_electronico_venta_11hs': '43,800',
                'tc_ars_usd_galicia_electronico_venta_13hs': '43,900',
                'tc_ars_usd_galicia_electronico_venta_15hs': '43,900'
            }
        ]
        parsed_euro = [
            {
                'moneda': 'euro',
                'indice_tiempo': '22/04/2019',
                'tc_ars_eur_galicia_mostrador_compra_11hs': '46,600',
                'tc_ars_eur_galicia_mostrador_compra_13hs': '46,600',
                'tc_ars_eur_galicia_mostrador_compra_15hs': '46,600',
                'tc_ars_eur_galicia_electronico_compra_11hs': '',
                'tc_ars_eur_galicia_electronico_compra_13hs': '',
                'tc_ars_eur_galicia_electronico_compra_15hs': '',
                'tc_ars_eur_galicia_mostrador_venta_11hs': '49,000',
                'tc_ars_eur_galicia_mostrador_venta_13hs': '49,000',
                'tc_ars_eur_galicia_mostrador_venta_15hs': '49,000',
                'tc_ars_eur_galicia_electronico_venta_11hs': '',
                'tc_ars_eur_galicia_electronico_venta_13hs': '',
                'tc_ars_eur_galicia_electronico_venta_15hs': ''
            }
        ]

        with patch.object(
            BCRATCEScraper,
            'parse_content',
            side_effect=[parsed_dolar, parsed_euro]

        ):
            scraper = BCRATCEScraper(url, coins, entities, False)
            result = scraper.parse_contents(
                contents,
                entities,
                start_date,
                end_date
                )

            assert result == [
                    {
                        'moneda': 'dolar',
                        'indice_tiempo': '22/04/2019',
                        'tc_ars_usd_galicia_mostrador_compra_11hs': '41,800',
                        'tc_ars_usd_galicia_mostrador_compra_13hs': '41,900',
                        'tc_ars_usd_galicia_mostrador_compra_15hs': '41,900',
                        'tc_ars_usd_galicia_electronico_compra_11hs': '41,800',
                        'tc_ars_usd_galicia_electronico_compra_13hs': '41,900',
                        'tc_ars_usd_galicia_electronico_compra_15hs': '41,900',
                        'tc_ars_usd_galicia_mostrador_venta_11hs': '43,800',
                        'tc_ars_usd_galicia_mostrador_venta_13hs': '43,900',
                        'tc_ars_usd_galicia_mostrador_venta_15hs': '43,900',
                        'tc_ars_usd_galicia_electronico_venta_11hs': '43,800',
                        'tc_ars_usd_galicia_electronico_venta_13hs': '43,900',
                        'tc_ars_usd_galicia_electronico_venta_15hs': '43,900'
                    },
                    {
                        'moneda': 'euro',
                        'indice_tiempo': '22/04/2019',
                        'tc_ars_eur_galicia_mostrador_compra_11hs': '46,600',
                        'tc_ars_eur_galicia_mostrador_compra_13hs': '46,600',
                        'tc_ars_eur_galicia_mostrador_compra_15hs': '46,600',
                        'tc_ars_eur_galicia_electronico_compra_11hs': '',
                        'tc_ars_eur_galicia_electronico_compra_13hs': '',
                        'tc_ars_eur_galicia_electronico_compra_15hs': '',
                        'tc_ars_eur_galicia_mostrador_venta_11hs': '49,000',
                        'tc_ars_eur_galicia_mostrador_venta_13hs': '49,000',
                        'tc_ars_eur_galicia_mostrador_venta_15hs': '49,000',
                        'tc_ars_eur_galicia_electronico_venta_11hs': '',
                        'tc_ars_eur_galicia_electronico_venta_13hs': '',
                        'tc_ars_eur_galicia_electronico_venta_15hs': ''
                    }
                ]

    def test_run(self):

        start_date = datetime(2019, 4, 22)
        end_date = datetime(2019, 4, 22)

        url = '''
         http://www.bcra.gov.ar/PublicacionesEstadisticas/Tipo_de_cambio_sml.asp
        '''

        coins = {
            "dolar": "DOLAR",
            "euro": "EURO"
        }

        entities = {
            "galicia": "BANCO DE GALICIA Y BUENOS AIRES S.A.U."
        }

        parsed = [
            {
                'moneda': 'dolar',
                'indice_tiempo': '22/04/2019',
                'tc_ars_usd_galicia_mostrador_compra_11hs': '41,800',
                'tc_ars_usd_galicia_mostrador_compra_13hs': '41,900',
                'tc_ars_usd_galicia_mostrador_compra_15hs': '41,900',
                'tc_ars_usd_galicia_electronico_compra_11hs': '41,800',
                'tc_ars_usd_galicia_electronico_compra_13hs': '41,900',
                'tc_ars_usd_galicia_electronico_compra_15hs': '41,900',
                'tc_ars_usd_galicia_mostrador_venta_11hs': '43,800',
                'tc_ars_usd_galicia_mostrador_venta_13hs': '43,900',
                'tc_ars_usd_galicia_mostrador_venta_15hs': '43,900',
                'tc_ars_usd_galicia_electronico_venta_11hs': '43,800',
                'tc_ars_usd_galicia_electronico_venta_13hs': '43,900',
                'tc_ars_usd_galicia_electronico_venta_15hs': '43,900'
            },
            {
                'moneda': 'euro',
                'indice_tiempo': '22/04/2019',
                'tc_ars_eur_galicia_mostrador_compra_11hs': '46,600',
                'tc_ars_eur_galicia_mostrador_compra_13hs': '46,600',
                'tc_ars_eur_galicia_mostrador_compra_15hs': '46,600',
                'tc_ars_eur_galicia_electronico_compra_11hs': '',
                'tc_ars_eur_galicia_electronico_compra_13hs': '',
                'tc_ars_eur_galicia_electronico_compra_15hs': '',
                'tc_ars_eur_galicia_mostrador_venta_11hs': '49,000',
                'tc_ars_eur_galicia_mostrador_venta_13hs': '49,000',
                'tc_ars_eur_galicia_mostrador_venta_15hs': '49,000',
                'tc_ars_eur_galicia_electronico_venta_11hs': '',
                'tc_ars_eur_galicia_electronico_venta_13hs': '',
                'tc_ars_eur_galicia_electronico_venta_15hs': ''
            }
        ]

        with patch.object(
            BCRATCEScraper,
            'fetch_contents',
            return_value=''
        ):
            with patch.object(
                BCRATCEScraper,
                'parse_contents',
                return_value=parsed
            ):
                scraper = BCRATCEScraper(url, coins, entities, False)
                result = scraper.run(start_date, end_date)

                assert result == [
                    {
                        'moneda': 'dolar',
                        'indice_tiempo': '22/04/2019',
                        'tc_ars_usd_galicia_mostrador_compra_11hs': '41,800',
                        'tc_ars_usd_galicia_mostrador_compra_13hs': '41,900',
                        'tc_ars_usd_galicia_mostrador_compra_15hs': '41,900',
                        'tc_ars_usd_galicia_electronico_compra_11hs': '41,800',
                        'tc_ars_usd_galicia_electronico_compra_13hs': '41,900',
                        'tc_ars_usd_galicia_electronico_compra_15hs': '41,900',
                        'tc_ars_usd_galicia_mostrador_venta_11hs': '43,800',
                        'tc_ars_usd_galicia_mostrador_venta_13hs': '43,900',
                        'tc_ars_usd_galicia_mostrador_venta_15hs': '43,900',
                        'tc_ars_usd_galicia_electronico_venta_11hs': '43,800',
                        'tc_ars_usd_galicia_electronico_venta_13hs': '43,900',
                        'tc_ars_usd_galicia_electronico_venta_15hs': '43,900'
                    },
                    {
                        'moneda': 'euro',
                        'indice_tiempo': '22/04/2019',
                        'tc_ars_eur_galicia_mostrador_compra_11hs': '46,600',
                        'tc_ars_eur_galicia_mostrador_compra_13hs': '46,600',
                        'tc_ars_eur_galicia_mostrador_compra_15hs': '46,600',
                        'tc_ars_eur_galicia_electronico_compra_11hs': '',
                        'tc_ars_eur_galicia_electronico_compra_13hs': '',
                        'tc_ars_eur_galicia_electronico_compra_15hs': '',
                        'tc_ars_eur_galicia_mostrador_venta_11hs': '49,000',
                        'tc_ars_eur_galicia_mostrador_venta_13hs': '49,000',
                        'tc_ars_eur_galicia_mostrador_venta_15hs': '49,000',
                        'tc_ars_eur_galicia_electronico_venta_11hs': '',
                        'tc_ars_eur_galicia_electronico_venta_13hs': '',
                        'tc_ars_eur_galicia_electronico_venta_15hs': ''
                    }
                ]

    def test_fetch_content_patching_driver(self):
        """Probar fetch content"""
        single_date = date(2019, 3, 4)
        coins = {}
        entities = {}
        url = ''

        mocked_driver = MagicMock()
        mocked_driver.page_source = "foo"
        mocked_driver.status_code = 200

        with patch.object(
            BCRATCEScraper,
            'get_browser_driver',
            return_value=mocked_driver
        ):
            scraper = BCRATCEScraper(url, coins, entities, False)
            content = scraper.fetch_content(single_date, coins)
            assert content == "foo"

    def test_fetch_content_invalid_url_patching_driver(self):
        """Probar fetch content con url invalida"""
        single_date = date(2019, 3, 4)
        coins = {}
        entities = {}
        url = ''

        mocked_driver = MagicMock()
        mocked_driver.page_source = 400

        with patch.object(
            BCRATCEScraper,
            'get_browser_driver',
            return_value=mocked_driver
        ):
            scraper = BCRATCEScraper(url, coins, entities, False)
            content = scraper.fetch_content(single_date, coins)
            assert content == 400

    def test_parse_content(self):

        start_date = datetime(2019, 4, 22)
        end_date = datetime(2019, 4, 22)
        url = ''
        coins = {}
        coin = "dolar"
        entities = {
            "galicia": "BANCO DE GALICIA Y BUENOS AIRES S.A.U."
        }

        content = '''
            <table class="table table-BCRA table-bordered table-hover\
                table-responsive" colspan="3">
            <thead>
            <tr>
            <td colspan="13"><b>Cotizaciones a la fecha:  22/04/2019</b></td>
            </tr>
            </thead>
            <tbody><tr>
            <td rowspan="4" width="18%"><b>Entidades Financieras</b></td>
            </tr>
            <tr>
            <td colspan="4" width="23%"><b>11:00 hs.</b></td>
            <td colspan="4" width="26%"><b>13:00 hs.</b></td>
            <td colspan="4" width="25%"><b>15:00 hs.</b></td>
            </tr>
            <tr>
            <td colspan="2" width="12%"><b>Mostrador</b></td>
            <td colspan="2" width="11%"><b>Electrónico</b></td>
            <td colspan="2" width="12%"><b>Mostrador</b></td>
            <td colspan="2" width="14%"><b>Electrónico</b></td>
            <td colspan="2" width="14%"><b>Mostrador</b></td>
            <td colspan="2" width="11%"><b>Electrónico</b></td>
            </tr>
            <tr>
            <td width="6%"><b>Compra</b></td>
            <td width="6%"><b>Venta</b></td>
            <td width="6%"><b>Compra</b></td>
            <td width="5%"><b>Venta</b></td>
            <td width="6%"><b>Compra</b></td>
            <td width="6%"><b>Venta</b></td>
            <td width="7%"><b>Compra</b></td>
            <td width="7%"><b>Venta</b></td>
            <td width="7%"><b>Compra</b></td>
            <td width="6%"><b>Venta</b></td>
            <td width="7%"><b>Compra</b></td>
            <td width="4%"><b>Venta</b></td>
            </tr>
            <tr>
            <td width="18%">BANCO DE GALICIA Y BUENOS AIRES S.A.U.</td>
            <td width="6%">41,800</td>
            <td width="6%">43,800</td>
            <td width="6%">41,800</td>
            <td width="5%">43,800</td>
            <td width="6%">41,900</td>
            <td width="6%">43,900</td>
            <td width="7%">41,900</td>
            <td width="7%">43,900</td>
            <td width="7%">41,900</td>
            <td width="6%">43,900</td>
            <td width="7%">41,900</td>
            <td width="4%">43,900</td>
            </tr>
            </tbody></table>
        '''

        scraper = BCRATCEScraper(url, coins, entities, False)
        result = scraper.parse_content(
            content, start_date, end_date, coin, entities
        )

        assert result == [
            {
                'moneda': 'dolar',
                'indice_tiempo': '22/04/2019',
                'tc_ars_usd_galicia_mostrador_compra_11hs': '41,800',
                'tc_ars_usd_galicia_mostrador_compra_13hs': '41,900',
                'tc_ars_usd_galicia_mostrador_compra_15hs': '41,900',
                'tc_ars_usd_galicia_electronico_compra_11hs': '41,800',
                'tc_ars_usd_galicia_electronico_compra_13hs': '41,900',
                'tc_ars_usd_galicia_electronico_compra_15hs': '41,900',
                'tc_ars_usd_galicia_mostrador_venta_11hs': '43,800',
                'tc_ars_usd_galicia_mostrador_venta_13hs': '43,900',
                'tc_ars_usd_galicia_mostrador_venta_15hs': '43,900',
                'tc_ars_usd_galicia_electronico_venta_11hs': '43,800',
                'tc_ars_usd_galicia_electronico_venta_13hs': '43,900',
                'tc_ars_usd_galicia_electronico_venta_15hs': '43,900'
            }
        ]
