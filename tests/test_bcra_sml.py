#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo bcrascraper."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

from datetime import datetime, date
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock

import io
import json

from bs4 import BeautifulSoup

from bcra_scraper.scraper import BCRASMLScraper
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

    def test_run_with_valid_dates(self):

        start_date = datetime(2019, 4, 24)
        end_date = datetime(2019, 4, 24)

        url = '''
         http://www.bcra.gov.ar/PublicacionesEstadisticas/Tipo_de_cambio_sml.asp
        '''

        coins = {
            "peso_uruguayo": "Peso Uruguayo",
            "real": "Real"
        }

        with patch.object(
            BCRASMLScraper,
            'fetch_contents',
            return_value={
                'peso_uruguayo':
                    '''
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
                    ''',
                    'real':
                    '''
                    <table colspan="3" class="table table-BCRA table-bordered
                    table-hover table-responsive">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Tipo de cambio de Referencia</th>
                            <th>Tipo de cambio PTAX</th>
                            <th>Tipo de cambio SML Peso Real</th>
                            <th>Tipo de cambio SML Real Peso</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>24/04/2019</td>
                            <td>43,47830</td>
                            <td>3,96270</td>
                            <td>10,97190</td>
                            <td>0,09115</td>
                        </tr>
                    </tbody>
                    </table>
                    '''
                    }
                ):

            scraper = BCRASMLScraper(url, coins, False)
            result = scraper.run(start_date, end_date)

            assert result == [
                {
                    'coin': 'peso_uruguayo',
                    'indice_tiempo': '24/04/2019',
                    'Tipo de cambio de Referencia': '43,47830',
                    'Tipo de cambio URINUSCA': '34,51000',
                    'Tipo de cambio SML Peso Uruguayo': '1,25990',
                    'Tipo de cambio SML Uruguayo Peso': '0,79375'
                },
                {
                    'coin': 'real',
                    'indice_tiempo': '24/04/2019',
                    'Tipo de cambio de Referencia': '43,47830',
                    'Tipo de cambio PTAX': '3,96270',
                    'Tipo de cambio SML Peso Real': '10,97190',
                    'Tipo de cambio SML Real Peso': '0,09115'
                }
            ]

    def test_run_with_non_valid_dates(self):

        start_date = datetime(2019, 4, 13)
        end_date = datetime(2019, 4, 12)

        url = ''

        coins = {}

        with patch.object(
            BCRASMLScraper,
            'run',
            return_value=[]
        ):

            scraper = BCRASMLScraper(url, coins, False)
            result = scraper.run(start_date, end_date)

            assert result == []

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
