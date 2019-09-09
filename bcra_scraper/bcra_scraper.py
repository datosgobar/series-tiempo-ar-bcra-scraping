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
    '--libor-csv-path',
    type=str
)
@click.option(
    '--intermediate-panel-path',
    type=str
)
@click.pass_context
def libor(ctx, start_date, end_date, config, use_intermediate_panel, libor_csv_path,
          intermediate_panel_path, *args, **kwargs):
    validate_dates(start_date, end_date)
    start_date = date(start_date.year, start_date.month, start_date.day)
    end_date = date(end_date.year, end_date.month, end_date.day)
    try:
        config = read_config(file_path=config, command=ctx.command.name)

        libor_file_path = libor_csv_path or config['libor_file_path']
        libor_file_path = (
            libor_file_path
            if libor_file_path.startswith('/')
            else os.path.join(ROOT_DIR, libor_file_path)
        )

        intermediate_panel_path = intermediate_panel_path or config['intermediate_panel_path']
        intermediate_panel_path = (
            intermediate_panel_path
            if intermediate_panel_path.startswith('/')
            else os.path.join(ROOT_DIR, intermediate_panel_path)
        )

        if os.path.isdir(libor_file_path):
            click.echo('Error: el path ingresado para tasas libor es un directorio')
            exit()
        elif os.path.isdir(intermediate_panel_path):
            click.echo('Error: el path ingresado para el panel intermedio es un directorio')
            exit()

        ensure_dir_exists(os.path.split(intermediate_panel_path)[0])
        ensure_dir_exists(os.path.split(libor_file_path)[0])

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

        write_file(processed_header, parsed, libor_file_path)

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
@click.option(
    '--tp-csv-path',
    type=str
)
@click.option(
    '--tc-csv-path',
    type=str
)
@click.option(
    '--intermediate-panel-path',
    type=str
)
@click.pass_context
def exchange_rates(ctx, start_date, end_date, config, use_intermediate_panel,
                   tp_csv_path, tc_csv_path, intermediate_panel_path):

    try:
        config = read_config(file_path=config, command=ctx.command.name)
        validate_url_config(config)
        validate_url_has_value(config)
        validate_coins_key_config(config)
        validate_coins_key_has_values(config)
        validate_dates(start_date, end_date)

        tp_file_path = tp_csv_path or config['tp_file_path']
        tp_file_path = (
            tp_file_path
            if tp_file_path.startswith('/')
            else os.path.join(ROOT_DIR, tp_file_path)
        )

        tc_file_path = tc_csv_path or config['tc_file_path']
        tc_file_path = (
            tc_file_path
            if tc_file_path.startswith('/')
            else os.path.join(ROOT_DIR, tc_file_path)
        )

        intermediate_panel_path = intermediate_panel_path or config['intermediate_panel_path']
        intermediate_panel_path = (
            intermediate_panel_path
            if intermediate_panel_path.startswith('/')
            else os.path.join(ROOT_DIR, intermediate_panel_path)
        )

        if os.path.isdir(tp_file_path):
            click.echo('Error: el path ingresado para tipo de pase usd es un directorio')
            exit()
        elif os.path.isdir(tc_file_path):
            click.echo('Error: el path ingresado para tipo de cambio local es un directorio')
            exit()
        elif os.path.isdir(intermediate_panel_path):
            click.echo('Error: el path ingresado para el panel intermedio es un directorio')
            exit()

        ensure_dir_exists(os.path.split(tp_file_path)[0])
        ensure_dir_exists(os.path.split(tc_file_path)[0])
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
            csv_header = ['indice_tiempo']
            csv_header.extend([v for v in coins.keys()])

            write_file(csv_header, parsed['tp_usd'], tp_file_path)

            write_file(csv_header, parsed['tc_local'], tc_file_path)

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
@click.option(
    '--uruguayo-csv-path',
    type=str
)
@click.option(
    '--real-csv-path',
    type=str
)
@click.option(
    '--intermediate-panel-path',
    type=str
)
@click.pass_context
def sml(ctx, config, start_date, end_date, use_intermediate_panel, uruguayo_csv_path,
        real_csv_path, intermediate_panel_path):

    try:
        config = read_config(file_path=config, command=ctx.command.name)
        validate_url_config(config)
        validate_url_has_value(config)
        validate_coins_key_config(config)
        validate_coins_key_has_values(config)
        validate_dates(start_date, end_date)

        peso_uruguayo_file_path = uruguayo_csv_path or config['peso_uruguayo_file_path']
        peso_uruguayo_file_path = (
            peso_uruguayo_file_path
            if peso_uruguayo_file_path.startswith('/')
            else os.path.join(ROOT_DIR, peso_uruguayo_file_path)
        )

        real_file_path = real_csv_path or config['real_file_path']
        real_file_path = (
            real_file_path
            if real_file_path.startswith('/')
            else os.path.join(ROOT_DIR, real_file_path)
        )

        intermediate_panel_path = intermediate_panel_path or config['intermediate_panel_path']
        intermediate_panel_path = (
            intermediate_panel_path
            if intermediate_panel_path.startswith('/')
            else os.path.join(ROOT_DIR, intermediate_panel_path)
        )

        if os.path.isdir(peso_uruguayo_file_path):
            click.echo('Error: el path ingresado para peso uruguayo es un directorio')
            exit()
        elif os.path.isdir(real_file_path):
            click.echo('Error: el path ingresado para real es un directorio')
            exit()
        elif os.path.isdir(intermediate_panel_path):
            click.echo('Error: el path ingresado para el panel intermedio es un directorio')
            exit()

        ensure_dir_exists(os.path.split(peso_uruguayo_file_path)[0])
        ensure_dir_exists(os.path.split(real_file_path)[0])
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

                    write_file(csv_header, parsed['peso_uruguayo'], peso_uruguayo_file_path)


                elif k == 'real':
                    csv_header = [
                        'indice_tiempo',
                        'Tipo de cambio de Referencia',
                        'Tipo de cambio PTAX',
                        'Tipo de cambio SML Peso Real',
                        'Tipo de cambio SML Real Peso'
                    ]

                    write_file(csv_header, parsed['real'], real_file_path)

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
@click.option(
    '--dolar-csv-path',
    type=str
)
@click.option(
    '--euro-csv-path',
    type=str
)
@click.option(
    '--intermediate-panel-path',
    type=str
)
@click.pass_context
def tce(ctx, config, start_date, end_date, use_intermediate_panel, dolar_csv_path,
        euro_csv_path, intermediate_panel_path):

    try:
        config = read_config(file_path=config, command=ctx.command.name)
        validate_url_config(config)
        validate_url_has_value(config)
        validate_coins_key_config(config)
        validate_coins_key_has_values(config)
        validate_dates(start_date, end_date)
        validate_entities_key_config(config)
        validate_entities_key_has_values(config)

        dolar_file_path = dolar_csv_path or config['dolar_file_path']
        dolar_file_path = (
            dolar_file_path
            if dolar_file_path.startswith('/')
            else os.path.join(ROOT_DIR, dolar_file_path)
        )

        euro_file_path = euro_csv_path or config['euro_file_path']
        euro_file_path = (
            euro_file_path
            if euro_file_path.startswith('/')
            else os.path.join()
        )

        intermediate_panel_path = intermediate_panel_path or config['intermediate_panel_path']
        intermediate_panel_path = (
            intermediate_panel_path
            if intermediate_panel_path.startswith('/')
            else os.path.join(ROOT_DIR, intermediate_panel_path)
        )

        if os.path.isdir(dolar_file_path):
            click.echo('Error: el path ingresado para dolar es un directorio')
            exit()
        elif os.path.isdir(euro_file_path):
            click.echo('Error: el path ingresado para euro es un directorio')
            exit()
        elif os.path.isdir(intermediate_panel_path):
            click.echo('Error: el path ingresado para el panel intermedio es un directorio')
            exit()

        ensure_dir_exists(os.path.split(dolar_file_path)[0])
        ensure_dir_exists(os.path.split(euro_file_path)[0])
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
                    csv_name = dolar_file_path
                else:
                    csv_name = euro_file_path

                write_file(csv_header, parsed[coin], csv_name)

        else:
            click.echo("No se encontraron resultados")

    except InvalidConfigurationError as err:
        click.echo(err)
