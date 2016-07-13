# -*- coding: utf-8 -*-
"""
:DESCRIPTION: This reads command line arguments and sets up
              logging and an output directory for BurPro

:REQUIRES: burpro.py, .xlsx burst data files in cwd folder "data"

:AUTHOR: John Franco Saraceno, John M. Donovan
:ORGANIZATION: U.S. Geological Survey, United States Department of Interior
:CONTACT: saraceno@usgs.gov, jmd@usgs.gov

TODO:Convert all print statments to Py3
"""
# =============================================================================
# IMPORT STATEMENTS
# =============================================================================
from __future__ import print_function
import argparse
import datetime
import getpass
import logging
import os
import os.path
import sys
import traceback


# Override error handling in the parser library
class BurProArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise Exception(message)


def setup_logger(logger_name, log_file, level=logging.INFO):
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)


def report_setup_error(error):
    print >>sys.stderr, 'BurPro Setup Error: ', error
    traceback.print_exc()
    print >>sys.stderr, 'Exiting.'
    sys.exit(2)


def handle_args(version, argv=None):
    if argv is None:
        argv = sys.argv
    if len(sys.argv) < 2:
        raise Exception('BurPro must be given an input file for processing')

    print('USGS California Water Science Center')
    print('BurPro Revision', version, sep=' ')
    print('Reading run parameters...')

    parser = BurProArgumentParser(
             description="KOR exo file")
    parser.add_argument('exo_filename', type=str)
    input_path = parser.parse_args()

    return input_path.exo_filename


def setup_output_dir(exo_filename):
    dir_name = "BurPro_" + getpass.getuser() + "_"
    dir_name = dir_name + datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    base_path = os.path.dirname(exo_filename)
    output_dir = os.path.join(base_path, dir_name)
    print('Writing output to', output_dir, sep=' ')
    os.makedirs(output_dir)

    return output_dir
