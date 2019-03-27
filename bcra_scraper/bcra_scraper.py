#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from csv import DictWriter
from datetime import date
import json

import click

from bcra_scraper.scraper import Scraper

# TODO: test me!
def write_tasas_libor(file_name, header, rows):
    with open(file_name, 'w') as archivo:
        writer = DictWriter(archivo, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

def get_default_start_date():
    today = date.today()

    return f'{today.day}/{today.month}/{today.year}'

def get_default_end_date():
    today = date.today()

    return f'{today.day}/{today.month}/{today.year}'

def read_config(file_path):
    with open(file_path) as config_data:
        return json.load(config_data)


# TODO: validar q no se ingrese solo end_date
# TODO: validar q end_date >= start_date
@click.command()
@click.option(
    '--start-date',
    default=get_default_start_date,
    type=click.DateTime(formats=['%d/%m/%Y']),
    )
@click.option(
    '--end-date',
    default=get_default_end_date,
    type=click.DateTime(formats=['%d/%m/%Y']),
    )
@click.option(
    '--config',
    default='config.json',
    type=click.Path(exists=True),
    )
def main(start_date, end_date, config):
    start_date = date(start_date.year, start_date.month, start_date.day)
    end_date = date(end_date.year, end_date.month, end_date.day)

    config = read_config(file_path=config)

    scraper = Scraper(url=config.get('url'), rates=config.get('rates'))

    parsed = scraper.run(start_date, end_date)

    if parsed:
        csv_name = 'tasas-libor.csv'
        csv_header = ['indice_tiempo', '30', '60', '90', '180', '360']

        write_tasas_libor(csv_name, csv_header, parsed)
    else:
        click.echo("No se encontraron resultados")