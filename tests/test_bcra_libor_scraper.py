#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests del modulo bcra_scraper."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import with_statement
import unittest

from datetime import date, timedelta

from bcra_scraper.utils import get_most_recent_previous_business_day


class BcraLiborScraperTestCase(unittest.TestCase):

    def test_get_last_business_day(self):
        assert date(2019, 3, 15) == get_most_recent_previous_business_day(date(2019, 3, 18))
        assert date(2019, 3, 18) == get_most_recent_previous_business_day(date(2019, 3, 19))
        assert date(2019, 3, 22) == get_most_recent_previous_business_day(date(2019, 3, 24))
