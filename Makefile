clean:
	rm -rf bcra_scraper.egg-info
	rm -rf .cache
	rm -rf .pytest_cache

all: libor exchange-rates sml tce

libor:
	bcra_scraper libor --start-date=01/04/2019

exchange-rates:
	bcra_scraper exchange-rates --start-date=01/04/2019

sml:
	bcra_scraper sml --start-date=01/04/2019

tce:
	bcra_scraper tce --start-date=01/04/2019
