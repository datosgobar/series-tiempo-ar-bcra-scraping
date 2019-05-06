#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo bcrascraper."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import datetime
from datetime import date
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock
from decimal import Decimal

import io
import json

from bs4 import BeautifulSoup

from bcra_scraper.scraper import BCRAExchangeRateScraper
from bcra_scraper.bcra_scraper import validate_url_config
from bcra_scraper.bcra_scraper import validate_url_has_value
from bcra_scraper.bcra_scraper import validate_coins_key_config
from bcra_scraper.bcra_scraper import validate_coins_key_has_values
from bcra_scraper.exceptions import InvalidConfigurationError
from bcra_scraper.bcra_scraper import read_config


class BcraExchangeRateTestCase(unittest.TestCase):

    def test_html_is_valid(self):
        """Probar que el html sea valido"""
        url = ""
        single_date = date(2019, 3, 4)

        rates = {}
        with patch.object(
            BCRAExchangeRateScraper,
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
            scraper = BCRAExchangeRateScraper(url, rates, False)
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
            BCRAExchangeRateScraper,
            'fetch_content',
            return_value=' '
        ):
            scraper = BCRAExchangeRateScraper(url, coins, False)
            content = scraper.fetch_content(single_date)

            soup = BeautifulSoup(content, "html.parser")

            table = soup.find('table')
            head = table.find('thead') if table else None
            body = table.find('tbody') if table else None

            assert table is None
            assert head is None
            assert body is None

    def test_parse_for_empty_contents(self):
        url = \
         "http://www.bcra.gov.ar/Publicaciones\
            Estadisticas/Evolucion_moneda.asp"
        coins = {
            "bolivar_venezolano": "Bolívar Venezolano",
            "chelin_austriaco": "Chelín Austríaco",
            "cordoba_nicaraguense": "Cordoba Nicaraguense",
            "corona_checa": "Corona Checa",
            "corona_danesa": "Corona Danesa",
        }
        scraper = BCRAExchangeRateScraper(url, coins, False)
        start_date = date.today()
        end_date = date.today()
        contents = {}
        parsed = scraper.parse_contents(contents, start_date, end_date)

        assert parsed['tc_local'] == []
        assert parsed['tp_usd'] == []

    def test_parse_for_non_empty_contents(self):
        url = \
         "http://www.bcra.gov.ar/Publicaciones\
            Estadisticas/Evolucion_moneda.asp"
        coins = {
            "bolivar_venezolano": "Bolívar Venezolano"
        }
        scraper = BCRAExchangeRateScraper(url, coins, False)
        start_date = datetime.datetime(2019, 4, 8)
        end_date = datetime.datetime(2019, 4, 8)
        contents = {}

        table_content = '''
        <table class="table table-BCRA table-bordered table-hover
        table-responsive" colspan="3">
            <thead>
            <tr>
            <td colspan="3">
                <b>MERCADO DE CAMBIOS - COTIZACIONES CIERRE VENDEDOR<br>
                Bolívar Venezolano</b>
            </td>
            </tr>
            <tr>
                <td width="10%"><b>
                    FECHA</b>
                </td>
                <td width="40%"><b>
            TIPO DE PASE - EN DOLARES - (por unidad)</b></td>
                <td width="50%"><b>
            TIPO DE CAMBIO - MONEDA DE CURSO LEGAL - (por unidad)</b></td>
                </tr>
            </thead>
            <tbody><tr>
                <td width="10%">
                08/04/2019</td>
                <td width="40%">
                0,0003030</td>
                <td width="50%">
                0,0132500</td>
            </tr>
            </tbody>
        </table>
        '''

        contents['bolivar_venezolano'] = table_content

        parsed = scraper.parse_contents(contents, start_date, end_date)

        # FIXME
        assert len(parsed['tc_local']) == 1
        assert len(parsed['tp_usd']) == 1

    def test_parse_coin(self):
        url = \
         "http://www.bcra.gov.ar/Publicaciones\
            Estadisticas/Evolucion_moneda.asp"
        coins = {
            "bolivar_venezolano": "Bolívar Venezolano"
        }
        scraper = BCRAExchangeRateScraper(url, coins, False)
        start_date = datetime.datetime(2019, 4, 8)
        end_date = datetime.datetime(2019, 4, 8)
        coin = 'bolivar_venezolano'

        content = '''
        <table class="table table-BCRA table-bordered table-hover
        table-responsive" colspan="3">
            <thead>
            <tr>
            <td colspan="3">
                <b>MERCADO DE CAMBIOS - COTIZACIONES CIERRE VENDEDOR<br>
                Bolívar Venezolano</b>
            </td>
            </tr>
            <tr>
                <td width="10%"><b>
                    FECHA</b>
                </td>
                <td width="40%"><b>
            TIPO DE PASE - EN DOLARES - (por unidad)</b></td>
                <td width="50%"><b>
            TIPO DE CAMBIO - MONEDA DE CURSO LEGAL - (por unidad)</b></td>
                </tr>
            </thead>
            <tbody><tr>
                <td width="10%">
                08/04/2019</td>
                <td width="40%">
                0,0003030</td>
                <td width="50%">
                0,0132500</td>
            </tr>
            </tbody>
        </table>
        '''

        parsed_coin = scraper.parse_coin(content, start_date, end_date, coin)
        # breakpoint()

        # FIXME
        assert len(parsed_coin) == 1
        # assert len(parsed['tp_usd']) == 1
        # assert parsed_coin == [{'moneda': 'bolivar_venezolano',
        #                         'indice_tiempo': '08/04/2019',
        #                         'tp_usd': '0,0003030',
        #                         'tc_local': '0,0132500'}]

    def test_run_with_valid_dates(self):

        start_date = datetime.datetime(2019, 4, 8)
        end_date = datetime.datetime(2019, 4, 8)

        url = '''
        http://www.bcra.gov.ar/PublicacionesEstadisticas/Tipo_de_cambio_sml.asp
        '''

        coins = {
            "bolivar_venezolano": "Bolívar Venezolano",
            "cordoba_nicaraguense": "Cordoba Nicaraguense",
        }

        with patch.object(
            BCRAExchangeRateScraper,
            'fetch_contents',
            return_value={
                    'bolivar_venezolano':
                    '''
                    <table class="table table-BCRA table-bordered\
                        table-hover table-responsive" colspan="3">
                        <thead>
                        </thead>
                        <tbody><tr>
                            <td width="10%">08/04/2019</td>
                            <td width="40%">0,0003030</td>
                            <td width="50%">0,0132500</td>
                        </tr>
                        </tbody>
                    </table>
                    ''',
                    'cordoba_nicaraguense':
                    '''
                    <table class="table table-BCRA table-bordered\
                        table-hover table-responsive" colspan="3">
                        <thead>
                        </thead>
                        <tbody><tr>
                            <td width="10%">08/04/2019</td>
                            <td width="40%">0,0302850</td>
                            <td width="50%">1,3234400</td>
                        </tr>
                        </tbody>
                    </tbody>
                    </table>
                    '''
                    }
                ):

            scraper = BCRAExchangeRateScraper(url, coins, False)
            result = scraper.run(start_date, end_date)

            assert result == {
                'tc_local':
                    [
                        {
                            'bolivar_venezolano': Decimal('2500'),
                            'cordoba_nicaraguense': Decimal('4400'),
                            'indice_tiempo': datetime.date(2019, 4, 8)
                        }
                    ],
                'tp_usd':
                    [
                        {
                            'bolivar_venezolano': Decimal('3030'),
                            'cordoba_nicaraguense': Decimal('2850'),
                            'indice_tiempo': datetime.date(2019, 4, 8)
                        }
                    ]
                }

    def test_exchange_rates_configuration_has_url(self):
        """Validar la existencia de la clave url dentro de
        la configuración de exchange-rates"""
        dict_config = {'exchange-rates': {'foo': 'bar'}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config.json", "exchange-rates")
                validate_url_config(config)

    def test_exchange_rates_url_has_value(self):
        """Validar que la url sea valida"""
        dict_config = {'exchange-rates': {'url': ''}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config.json", "exchange-rates")
                validate_url_has_value(config)

    def test_exchange_rates_configuration_has_coins(self):
        """Validar la existencia de la clave coins dentro de
        la configuración de exchange rates"""
        dict_config = {'exchange-rates': {'foo': 'bar'}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config.json", "exchange-rates")
                validate_coins_key_config(config)

    def test_exchange_rates_coins_has_values(self):
        """Validar la existencia de valores dentro de coins"""
        dict_config = {'exchange-rates': {'coins': {}}}

        with mock.patch(
            'builtins.open',
            return_value=io.StringIO(json.dumps(dict_config))
        ):

            with self.assertRaises(InvalidConfigurationError):
                config = read_config("config.json", "exchange-rates")
                validate_coins_key_has_values(config)

    def test_fetch_content_patching_driver(self):
        """Probar fetch content"""
        single_date = date(2019, 3, 4)
        coins = {}
        url = ''

        mocked_driver = MagicMock()
        mocked_driver.page_source = "foo"
        mocked_driver.status_code = 200

        with patch.object(
            BCRAExchangeRateScraper,
            'get_browser_driver',
            return_value=mocked_driver
        ):
            scraper = BCRAExchangeRateScraper(url, coins, False)
            content = scraper.fetch_content(single_date, coins)
            assert content == "foo"

    def test_fetch_content_invalid_url_patching_driver(self):
        """Probar fetch content con url invalida"""
        single_date = date(2019, 3, 4)
        coins = {}
        url = ''

        mocked_driver = MagicMock()
        mocked_driver.page_source = 400

        with patch.object(
            BCRAExchangeRateScraper,
            'get_browser_driver',
            return_value=mocked_driver
        ):
            scraper = BCRAExchangeRateScraper(url, coins, False)
            content = scraper.fetch_content(single_date, coins)
            assert content == 400
