clean:
	rm -rf bcra_scraper.egg-info
	rm -rf .cache
	rm -rf .pytest_cache

all_short: libor_short exchange_rates_short sml_short tce_short
all: libor exchange_rates sml tce

# desde una fecha cercana (para pruebas rápidas)
libor_short:
	bcra_scraper libor --start-date=01/08/2019

exchange_rates_short:
	bcra_scraper exchange-rates --start-date=01/08/2019

sml_short:
	bcra_scraper sml --start-date=01/08/2019

tce_short:
	bcra_scraper tce --start-date=01/08/2019

# desde la fecha más lejana posible en cada caso
libor:
	bcra_scraper libor --start-date=01/04/2019

exchange_rates:
	bcra_scraper exchange-rates --start-date=01/04/2019

sml:
	bcra_scraper sml --start-date=01/04/2019

tce:
	bcra_scraper tce --start-date=01/04/2019
