#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import date

import click

from bcra_scraper.scraper import Scraper


def get_default_start_date():
    today = date.today()

    return f'{today.day}/{today.month}/{today.year}'

def get_default_end_date():
    today = date.today()

    return f'{today.day}/{today.month}/{today.year}'

# def arg1_validator(ctx, param, value):
#     breakpoint()
#     if ctx.args is not []:
#         raise click.BadParameter('Should be a positive, even integer.')
#     else:
#         return value

# def arg_validator(ctx, param, value):
#     breakpoint()
#     if ctx.args is not []:
#         raise click.BadParameter('Should be a positive, even integer.')
#     else:
#         return value

# validar q no se ingrese solo end_date
# validar q end_date >= start_date
@click.command()
@click.option(
    '--start-date',
    default=get_default_start_date,
    type=click.DateTime(formats=['%d/%m/%Y']),
    # callback=arg1_validator
    )
@click.option(
    '--end-date',
    default=get_default_end_date,
    type=click.DateTime(formats=['%d/%m/%Y']),
    # callback=arg_validator
    )
def main(start_date, end_date):
    start_date = date(start_date.year, start_date.month, start_date.day)
    end_date = date(end_date.year, end_date.month, end_date.day) 
    scraper = Scraper()
    parsed = scraper.run(start_date, end_date)
    click.echo(parsed)