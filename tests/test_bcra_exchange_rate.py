#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo bcrascraper."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

import datetime
from datetime import date
import unittest

from bcra_scraper.scraper import BCRAExchangeRateScraper


class BcraExchangeRateTestCase(unittest.TestCase):

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
        scraper = BCRAExchangeRateScraper(url, coins)
        end_date = date.today()
        contents = {}
        parsed = scraper.parse_contents(contents, end_date)

        assert parsed == []

    def test_parse_for_non_empty_contents(self):
        url = \
         "http://www.bcra.gov.ar/Publicaciones\
            Estadisticas/Evolucion_moneda.asp"
        coins = {
            "bolivar_venezolano": "Bolívar Venezolano"
        }
        scraper = BCRAExchangeRateScraper(url, coins)
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

        parsed = scraper.parse_contents(contents, end_date)

        assert parsed == [{'moneda': 'bolivar_venezolano',
                          'indice_tiempo': '08/04/2019',
                           'tipo_pase': '0,0003030',
                           'tipo_cambio': '0,0132500'}]

    def test_parse_coin(self):
        url = \
         "http://www.bcra.gov.ar/Publicaciones\
            Estadisticas/Evolucion_moneda.asp"
        coins = {
            "bolivar_venezolano": "Bolívar Venezolano"
        }
        scraper = BCRAExchangeRateScraper(url, coins)
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

        parsed_coin = scraper.parse_coin(content, end_date, coin)

        assert parsed_coin == [{'moneda': 'bolivar_venezolano',
                                'indice_tiempo': '08/04/2019',
                                'tipo_pase': '0,0003030',
                                'tipo_cambio': '0,0132500'}]
