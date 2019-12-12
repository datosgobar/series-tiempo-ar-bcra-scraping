#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from csv import DictWriter
from datetime import date, datetime, timedelta
from email.utils import formatdate
from json import JSONDecodeError
import json
import logging
import os

import click

from bcra_scraper.exceptions import InvalidConfigurationError
from bcra_scraper.mails import Email

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

def validate_refetch_dates(start_date, end_date, refetch_from, refetch_to):
    if refetch_from < start_date:
        raise InvalidConfigurationError(
            "La fecha de refetch_from no debe ser menor a la fecha de inicio"
        )
    elif refetch_to > end_date:
        raise InvalidConfigurationError(
            "La fecha de refetch_from no puede ser mayor a la fecha de fin"
        )


def validate_entities_key_config(config):
    if 'entities' not in config:
        raise InvalidConfigurationError("La clave entities no existe")


def validate_entities_key_has_values(config):
    entities = config.get('entities', {})
    if entities == {}:
        raise InvalidConfigurationError("No existen valores para entities")


def validate_file_path(file_path, config, file_path_key):
    try:
        file_path = file_path or config.get(file_path_key)
        file_path = (
            file_path
            if file_path.startswith('/')
            else os.path.join(ROOT_DIR, file_path)
        )
    except Exception:
        raise InvalidConfigurationError(f"Error: No hay configuración para {file_path_key}")
    return file_path

def filter_parsed(parsed, csv_header):
    for v in list(parsed.values()):
        for r in list(v):
            if r not in csv_header:
                v.pop(r)
    return parsed

def get_csv_header(coin, config):
    csv_header = ['indice_tiempo']
    for k, v in config['entities'].items():
        for hour, channels in v['coins'][coin].items():
            for channel, state in channels['channels'].items():
                if state:
                    for flow in ['compra', 'venta']:
                        csv_header.append(
                            f'tc_ars_{coin}_{k}_{channel}_{flow}_{hour}hs'
                        )
    return csv_header

def generate_dates_range(first_date, last_date):
    delta = last_date - first_date
    dates_range = []
    for i in range(delta.days + 1):
        dates_range.append(first_date + timedelta(days=i))
    return dates_range


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
    '--refetch-from',
    default=None,
    type=click.DateTime(formats=['%d/%m/%Y']),
    )
@click.option(
    '--refetch-to',
    default=None,
    type=click.DateTime(formats=['%d/%m/%Y']),
    )
@click.option(
    '--config',
    default='config_general.json',
    type=click.Path(exists=True),
    )
