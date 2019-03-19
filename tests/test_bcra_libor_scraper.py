#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo bcra_scraper."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import unittest
from collections import OrderedDict

from datetime import date, timedelta
from bcra_scraper.scraper import Scraper
from bcra_scraper.utils import get_most_recent_previous_business_day


class BcraLiborScraperTestCase(unittest.TestCase):

    def test_get_last_business_day(self):
        assert date(2019, 3, 15) == get_most_recent_previous_business_day(date(2019, 3, 18))
        assert date(2019, 3, 18) == get_most_recent_previous_business_day(date(2019, 3, 19))
        assert date(2019, 3, 22) == get_most_recent_previous_business_day(date(2019, 3, 24))

    def test_scraper_with_empty_table(self):
        content = '''
        <table class="table table-BCRA table-bordered table-hover table-responsive">
            <thead>
                <tr><th>No existen registros</th></tr>
            </thead>
        </table>
        '''
        scraper = Scraper()

        result = scraper.parse(content)

        assert result == {}

    def test_scraper_with_valid_table(self):
        content = '''
        	<table class="table table-BCRA table-bordered table-hover table-responsive">
        <thead>
            <tr>
                <th colspan="2" align="left">Tasa LIBOR al:  15/03/2019</th>
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
        '''
        scraper = Scraper()

        result = scraper.parse(content)

        assert result.get('indice_tiempo') == '15/03/2019'
        assert result.get('30') == '2,481750'
        assert result.get('60') == '2,558380'
        assert result.get('90') == '2,625250'
        assert result.get('180') == '2,671750'
        assert result.get('360') == '2,840500'