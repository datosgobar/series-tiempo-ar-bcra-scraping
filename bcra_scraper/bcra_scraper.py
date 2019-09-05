#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from csv import DictWriter
from datetime import date, datetime
from json import JSONDecodeError
import json
import os

import click

from bcra_scraper.exceptions import InvalidConfigurationError

from bcra_scraper import (
    BCRALiborScraper,
    BCRAExchangeRateScraper,
    BCRASMLScraper,
    BCRATCEScraper,
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# TODO: test me!
def write_file(header, rows, file_path):
    with open(file_path, 'w') as archivo:
        writer = DictWriter(archivo, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def ensure_dir_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_default_start_date():
    today = date.today()

    return f'{today.day}/{today.month}/{today.year}'


def get_default_end_date():
    today = date.today()

    return f'{today.day}/{today.month}/{today.year}'


def read_config(file_path, command):
    try:
        with open(file_path) as config_data:
            return json.load(config_data)[command]
    except JSONDecodeError:
        raise InvalidConfigurationError(
            "El formato del archivo de configuración es inválido"
        )


def validate_url_config(config):
    if 'url' not in config:
        raise InvalidConfigurationError("La clave url no existe")


def validate_url_has_value(config):
    if config['url'] == '':
        raise InvalidConfigurationError("La url no es válida")


def validate_libor_rates_config(config):
    if 'rates' not in config:
        raise InvalidConfigurationError("La clave rates no existe")


def validate_libor_rates_has_values(config):
    rates = config.get('rates', {})
    if rates == {}:
        raise InvalidConfigurationError("No existen valores para rates")


def validate_coins_key_config(config):
    if 'coins' not in config:
        raise InvalidConfigurationError("La clave coins no existe")


def validate_coins_key_has_values(config):
    coins = config.get('coins', {})
    if coins == {}:
        raise InvalidConfigurationError("No existen valores para coins")


def validate_dates(start_date, end_date):
    if start_date > end_date:
        raise InvalidConfigurationError(
            "La fecha de inicio no debe ser mayor a la de fin"
        )
    elif end_date > datetime.today():
        raise InvalidConfigurationError(
            "La fecha de fin no puede ser mayor a la fecha actual"
        )


def validate_entities_key_config(config):
    if 'entities' not in config:
        raise InvalidConfigurationError("La clave entities no existe")


def validate_entities_key_has_values(config):
    entities = config.get('entities', {})
    if entities == {}:
        raise InvalidConfigurationError("No existen valores para entities")


@click.group()
@click.pass_context
def cli(ctx):
    pass


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
@click.option(
    '--file-path',
    type=str
)
@click.pass_context
def libor(ctx, start_date, end_date, config, use_intermediate_panel, file_path,
          *args, **kwargs):
    validate_dates(start_date, end_date)
    start_date = date(start_date.year, start_date.month, start_date.day)
    end_date = date(end_date.year, end_date.month, end_date.day)

    try:
        config = read_config(file_path=config, command=ctx.command.name)
        file_path = (config['file_path']
                     if config['file_path'].startswith('/')
                     else os.path.join(ROOT_DIR, config['file_path'])
                    )
        intermediate_panel_path = (config['intermediate_panel_path']
                                   if config['intermediate_panel_path'].startswith('/')
                                   else os.path.join(ROOT_DIR, config['intermediate_panel_path'])
                                  )
        ensure_dir_exists(os.path.split(intermediate_panel_path)[0])

        validate_url_config(config)
        validate_url_has_value(config)
        validate_libor_rates_config(config)
        validate_libor_rates_has_values(config)

        scraper = BCRALiborScraper(
            url=config.get('url'),
            rates=config.get('rates'),
            use_intermediate_panel=use_intermediate_panel,
            intermediate_panel_path=intermediate_panel_path,
        )

        parsed = scraper.run(start_date, end_date)

        processed_header = scraper.preprocess_header(scraper.rates)

        write_file(processed_header, parsed, file_path)

    except InvalidConfigurationError as err:
        click.echo(err)


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
def exchange_rates(ctx, start_date, end_date, config, use_intermediate_panel):

    try:
        config = read_config(file_path=config, command=ctx.command.name)
        validate_url_config(config)
        validate_url_has_value(config)
        validate_coins_key_config(config)
        validate_coins_key_has_values(config)
        validate_dates(start_date, end_date)
        intermediate_panel_path = (config['intermediate_panel_path']
                                   if config['intermediate_panel_path'].startswith('/')
                                   else os.path.join(ROOT_DIR, config['intermediate_panel_path'])
                                  )
        ensure_dir_exists(os.path.split(intermediate_panel_path)[0])

        scraper = BCRAExchangeRateScraper(
            url=config.get('url'),
            coins=config.get('coins'),
            use_intermediate_panel=use_intermediate_panel,
            intermediate_panel_path=intermediate_panel_path
        )
        parsed = scraper.run(start_date, end_date)

        if parsed:
            coins = config.get('coins')

            csv_name = (config['tp_file_path']
                        if config['tp_file_path'].startswith('/')
                        else os.path.join(ROOT_DIR, config['tp_file_path'])
                       )
            csv_header = ['indice_tiempo']
            csv_header.extend([v for v in coins.keys()])

            write_file(csv_header, parsed['tp_usd'], csv_name)

            csv_name = (config['tc_file_path']
                        if config['tc_file_path'].startswith('/')
                        else os.path.join(ROOT_DIR, config['tc_file_path'])
                       )
            csv_header = ['indice_tiempo']
            csv_header.extend([v for v in coins.keys()])

            write_file(csv_header, parsed['tp_usd'], csv_name)

        else:
            click.echo("No se encontraron resultados")

    except InvalidConfigurationError as err:
        click.echo(err)


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
def sml(ctx, config, start_date, end_date, use_intermediate_panel):

    try:
        config = read_config(file_path=config, command=ctx.command.name)
        validate_url_config(config)
        validate_url_has_value(config)
        validate_coins_key_config(config)
        validate_coins_key_has_values(config)
        validate_dates(start_date, end_date)
        intermediate_panel_path = (config['intermediate_panel_path']
                                   if config['intermediate_panel_path'].startswith('/')
                                   else os.path.join(ROOT_DIR, config['intermediate_panel_path'])
                                  )
        ensure_dir_exists(os.path.split(intermediate_panel_path)[0])

        scraper = BCRASMLScraper(
            url=config.get('url'),
            coins=config.get('coins'),
            use_intermediate_panel=use_intermediate_panel,
            intermediate_panel_path=intermediate_panel_path
        )

        parsed = scraper.run(start_date, end_date)

        if parsed:

            for k, v in parsed.items():
                if k == 'peso_uruguayo':
                    csv_header = [
                        'indice_tiempo',
                        'Tipo de cambio de Referencia',
                        'Tipo de cambio URINUSCA',
                        'Tipo de cambio SML Peso Uruguayo',
                        'Tipo de cambio SML Uruguayo Peso'
                    ]

                    csv_name = (config['peso_uruguayo_file_path']
                                if config['peso_uruguayo_file_path'].startswith('/')
                                else os.path.join(ROOT_DIR, config['peso_uruguayo_file_path'])
                               )

                    write_file(csv_header, parsed['peso_uruguayo'], csv_name)


                elif k == 'real':
                    csv_header = [
                        'indice_tiempo',
                        'Tipo de cambio de Referencia',
                        'Tipo de cambio PTAX',
                        'Tipo de cambio SML Peso Real',
                        'Tipo de cambio SML Real Peso'
                    ]

                    csv_name = (config['real_file_path']
                                if config['real_file_path'].startswith('/')
                                else os.path.join(ROOT_DIR, config['real_file_path'])
                               )

                    write_file(csv_header, parsed['real'], csv_name)

        else:
            click.echo("No se encontraron resultados")

    except InvalidConfigurationError as err:
        click.echo(err)


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
def tce(ctx, config, start_date, end_date, use_intermediate_panel):

    try:
        config = read_config(file_path=config, command=ctx.command.name)
        validate_url_config(config)
        validate_url_has_value(config)
        validate_coins_key_config(config)
        validate_coins_key_has_values(config)
        validate_dates(start_date, end_date)
        validate_entities_key_config(config)
        validate_entities_key_has_values(config)
        intermediate_panel_path = (config['intermediate_panel_path']
                                   if config['intermediate_panel_path'].startswith('/')
                                   else os.path.join(ROOT_DIR, config['intermediate_panel_path'])
                                  )
        ensure_dir_exists(os.path.split(intermediate_panel_path)[0])

        scraper = BCRATCEScraper(
            url=config.get('url'),
            coins=config.get('coins'),
            entities=config.get('entities'),
            use_intermediate_panel=use_intermediate_panel,
            intermediate_panel_path=intermediate_panel_path
        )
        parsed = scraper.run(start_date, end_date)

        if parsed:
            for coin in ['dolar', 'euro']:
                csv_header = ['indice_tiempo']
                for entity in config.get('entities'):
                    for channel in ['mostrador', 'electronico']:
                        for flow in ['compra', 'venta']:
                            for hour in [11, 13, 15]:
                                csv_header.append(
                                    f'tc_ars_{coin}_{entity}_{channel}_{flow}_{hour}hs'
                                )

                if coin == 'dolar':
                    csv_name = (config['dolar_file_path']
                                if config['dolar_file_path'].startswith('/')
                                else os.path.join(ROOT_DIR, config['dolar_file_path'])
                               )
                    ensure_dir_exists(os.path.split(csv_name)[0])
                else:
                    csv_name = (config['euro_file_path']
                                if config['euro_file_path'].startswith('/')
                                else os.path.join(ROOT_DIR, config['euro_file_path'])
                               )
                    ensure_dir_exists(os.path.split(csv_name)[0])

                write_file(csv_header, parsed[coin], csv_name)

        else:
            click.echo("No se encontraron resultados")

    except InvalidConfigurationError as err:
        click.echo(err)
