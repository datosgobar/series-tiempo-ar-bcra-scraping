#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import date

import click

from bcra_scraper.scraper import Scraper


@click.command()
def main():
    scraper = Scraper()
    parsed = scraper.run()
    click.echo(parsed)

if __name__ == '__main__':
    main()
