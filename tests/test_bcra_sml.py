#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo bcrascraper."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement

from datetime import datetime
import unittest

from bcra_scraper.scraper import BCRASMLScraper


class BcraSmlScraperTestCase(unittest.TestCase):

    def test_parse_content_with_valid_content(self):

        start_date = datetime(2019, 4, 11)
        end_date = datetime(2019, 4, 11)
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
                    <td>11/04/2019</td>
                    <td>42,91170</td>
                    <td>34,12800</td>
                    <td>1,25740</td>
                    <td>0,79535</td>
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
                'moneda': 'peso_uruguayo',
                'Fecha': '11/04/2019',
                'Tipo de cambio de Referencia': '42,91170',
                'Tipo de cambio URINUSCA': '34,12800',
                'Tipo de cambio SML Peso Uruguayo': '1,25740',
                'Tipo de cambio SML Uruguayo Peso': '0,79535'
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

    def test_run(self):

        start_date = datetime(2019, 4, 11)
        end_date = datetime(2019, 4, 11)

        url = '''
         http://www.bcra.gov.ar/PublicacionesEstadisticas/Tipo_de_cambio_sml.asp
        '''

        coins = {
            "peso_uruguayo": "Peso Uruguayo",
            "real": "Real"
        }

        scraper = BCRASMLScraper(url, coins, False)
        result = scraper.run(start_date, end_date)

        assert result == [
            {
                'moneda': 'peso_uruguayo',
                'Fecha': '11/04/2019',
                'Tipo de cambio de Referencia': '42,91170',
                'Tipo de cambio URINUSCA': '34,12800',
                'Tipo de cambio SML Peso Uruguayo': '1,25740',
                'Tipo de cambio SML Uruguayo Peso': '0,79535'
            },
            {
                'moneda': 'real',
                'Fecha': '11/04/2019',
                'Tipo de cambio de Referencia': '42,91170',
                'Tipo de cambio PTAX': '3,83960',
                'Tipo de cambio SML Peso Real': '11,17610',
                'Tipo de cambio SML Real Peso': '0,08950'
            }
        ]
