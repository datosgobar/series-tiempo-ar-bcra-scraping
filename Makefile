# Makefile para Ubuntu 16.04
SHELL = /bin/bash
SERIES_TIEMPO_PIP ?= pip
SERIES_TIEMPO_PYTHON ?= python
VIRTUALENV = series-tiempo-ar-bcra-scraping
CONDA_ENV = series-tiempo-ar-bcra-scraping
ACTIVATE = /home/seriesbcra/miniconda3/bin/activate

clean:
	rm -rf bcra_scraper.egg-info
	rm -rf .cache
	rm -rf .pytest_cache

all_local: libor_local exchange_rates_local sml_local tce_local
all: libor exchange_rates sml tce

# desde una fecha cercana (para pruebas rápidas)
libor_local:
	bcra_scraper libor --start-date=05/01/2018

exchange_rates_local:
	bcra_scraper exchange-rates --start-date=01/08/2019

sml_local:
	bcra_scraper sml --start-date=01/08/2019

tce_local:
	bcra_scraper tce --start-date=05/01/2018

# desde la fecha más lejana posible en cada caso
libor:
	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper libor --start-date=03/01/2001

exchange_rates:
	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper exchange-rates --start-date=31/01/1935

sml:
	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper sml --start-date=03/10/2008

tce:
	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper tce --start-date=10/03/2010
