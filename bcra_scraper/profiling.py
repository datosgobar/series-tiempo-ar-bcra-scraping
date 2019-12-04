#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Decorador auxiliar

Debe instalarse 'graphviz' en el sistema para que funcione.

    Ubuntu: sudo apt-get install graphviz
    Mac: brew install graphviz
"""

import os
import sys
import vcr

from functools import wraps
from pycallgraph import PyCallGraph
from pycallgraph import Config
from pycallgraph import GlobbingFilter
from pycallgraph.output import GraphvizOutput

# módulo de ejemplo que se quiere analizar
from bcra_scraper import tce

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DIR = os.path.join(ROOT_DIR, "config")

SAMPLES_DIR = os.path.join(ROOT_DIR, "tests", "samples")
TEMP_DIR = os.path.join(ROOT_DIR, "tests", "temp")
PROFILING_DIR = os.path.join(ROOT_DIR, "tests", "profiling")
os.makedirs(PROFILING_DIR) if not os.path.exists(PROFILING_DIR) else None

VCR = vcr.VCR(path_transformer=vcr.VCR.ensure_suffix('.yaml'),
              cassette_library_dir=os.path.join(
                  "tests", "cassetes", "profiling"),
              record_mode='once')


def profile(profiling_result_path):
    """Decorador de una función para que se corra haciendo profiling."""

    def fn_decorator(fn):
        """Decora una función con el análisis de profiling."""

        @wraps(fn)
        def fn_decorated(*args, **kwargs):
            """Crea la función decorada."""

            graphviz = GraphvizOutput()
            graphviz.output_file = profiling_result_path

            with PyCallGraph(output=graphviz, config=None):
                fn(*args, **kwargs)

        return fn_decorated
    return fn_decorator


@VCR.use_cassette()
@profile("tests/profiling/profiling_test.png")
def main():
    """Hace un profiling del scraping de una distribución."""

    tce(ctx, config, start_date, end_date, skip_intermediate_panel_data, dolar_csv_path,
        euro_csv_path, intermediate_panel_path)


if __name__ == '__main__':
    main()
