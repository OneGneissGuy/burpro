# -*- coding: utf-8 -*-
"""burpro project"""
from setuptools import setup
from setuptools import find_packages
pkgs = find_packages()

with open('README.RST') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()
url = 'https://my.usgs.gov/bitbucket/projects/BGCTECH/repos/burpro/browse'
setup(name='burpro',
      version='1.1',
      description='A module to process burst XYLEM EXO .xls data files',
      long_description=readme,
      author='John Franco Saraceno',
      author_email='saraceno@usgs.gov',
      url=url,
      download_url=url,
      install_requires=['numpy', 'pandas', 'statsmodels'],
      license=license,
      packages=pkgs,
      include_package_data=True,
      )
