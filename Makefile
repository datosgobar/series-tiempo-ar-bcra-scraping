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

all_local: libor_local sml_local tce_local exchange_rates_local
all: libor sml tce exchange_rates

install_anaconda:
	wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
	bash Miniconda3-latest-Linux-x86_64.sh
	rm Miniconda3-latest-Linux-x86_64.sh
	export PATH=$$PATH:/home/seriesbcra/miniconda3/bin

setup_anaconda:
	conda create -n $(CONDA_ENV) python=3.7 --no-default-packages
	source $(ACTIVATE) $(CONDA_ENV); $(SERIES_TIEMPO_PIP) install -e .

setup_anaconda_local:
	conda create -n $(CONDA_ENV) python=3.7 --no-default-packages
	source activate $(CONDA_ENV); $(SERIES_TIEMPO_PIP) install -e .

setup_virtualenv:
	test -d $(VIRTUALENV)/bin/activate || $(SERIES_TIEMPO_PYTHON) -m venv $(VIRTUALENV)
	source $(VIRTUALENV)/bin/activate; \
		$(SERIES_TIEMPO_PIP) install -r requirements.txt

update_environment:
	git pull
	source $(ACTIVATE) $(CONDA_ENV); $(SERIES_TIEMPO_PIP) install -r requirements.txt --upgrade

update_environment_local:
	git pull
	source activate $(CONDA_ENV); $(SERIES_TIEMPO_PIP) install -r requirements.txt --upgrade


# desde una fecha cercana (para pruebas rápidas)
libor_local:
	bcra_scraper libor --start-date=03/01/2001

sml_local:
	bcra_scraper sml --start-date=01/01/2016

tce_local:
	bcra_scraper tce --start-date=01/01/2016

exchange_rates_local:
	bcra_scraper exchange-rates --start-date=01/08/2019

# desde la fecha más lejana posible en cada caso
libor:
# 	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper libor --start-date=03/01/2001
	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper libor --start-date=03/01/2001

sml:
# 	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper sml --start-date=03/10/2008
	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper sml --start-date=01/01/2016

tce:
# 	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper tce --start-date=10/03/2010
	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper tce --start-date=01/01/2016

exchange_rates:
# 	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper exchange-rates --start-date=31/01/1935
	source $(ACTIVATE) $(CONDA_ENV); bcra_scraper exchange-rates --start-date=01/08/2019
