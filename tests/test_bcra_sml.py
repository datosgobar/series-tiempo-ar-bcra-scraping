from datetime import datetime, date

import unittest
from unittest import mock
from unittest.mock import patch, MagicMock
from decimal import Decimal

import pandas as pd
import io
import json

from bs4 import BeautifulSoup

from bcra_scraper import BCRASMLScraper
from bcra_scraper.bcra_scraper import validate_url_config
from bcra_scraper.bcra_scraper import validate_url_has_value
from bcra_scraper.bcra_scraper import validate_coins_key_config
from bcra_scraper.bcra_scraper import validate_coins_key_has_values
from bcra_scraper.exceptions import InvalidConfigurationError
from bcra_scraper.bcra_scraper import read_config


class BcraSmlScraperTestCase(unittest.TestCase):

    def test_html_is_valid(self):
        """Probar que el html sea valido"""
        url = ""
        single_date = date(2019, 3, 4)

        coins = {}
        with patch.object(
            BCRASMLScraper,
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
            scraper = BCRASMLScraper(url, coins, False)
            content = scraper.fetch_content(single_date)

            soup = BeautifulSoup(content, "html.parser")

            table = soup.find('table')
            head = table.find('thead') if table else None
            body = table.find('tbody') if table else None

            assert table is not None
            assert head is not None
            assert body is not None

    def test_html_is_not_valid(self):
        """Probar que el html no sea valido"""
        url = ""
        single_date = date(2019, 3, 4)

        coins = {}
        with patch.object(
            BCRASMLScraper,
            'fetch_content',
            return_value=' '
        ):
            scraper = BCRASMLScraper(url, coins, False)
            content = scraper.fetch_content(single_date)

            soup = BeautifulSoup(content, "html.parser")

            table = soup.find('table')
            head = table.find('thead') if table else None
            body = table.find('tbody') if table else None

            assert table is None
            assert head is None
            assert body is None

    def test_fetch_contents(self):
        url = ''

        coins = {
            "peso_uruguayo": "Peso Uruguayo",
            "real": "Real"
        }

        content = 'foo'

        with patch.object(
            BCRASMLScraper,
            'fetch_content',
            return_value=content
        ):
            scraper = BCRASMLScraper(url, coins, False)
            result = scraper.fetch_contents(coins)

            assert result == {
                'peso_uruguayo': 'foo',
                'real': 'foo'
            }

    def test_parse_content_with_valid_content(self):

        start_date = datetime(2019, 4, 24)
        end_date = datetime(2019, 4, 24)
        coin = "peso_uruguayo"

        content = '''
        <table colspan="3" class="table table-BCRA table-bordered
        table-hover table-responsive">
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>Tipo de cambio de Referencia</th>
                    <th>Tipo de cambio URINUSCA</th>
                    <th>Tipo de cambio SML Peso Uruguayo</th>
                    <th>Tipo de cambio SML Uruguayo Peso</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>24/04/2019</td>
                    <td>43,47830</td>
                    <td>34,51000</td>
                    <td>1,25990</td>
                    <td>0,79375</td>
                </tr>
            </tbody>
        </table>
        '''

        scraper = BCRASMLScraper(False, coin, False)
        result = scraper.parse_content(
                content, coin, start_date, end_date
            )

        assert result == [
            {
                'coin': 'peso_uruguayo',
                'indice_tiempo': '24/04/2019',
                'Tipo de cambio de Referencia': '43,47830',
                'Tipo de cambio URINUSCA': '34,51000',
                'Tipo de cambio SML Peso Uruguayo': '1,25990',
                'Tipo de cambio SML Uruguayo Peso': '0,79375'
                }
            ]

    def test_parse_content_with_non_valid_content(self):

        start_date = datetime(2019, 4, 11)
        end_date = datetime(2019, 4, 11)
        coin = "peso_uruguayo"

        content = '''
        <table colspan="3" class="table table-BCRA table-bordered
        table-hover table-responsive">
            <thead>
            </thead>
            <tbody>
            </tbody>
        </table>
        '''

        scraper = BCRASMLScraper(False, coin, False)
        result = scraper.parse_content(
                content, coin, start_date, end_date
            )

        assert result == []

    def test_parse_contents(self):
        url = ''

        contents = {
            'peso_uruguayo': 'foo',
            'real': 'foo'
        }

        start_date = datetime(2019, 4, 24)
        end_date = datetime(2019, 4, 24)

        coins = {
            "peso_uruguayo": "Peso Uruguayo",
            "real": "Real"
        }

        content_peso = [
            {
                'coin': 'peso_uruguayo',
                'indice_tiempo': '24/04/2019',
                'Tipo de cambio de Referencia': '43,47830',
                'Tipo de cambio URINUSCA': '34,51000',
                'Tipo de cambio SML Peso Uruguayo': '1,25990',
                'Tipo de cambio SML Uruguayo Peso': '0,79375'
            }
        ]

        content_real = [
            {
                'coin': 'real',
                'indice_tiempo': '24/04/2019',
                'Tipo de cambio de Referencia': '43,47830',
                'Tipo de cambio PTAX': '3,96270',
                'Tipo de cambio SML Peso Real': '10,97190',
                'Tipo de cambio SML Real Peso': '0,09115'
            }
        ]

        with patch.object(
            BCRASMLScraper,
            'parse_content',
            side_effect=[content_peso, content_real]
        ):
            scraper = BCRASMLScraper(url, coins, False)

            result = scraper.parse_contents(contents, start_date, end_date)

            assert result == {
                'peso_uruguayo':
                [
                    {
                        'Tipo de cambio de Referencia': '43,47830',
                        'Tipo de cambio URINUSCA': '34,51000',
                        'Tipo de cambio SML Peso Uruguayo': '1,25990',
                        'Tipo de cambio SML Uruguayo Peso': '0,79375',
                        'indice_tiempo': '24/04/2019'
                    }
                ],
                'real':
                [
                    {
                        'Tipo de cambio de Referencia': '43,47830',
                        'Tipo de cambio PTAX': '3,96270',
                        'Tipo de cambio SML Peso Real': '10,97190',
                        'Tipo de cambio SML Real Peso': '0,09115',
                        'indice_tiempo': '24/04/2019'
                    }
                ]
            }

    def test_sml_configuration_has_url(self):
        """Validar la existencia de la clave url dentro de
        la configuración de sml"""
        dict_config = {'sml': {'foo': 'bar'}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config.json", "sml")
                validate_url_config(config)

    def test_sml_url_has_value(self):
        """Validar que la url sea valida"""
        dict_config = {'sml': {'url': ''}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config.json", "sml")
                validate_url_has_value(config)

    def test_sml_configuration_has_coins(self):
        """Validar la existencia de la clave coins dentro de
        la configuración de sml"""
        dict_config = {'sml': {'foo': 'bar'}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config.json", "sml")
                validate_coins_key_config(config)

    def test_sml_coins_has_values(self):
        """Validar la existencia de valores dentro de coins"""
        dict_config = {'sml': {'coins': {}}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config.json", "sml")
                validate_coins_key_has_values(config)

    def test_fetch_content_patching_driver(self):
        """Probar fetch content"""
        coins = {}
        url = ''

        mocked_driver = MagicMock()
        mocked_driver.page_source = "foo"
        mocked_driver.status_code = 200

        with patch.object(
            BCRASMLScraper,
            'get_browser_driver',
            return_value=mocked_driver
        ):
            scraper = BCRASMLScraper(url, coins, False)
            content = scraper.fetch_content(coins)
            assert content == "foo"

    def test_fetch_content_invalid_url_patching_driver(self):
        """Probar fetch content con url invalida"""
        coins = {}
        url = ''

        mocked_driver = MagicMock()
        mocked_driver.page_source = 400

        with patch.object(
            BCRASMLScraper,
            'get_browser_driver',
            return_value=mocked_driver
        ):
            scraper = BCRASMLScraper(url, coins, False)
            content = scraper.fetch_content(coins)
            assert content == 400

    def test_get_intermediate_panel_data_from_parsed(self):

        parsed = {
            'peso_uruguayo':
            [
                {
                    'Tipo de cambio de Referencia': Decimal('44.89670'),
                    'Tipo de cambio URINUSCA': Decimal('35.03600'),
                    'Tipo de cambio SML Peso Uruguayo': Decimal('1.28145'),
                    'Tipo de cambio SML Uruguayo Peso': Decimal('0.78040'),
                    'indice_tiempo': date(2019, 5, 6)
                }
            ],
            'real':
            [
                {
                    'Tipo de cambio de Referencia': Decimal('44.89670'),
                    'Tipo de cambio PTAX': Decimal('3.96210'),
                    'Tipo de cambio SML Peso Real': Decimal('11.33155'),
                    'Tipo de cambio SML Real Peso': Decimal('0.08825'),
                    'indice_tiempo': date(2019, 5, 6)
                }
            ]
        }

        url = ''
        coins = {
            'peso_uruguayo': 'Peso Uruguayo',
            'real': 'Real'
        }

        scraper = BCRASMLScraper(url, coins, True)

        result = scraper.get_intermediate_panel_data_from_parsed(parsed)

        assert result == [
            {
                'indice_tiempo': date(2019, 5, 6),
                'coin': 'peso_uruguayo',
                'type': 'Tipo de cambio de Referencia',
                'value': Decimal('44.89670')
            },
            {
                'indice_tiempo': date(2019, 5, 6),
                'coin': 'peso_uruguayo',
                'type': 'Tipo de cambio URINUSCA',
                'value': Decimal('35.03600')
            },
            {
                'indice_tiempo': date(2019, 5, 6),
                'coin': 'peso_uruguayo',
                'type': 'Tipo de cambio SML Peso Uruguayo',
                'value': Decimal('1.28145')
            },
            {
                'indice_tiempo': date(2019, 5, 6),
                'coin': 'peso_uruguayo',
                'type': 'Tipo de cambio SML Uruguayo Peso',
                'value': Decimal('0.78040')
            },
            {
                'indice_tiempo': date(2019, 5, 6),
                'coin': 'real',
                'type': 'Tipo de cambio de Referencia',
                'value': Decimal('44.89670')
            },
            {
                'indice_tiempo': date(2019, 5, 6),
                'coin': 'real',
                'type': 'Tipo de cambio PTAX',
                'value': Decimal('3.96210')
            },
            {
                'indice_tiempo': date(2019, 5, 6),
                'coin': 'real',
                'type': 'Tipo de cambio SML Peso Real',
                'value': Decimal('11.33155')
            },
            {
                'indice_tiempo': date(2019, 5, 6),
                'coin': 'real',
                'type': 'Tipo de cambio SML Real Peso',
                'value': Decimal('0.08825')
            }
        ]

    def test_preprocessed_rows(self):
        rows = [
            {
                'indice_tiempo': '2019-03-06',
                'Tipo de cambio de Referencia': '40.48170',
                'Tipo de cambio URINUSCA': '32.68200',
                'Tipo de cambio SML Peso Uruguayo': '1.23865',
                'Tipo de cambio SML Uruguayo Peso': '0.80735'
            },
            {
                'indice_tiempo': '2019-03-06',
                'Tipo de cambio de Referencia': '40.48170',
                'Tipo de cambio PTAX': '3.83000',
                'Tipo de cambio SML Peso Real': '10.56965',
                'Tipo de cambio SML Real Peso': '0.09465'
            }
        ]

        scraper = BCRASMLScraper(False, rows, False)

        result = scraper.preprocess_rows(rows)

        assert result == [
            {
                'indice_tiempo': date(2019, 3, 6),
                'Tipo de cambio de Referencia': Decimal('40.48170'),
                'Tipo de cambio URINUSCA': Decimal('32.68200'),
                'Tipo de cambio SML Peso Uruguayo': Decimal('1.23865'),
                'Tipo de cambio SML Uruguayo Peso': Decimal('0.80735')
            },
            {
                'indice_tiempo': date(2019, 3, 6),
                'Tipo de cambio de Referencia': Decimal('40.48170'),
                'Tipo de cambio PTAX': Decimal('3.83000'),
                'Tipo de cambio SML Peso Real': Decimal('10.56965'),
                'Tipo de cambio SML Real Peso': Decimal('0.09465')
            }
        ]

    def test_parse_from_intermediate_panel(self):
        """Probar parseo desde el archivo intermedio"""

        start_date = '2019-03-06'
        end_date = '2019-03-06'

        coins = {
            "peso_uruguayo": "Peso Uruguayo",
            "real": "Real"
        }
        url = ''

        intermediate_panel_df = MagicMock()
        intermediate_panel_df = {
            'indice_tiempo': [
                '2019-03-06',
                '2019-03-06',
                '2019-03-06',
                '2019-03-06',
                '2019-03-06',
                '2019-03-06',
                '2019-03-06',
                '2019-03-06'
            ],
            'coin': [
                'real',
                'real',
                'real',
                'real',
                'peso_uruguayo',
                'peso_uruguayo',
                'peso_uruguayo',
                'peso_uruguayo'
            ],
            'type': [
                'Tipo de cambio de Referencia',
                'Tipo de cambio PTAX',
                'Tipo de cambio SML Peso Real',
                'Tipo de cambio SML Real Peso',
                'Tipo de cambio de Referencia',
                'Tipo de cambio URINUSCA',
                'Tipo de cambio SML Peso Uruguayo',
                'Tipo de cambio SML Uruguayo Peso'
            ],
            'value': [
                '40.48170',
                '3.83000',
                '10.56965',
                '0.09465',
                '40.48170',
                '32.68200',
                '1.23865',
                '0.80735',
            ]
        }

        with patch.object(
            BCRASMLScraper,
            'read_intermediate_panel_dataframe',
            return_value=pd.DataFrame(data=intermediate_panel_df)
        ):
            scraper = BCRASMLScraper(url, coins, True)
            content = scraper.parse_from_intermediate_panel(
                start_date, end_date,
                )

            assert content == {
                'peso_uruguayo': [
                    {
                        'indice_tiempo': '2019-03-06',
                        'Tipo de cambio de Referencia': '40.48170',
                        'Tipo de cambio URINUSCA': '32.68200',
                        'Tipo de cambio SML Peso Uruguayo': '1.23865',
                        'Tipo de cambio SML Uruguayo Peso': '0.80735'
                    }
                ],
                'real': [
                    {
                        'indice_tiempo': '2019-03-06',
                        'Tipo de cambio de Referencia': '40.48170',
                        'Tipo de cambio PTAX': '3.83000',
                        'Tipo de cambio SML Peso Real': '10.56965',
                        'Tipo de cambio SML Real Peso': '0.09465'
                    }
                ]
            }

    def test_run_not_using_intermediate_panel(self):

        start_date = datetime(2019, 5, 6)
        end_date = datetime(2019, 5, 6)

        url = '''
         http://www.bcra.gov.ar/PublicacionesEstadisticas/Tipo_de_cambio_sml.asp
        '''

        coins = {
            "peso_uruguayo": "Peso Uruguayo",
            "real": "Real"
        }

        parsed = {
            'peso_uruguayo':
            [
                {
                    'Tipo de cambio de Referencia': Decimal('44.89670'),
                    'Tipo de cambio URINUSCA': Decimal('35.03600'),
                    'Tipo de cambio SML Peso Uruguayo': Decimal('1.28145'),
                    'Tipo de cambio SML Uruguayo Peso': Decimal('0.78040'),
                    'indice_tiempo': date(2019, 5, 6)
                }
            ],
            'real':
            [
                {
                    'Tipo de cambio de Referencia': Decimal('44.89670'),
                    'Tipo de cambio PTAX': Decimal('3.96210'),
                    'Tipo de cambio SML Peso Real': Decimal('11.33155'),
                    'Tipo de cambio SML Real Peso': Decimal('0.08825'),
                    'indice_tiempo': date(2019, 5, 6)
                }
            ]
        }

        peso_uruguayo_preprocess = [
                {
                    'Tipo de cambio de Referencia': Decimal('44.89670'),
                    'Tipo de cambio URINUSCA': Decimal('35.03600'),
                    'Tipo de cambio SML Peso Uruguayo': Decimal('1.28145'),
                    'Tipo de cambio SML Uruguayo Peso': Decimal('0.78040'),
                    'indice_tiempo': date(2019, 5, 6)
                }
            ]

        real_preprocess = [
                {
                    'Tipo de cambio de Referencia': Decimal('44.89670'),
                    'Tipo de cambio PTAX': Decimal('3.96210'),
                    'Tipo de cambio SML Peso Real': Decimal('11.33155'),
                    'Tipo de cambio SML Real Peso': Decimal('0.08825'),
                    'indice_tiempo': date(2019, 5, 6)
                }
            ]

        with patch.object(
            BCRASMLScraper,
            'fetch_contents',
            return_value=''
        ):
            with patch.object(
                BCRASMLScraper,
                'parse_contents',
                return_value=parsed
            ):
                with patch.object(
                    BCRASMLScraper,
                    'preprocess_rows',
                    side_effect=[peso_uruguayo_preprocess, real_preprocess]
                ):
                    with patch.object(
                        BCRASMLScraper,
                        'save_intermediate_panel',
                        return_value=''
                    ):
                        scraper = BCRASMLScraper(url, coins, False)
                        result = scraper.run(start_date, end_date)

                        assert result == {
                            'peso_uruguayo': [
                                {
                                    'Tipo de cambio de Referencia': Decimal(
                                        '44.89670'
                                        ),
                                    'Tipo de cambio URINUSCA': Decimal(
                                        '35.03600'
                                        ),
                                    'Tipo de cambio SML Peso Uruguayo': (
                                        Decimal('1.28145')
                                        ),
                                    'Tipo de cambio SML Uruguayo Peso': (
                                        Decimal('0.78040')
                                        ),
                                    'indice_tiempo': date(2019, 5, 6)
                                }
                            ],
                            'real': [
                                {
                                    'Tipo de cambio de Referencia': Decimal(
                                        '44.89670'
                                        ),
                                    'Tipo de cambio PTAX': Decimal('3.96210'),
                                    'Tipo de cambio SML Peso Real': Decimal(
                                        '11.33155'
                                        ),
                                    'Tipo de cambio SML Real Peso': Decimal(
                                        '0.08825'
                                        ),
                                    'indice_tiempo': date(2019, 5, 6)
                                }
                            ]
                        }

    def test_run_using_intermediate_panel(self):

        start_date = datetime(2019, 5, 6)
        end_date = datetime(2019, 5, 6)

        url = '''
         http://www.bcra.gov.ar/PublicacionesEstadisticas/Tipo_de_cambio_sml.asp
        '''

        coins = {
            "peso_uruguayo": "Peso Uruguayo",
            "real": "Real"
        }

        parsed = {
            'peso_uruguayo':
            [
                {
                    'Tipo de cambio de Referencia': Decimal('44.89670'),
                    'Tipo de cambio URINUSCA': Decimal('35.03600'),
                    'Tipo de cambio SML Peso Uruguayo': Decimal('1.28145'),
                    'Tipo de cambio SML Uruguayo Peso': Decimal('0.78040'),
                    'indice_tiempo': date(2019, 5, 6)
                }
            ],
            'real':
            [
                {
                    'Tipo de cambio de Referencia': Decimal('44.89670'),
                    'Tipo de cambio PTAX': Decimal('3.96210'),
                    'Tipo de cambio SML Peso Real': Decimal('11.33155'),
                    'Tipo de cambio SML Real Peso': Decimal('0.08825'),
                    'indice_tiempo': date(2019, 5, 6)
                }
            ]
        }

        peso_uruguayo_preprocess = [
                {
                    'Tipo de cambio de Referencia': Decimal('44.89670'),
                    'Tipo de cambio URINUSCA': Decimal('35.03600'),
                    'Tipo de cambio SML Peso Uruguayo': Decimal('1.28145'),
                    'Tipo de cambio SML Uruguayo Peso': Decimal('0.78040'),
                    'indice_tiempo': date(2019, 5, 6)
                }
            ]

        real_preprocess = [
                {
                    'Tipo de cambio de Referencia': Decimal('44.89670'),
                    'Tipo de cambio PTAX': Decimal('3.96210'),
                    'Tipo de cambio SML Peso Real': Decimal('11.33155'),
                    'Tipo de cambio SML Real Peso': Decimal('0.08825'),
                    'indice_tiempo': date(2019, 5, 6)
                }
            ]

        with patch.object(
            BCRASMLScraper,
            'parse_from_intermediate_panel',
            return_value=parsed
        ):
            with patch.object(
                BCRASMLScraper,
                'preprocess_rows',
                side_effect=[peso_uruguayo_preprocess, real_preprocess]
            ):
                scraper = BCRASMLScraper(url, coins, True)
                result = scraper.run(start_date, end_date)

                assert result == {
                    'peso_uruguayo': [
                        {
                            'Tipo de cambio de Referencia': Decimal(
                                '44.89670'
                                ),
                            'Tipo de cambio URINUSCA': Decimal('35.03600'),
                            'Tipo de cambio SML Peso Uruguayo': Decimal(
                                '1.28145'
                                ),
                            'Tipo de cambio SML Uruguayo Peso': Decimal(
                                '0.78040'
                                ),
                            'indice_tiempo': date(2019, 5, 6)
                        }
                    ],
                    'real': [
                        {
                            'Tipo de cambio de Referencia': Decimal(
                                '44.89670'
                                ),
                            'Tipo de cambio PTAX': Decimal('3.96210'),
                            'Tipo de cambio SML Peso Real': Decimal(
                                '11.33155'
                                ),
                            'Tipo de cambio SML Real Peso': Decimal('0.08825'),
                            'indice_tiempo': date(2019, 5, 6)
                        }
                    ]
                }
