# bcra_scraper

[![Coverage Status](https://coveralls.io/repos/github/datosgobar/bcra_scraper/badge.svg?branch=master)](https://coveralls.io/github/datosgobar/bcra_scraper?branch=master)
[![Build Status](https://travis-ci.org/datosgobar/bcra_scraper.svg?branch=master)](https://travis-ci.org/datosgobar/bcra_scraper)
[![PyPI](https://badge.fury.io/py/bcra_scraper.svg)](http://badge.fury.io/py/bcra_scraper)
[![Stories in Ready](https://badge.waffle.io/datosgobar/bcra_scraper.png?label=ready&title=Ready)](https://waffle.io/datosgobar/bcra_scraper)
[![Documentation Status](http://readthedocs.org/projects/bcra_scraper/badge/?version=latest)](http://bcra_scraper.readthedocs.org/en/latest/?badge=latest)

Descripción corta del proyecto.


* Versión python: 3.7
* Licencia: MIT license


## Instalación

Si tiene instalado una versión anterior a Python 3.6, es posible usar pyenv para instalar Python 3.6 o superior.

### pyenv en macOS

    $ brew install readline xz
    
    $ brew update
    $ brew install pyenv

### pyenv en linux
Usar https://github.com/pyenv/pyenv-installer

    $ sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
      libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
      xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
      
    $ curl https://pyenv.run | bash

### Usando pyenv

    $ pyenv install 3.6.6
    
### Instalación de bcra-scraper

    $ git clone https://github.com/datosgobar/series-tiempo-ar-bcra-scraping.git
    $ cd series-tiempo-ar-bcra-scraping
    $ pip install -e .
    
### Dependencias

* Para ejecutar el scraper es necesario tener chromedriver en el PATH, de manera que el script pueda ejecutarlo.

    brew cask install chromedriver
o
    brew cask reinstall chromedriver

### Configuración

* Crear los archivos config_email.yaml y config_general.json, en base a los archivos de ejemplo "config_email.yaml.sample", "config_general.json.sample".

    $ cp config_email.yaml.sample config_email.yaml
    $ cp config_general.json.sample config_general.json

Luego, editar los archivos config_email.yaml y config_general.json con los parámetros deseados.

* Para scraper tce: en caso de querer deshabilitar alguno de los channel para una entidad,
    cambiar a false el channel que no se quiera visualizar (mostrador o electronico).

## Uso
### Básico
* bcra_scraper libor --start-date=01/04/2019
* bcra_scraper exchange-rates --start-date=01/04/2019
* bcra_scraper sml --start-date=01/04/2019
* bcra_scraper tce --start-date=01/04/2019

### Saltear uso del panel intermedio

* bcra_scraper libor --start-date=01/04/2019 --skip-intermediate-panel-data

### Para no volver a visitar las últimas fechas que no tengan datos

* bcra_scraper libor --start-date=01/04/2019 --skip-clean-last-dates