@click.option(
    '--skip-intermediate-panel-data',
    default=False,
    is_flag=True,
    help=('Use este flag para no utilizar la lectura de datos desde un'
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
@click.option(
    '--skip-clean-last-dates',
    default=False,
    is_flag=True,
    help=('Use este flag para no volver a visitar las últimas fechas que no tengan datos')
)
@click.pass_context
def libor(ctx, start_date, end_date, refetch_from, refetch_to, config, skip_intermediate_panel_data, libor_csv_path,
          intermediate_panel_path, skip_clean_last_dates, *args, **kwargs):
    try:
        validate_dates(start_date, end_date)
        start_date = start_date.date()
        end_date = end_date.date()
        refetch_dates_range = []
        if refetch_from and refetch_to:
            validate_refetch_dates(start_date, end_date, refetch_from.date(), refetch_to.date())
            refetch_dates_range = generate_dates_range(refetch_from.date(), refetch_to.date())
        execution_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.basicConfig(level=logging.WARNING)
        config = read_config(file_path=config, command=ctx.command.name)
        libor_file_path = validate_file_path(libor_csv_path, config, file_path_key='libor_file_path')
        intermediate_panel_path = validate_file_path(intermediate_panel_path, config, file_path_key='intermediate_panel_path')

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

        timeout = (
            int(config.get('timeout'))
            if 'timeout' in config.keys() else None
        )
        tries = int(config.get('tries', 1))

        scraper = BCRALiborScraper(
            url=config.get('url'),
            timeout=timeout,
            tries=tries,
            rates=config.get('rates'),
            skip_intermediate_panel_data=skip_intermediate_panel_data,
            intermediate_panel_path=intermediate_panel_path,
            skip_clean_last_dates=skip_clean_last_dates
        )

        parsed = scraper.run(start_date, end_date, refetch_dates_range)

        processed_header = scraper.preprocess_header(scraper.rates)

        write_file(processed_header, parsed.values(), libor_file_path)

        execution_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        Email().send_validation_group_email(execution_start_time, execution_end_time, start_date, end_date, skip_intermediate_panel_data, identifier='libor')

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
    '--refetch-from',
    default=None,
    type=click.DateTime(formats=['%d/%m/%Y']),
    )
@click.option(
    '--refetch-to',
    default=None,
    type=click.DateTime(formats=['%d/%m/%Y']),
    )
@click.option(
    '--config',
    default='config_general.json',
    type=click.Path(exists=True),
    )
@click.option(
    '--skip-intermediate-panel-data',
    default=False,
    is_flag=True,
    help=('Use este flag para no utilizar la lectura de datos desde un'
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
@click.option(
    '--skip-clean-last-dates',
    default=False,
    is_flag=True,
    help=('Use este flag para no volver a visitar las últimas fechas que no tengan datos')
)
@click.pass_context
def exchange_rates(ctx, start_date, end_date, refetch_from, refetch_to, config, skip_intermediate_panel_data,
                   tp_csv_path, tc_csv_path, intermediate_panel_path, skip_clean_last_dates):

    try:
        execution_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.basicConfig(level=logging.WARNING)
        config = read_config(file_path=config, command=ctx.command.name)
        validate_url_config(config)
        validate_url_has_value(config)
        validate_coins_key_config(config)
        validate_coins_key_has_values(config)
        validate_dates(start_date, end_date)
        start_date = start_date.date()
        end_date = end_date.date()
        refetch_dates_range = []
        if refetch_from and refetch_to:
            validate_refetch_dates(start_date, end_date, refetch_from.date(), refetch_to.date())
            refetch_dates_range = generate_dates_range(refetch_from.date(), refetch_to.date())

        tp_file_path = validate_file_path(tp_csv_path, config, file_path_key='tp_file_path')
        tc_file_path = validate_file_path(tc_csv_path, config, file_path_key='tc_file_path')
        intermediate_panel_path = validate_file_path(intermediate_panel_path, config, file_path_key='intermediate_panel_path')

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

        timeout = (
            int(config.get('timeout'))
            if 'timeout' in config.keys() else None
        )
        tries = int(config.get('tries', 1))

        scraper = BCRAExchangeRateScraper(
            url=config.get('url'),
            timeout=timeout,
            tries=tries,
            coins=config.get('coins'),
            skip_intermediate_panel_data=skip_intermediate_panel_data,
            intermediate_panel_path=intermediate_panel_path,
            skip_clean_last_dates=skip_clean_last_dates
        )
        parsed = scraper.run(start_date, end_date, refetch_dates_range)

        if parsed:
            coins = config.get('coins')
            csv_header = ['indice_tiempo']
            csv_header.extend([v for v in coins.keys()])

            write_file(csv_header, parsed['tp_usd'].values(), tp_file_path)
            write_file(csv_header, parsed['tc_local'].values(), tc_file_path)

        else:
            click.echo("No se encontraron resultados")
        execution_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        Email().send_validation_group_email(execution_start_time, execution_end_time, start_date, end_date, skip_intermediate_panel_data, identifier='exchange-rates')

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
    '--refetch-from',
    default=None,
    type=click.DateTime(formats=['%d/%m/%Y']),
    )
@click.option(
    '--refetch-to',
    default=None,
    type=click.DateTime(formats=['%d/%m/%Y']),
    )
@click.option(
    '--config',
    default='config_general.json',
    type=click.Path(exists=True),
)
@click.option(
    '--skip-intermediate-panel-data',
    default=False,
    is_flag=True,
    help=('Use este flag para no utilizar la lectura de datos desde un'
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
@click.option(
    '--skip-clean-last-dates',
    default=False,
    is_flag=True,
    help=('Use este flag para no volver a visitar las últimas fechas que no tengan datos')
)
@click.pass_context
def sml(ctx, config, start_date, end_date, refetch_from, refetch_to, skip_intermediate_panel_data, uruguayo_csv_path,
        real_csv_path, intermediate_panel_path, skip_clean_last_dates):

    try:
        execution_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.basicConfig(level=logging.WARNING)
        config = read_config(file_path=config, command=ctx.command.name)
        validate_url_config(config)
        validate_url_has_value(config)
        validate_coins_key_config(config)
        validate_coins_key_has_values(config)
        validate_dates(start_date, end_date)
        start_date = start_date.date()
        end_date = end_date.date()
        refetch_dates_range = []
        if refetch_from and refetch_to:
            validate_refetch_dates(start_date, end_date, refetch_from.date(), refetch_to.date())
            refetch_dates_range = generate_dates_range(refetch_from.date(), refetch_to.date())

        peso_uruguayo_file_path = validate_file_path(uruguayo_csv_path, config, file_path_key='peso_uruguayo_file_path')
        real_file_path = validate_file_path(real_csv_path, config, file_path_key='real_file_path')
        intermediate_panel_path = validate_file_path(intermediate_panel_path, config, file_path_key='intermediate_panel_path')

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

        timeout = (
            int(config.get('timeout'))
            if 'timeout' in config.keys() else None
        )
        tries = int(config.get('tries', 1))

        scraper = BCRASMLScraper(
            url=config.get('url'),
            timeout=timeout,
            tries=tries,
            coins=config.get('coins'),
            types=config.get('types'),
            skip_intermediate_panel_data=skip_intermediate_panel_data,
            intermediate_panel_path=intermediate_panel_path,
            skip_clean_last_dates=skip_clean_last_dates
        )

        parsed = scraper.run(start_date, end_date, refetch_dates_range)

        if parsed:
            for k  in parsed.keys():
                if k == 'peso_uruguayo':
                    csv_header = ['indice_tiempo']
                    csv_header.extend(config['types']['peso_uruguayo'].values())
                    write_file(csv_header, parsed['peso_uruguayo'].values(), peso_uruguayo_file_path)


                elif k == 'real':
                    csv_header = ['indice_tiempo']
                    csv_header.extend(config['types']['real'].values())

                    write_file(csv_header, parsed['real'].values(), real_file_path)

        else:
            click.echo("No se encontraron resultados")
        execution_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        Email().send_validation_group_email(execution_start_time, execution_end_time, start_date, end_date, skip_intermediate_panel_data, identifier='sml')
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
    '--refetch-from',
    default=None,
    type=click.DateTime(formats=['%d/%m/%Y']),
    )
@click.option(
    '--refetch-to',
    default=None,
    type=click.DateTime(formats=['%d/%m/%Y']),
    )
@click.option(
    '--config',
    default='config_general.json',
    type=click.Path(exists=True),
)
@click.option(
    '--skip-intermediate-panel-data',
    default=False,
    is_flag=True,
    help=('Use este flag para no utilizar la lectura de datos desde un'
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
@click.option(
    '--skip-clean-last-dates',
    default=False,
    is_flag=True,
    help=('Use este flag para no volver a visitar las últimas fechas que no tengan datos')
)
@click.pass_context
def tce(ctx, config, start_date, end_date, refetch_from, refetch_to, skip_intermediate_panel_data, dolar_csv_path,
        euro_csv_path, intermediate_panel_path, skip_clean_last_dates):

    try:
        execution_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.basicConfig(level=logging.WARNING)
        config = read_config(file_path=config, command=ctx.command.name)
        validate_url_config(config)
        validate_url_has_value(config)
        validate_coins_key_config(config)
        validate_coins_key_has_values(config)
        validate_dates(start_date, end_date)
        validate_entities_key_config(config)
        validate_entities_key_has_values(config)
        start_date = start_date.date()
        end_date = end_date.date()
        refetch_dates_range = []
        if refetch_from and refetch_to:
            validate_refetch_dates(start_date, end_date, refetch_from.date(), refetch_to.date())
            refetch_dates_range = generate_dates_range(refetch_from.date(), refetch_to.date())

        dolar_file_path = validate_file_path(dolar_csv_path, config, file_path_key='dolar_file_path')
        euro_file_path = validate_file_path(euro_csv_path, config, file_path_key='euro_file_path')
        intermediate_panel_path = validate_file_path(intermediate_panel_path, config, file_path_key='intermediate_panel_path')

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

        timeout = (
            int(config.get('timeout'))
            if 'timeout' in config.keys() else None
        )
        tries = int(config.get('tries', 1))

        scraper = BCRATCEScraper(
            url=config.get('url'),
            timeout=timeout,
            tries=tries,
            coins=config.get('coins'),
            entities=config.get('entities'),
            skip_intermediate_panel_data=skip_intermediate_panel_data,
            intermediate_panel_path=intermediate_panel_path,
            skip_clean_last_dates=skip_clean_last_dates
        )
        parsed = scraper.run(start_date, end_date, refetch_dates_range)

        if parsed:
            for coin in ['dolar', 'euro']:
                csv_header = get_csv_header(coin, config)
                if coin == 'dolar':
                    csv_name = dolar_file_path
                else:
                    csv_name = euro_file_path

                filtered_parsed = filter_parsed(parsed[coin], csv_header)
                write_file(csv_header, filtered_parsed.values(), csv_name)

        else:
            click.echo("No se encontraron resultados")
        execution_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        Email().send_validation_group_email(execution_start_time, execution_end_time, start_date, end_date, skip_intermediate_panel_data, identifier='tce')

    except InvalidConfigurationError as err:
        click.echo(err)
