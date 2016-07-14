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
from itertools import chain
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


def takedown_logger(logger_name):
    l = logging.getLogger(logger_name)
    l.handlers = [
        h for h in l.handlers if not isinstance(h, logging.StreamHandler)]


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
    parser.add_argument('nargs', nargs='+')

    args = []
    for _, value in parser.parse_args()._get_kwargs():
        if value is not None:
            args.append(value)
#    print(args)
    args = list(chain.from_iterable(args))
    for arg in args:
        list_of_args = arg.split(' ')


    lof = []
    if len(list_of_args) == 1:  # its one file or one directory
        if os.path.isdir(list_of_args[0]):  # its a directory
            direc = list_of_args[0]
            lof = find_kor_files(direc)
        else:  # its a file or list of files
            lof = list_of_args
    else:  # its a file or its multiple files or multiple directories or a combo!
        lof = list_of_args
    return lof

#def handle_args(version, argv=None):
#    if argv is None:
#        argv = sys.argv
#    if len(sys.argv) < 2:
#        raise Exception('BurPro must be given an input file for processing')
#    print('USGS California Water Science Center')
#    print('BurPro Revision', version, sep=' ')
#    print('Reading run parameters...')
#    parser = BurProArgumentParser(
#             description="KOR exo file")
#    parser.add_argument('nargs', nargs='+')
##    input_path = parser.parse_args()
#    files = []
#    for _, value in parser.parse_args()._get_kwargs():
#        if value is not None:
#            files.append(value)
#    files = list(chain.from_iterable(files))
#    # files = []
#    for fil in files:
#        list_of_files = fil.split(' ')
#    return list_of_files


def find_kor_files(direc):
    lof = []
    if os.path.isdir(direc):
        for root, dirs, files in os.walk(direc, topdown=False):
            for name in files:
                lof.append(os.path.join(root, name))

        xls_files = [d for d in lof if d.endswith('.xlsx')]
        kor_files = [d for d in xls_files if 'mad' not in d]
        return kor_files


def setup_output_dir(exo_filename):
    dir_name = "BurPro_" + getpass.getuser() + "_"
    dir_name = dir_name + datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    base_path = os.path.dirname(exo_filename)
    output_dir = os.path.join(base_path, dir_name)
    print('Writing output to', output_dir, sep=' ')
    os.makedirs(output_dir)

    return output_dir
