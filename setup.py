#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

with open("requirements.txt") as f:
    requirements = [req.strip() for req in f.readlines()]

with open("requirements_dev.txt") as f:
    test_requirements = [req.strip() for req in f.readlines()]

setup(
    name='bcra_scraper',
    version='0.1.0',
    description="Descripción corta del proyecto.",
    long_description=readme + '\n\n' + history,
    author="BCRA Scraper",
    author_email='datos@modernizacion.gob.ar',
    url='https://github.com/datosgobar/bcra_scraper',
    packages=[
        'bcra_scraper',
    ],
    package_dir={'bcra_scraper':
                 'bcra_scraper'},
    include_package_data=True,
    install_requires=requirements,
    entry_points='''
        [console_scripts]
        bcra_scraper=bcra_scraper.bcra_scraper:cli
    ''',
    license="MIT license",
    zip_safe=False,
    keywords='bcra_scraper',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
