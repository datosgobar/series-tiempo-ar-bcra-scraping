#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from csv import DictWriter
from datetime import date
import json

import click

from bcra_scraper.scraper import BCRALiborScraper, BCRAExchangeRateScraper


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


def read_config(file_path, command):
    with open(file_path) as config_data:
        return json.load(config_data)[command]


@click.group()
@click.pass_context
def cli(ctx):
    pass


# TODO: validar q no se ingrese solo end_date
# TODO: validar q end_date >= start_date
@cli.command()
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
@click.option(
    '--use-intermediate-panel',
    default=False,
    is_flag=True,
    help=('Use este flag para forzar la lectura de datos desde un'
          'archivo intermedio')
)
@click.pass_context
def libor(ctx, start_date, end_date, config, use_intermediate_panel,
          *args, **kwargs):

    start_date = date(start_date.year, start_date.month, start_date.day)
    end_date = date(end_date.year, end_date.month, end_date.day)

    config = read_config(file_path=config, command=ctx.command.name)

    scraper = BCRALiborScraper(
        url=config.get('url'),
        rates=config.get('rates'),
        use_intermediate_panel=use_intermediate_panel
    )

    parsed = scraper.run(start_date, end_date)

    if parsed:
        csv_name = 'tasas-libor.csv'

        csv_header = ['indice_tiempo', '30', '60', '90', '180', '360']
        processed_header = scraper.preprocess_header(scraper.rates, csv_header)

        write_tasas_libor(csv_name, processed_header, parsed)
    else:
        click.echo("No se encontraron resultados")


@cli.command()
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
@click.pass_context
def exchange_rates(ctx, start_date, end_date, config):

    config = read_config(file_path=config, command=ctx.command.name)

    scraper = BCRAExchangeRateScraper(
        url=config.get('url'),
        coins=config.get('coins')
    )
    scraper.run(start_date, end_date)
