# -*- coding: utf-8 -*-
"""burpro project"""
from setuptools import setup
from setuptools import find_packages
pkgs = find_packages()

with open('README.*') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(name = 'burpro',
    version = '0.1',
    description = 'burpro module',
    long_description = readme,
    platforms = ['Microsoft :: Windows :: Windows 7'],
    author = 'John Franco Saraceno',
    author_email = 'saraceno@usgs.gov',
    url = 'URL to get it at.',
    download_url = 'Where to download it.',
    install_requires = ['nose'],
    scripts = [],
    Development = ['Development Status :: 1 - Planning'],
    license = license,
    packages = pkgs,
    include_package_data = True,
    )