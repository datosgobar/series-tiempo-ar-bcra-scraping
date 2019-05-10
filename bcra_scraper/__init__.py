# -*- coding: utf-8 -*-

from bcra_scraper.scraper_libor import BCRALiborScraper
from bcra_scraper.scraper_exchange_rates import BCRAExchangeRateScraper
from bcra_scraper.scraper_sml import BCRASMLScraper
from bcra_scraper.scraper_tce import BCRATCEScraper

__all__ = [
    BCRALiborScraper,
    BCRAExchangeRateScraper,
    BCRASMLScraper,
    BCRATCEScraper,
]


__author__ = """BCRA Scraper"""
__email__ = 'datos@modernizacion.gob.ar'
__version__ = '0.1.0'
