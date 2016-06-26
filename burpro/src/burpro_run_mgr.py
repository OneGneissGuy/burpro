# -*- coding: utf-8 -*-
"""
:DESCRIPTION: This code reads configuration information and launches
              processing of input data

:REQUIRES: burpro_process.py, .json configuration files

:#TODO:
1) Add support to read in multiple files in a directory

:AUTHOR: John Franco Saraceno, John M. Donovan
:ORGANIZATION: U.S. Geological Survey, United States Department of Interior
:CONTACT: saraceno@usgs.gov, jmd@usgs.gov

"""
# =============================================================================
# IMPORT STATEMENTS
# =============================================================================
from __future__ import print_function
import os
import os.path
import logging
import json
import validictory

from burpro_process import process


def manage_run(exo_filename, output_dir):

    log = logging.getLogger('BurPro')
    log.info('Reading configuration...')

    params = read_json_params()
    process(exo_filename, output_dir, params)


def read_json_params():
    #TODO: hierarchal json support
    #TODO: Look for json exo file direc then look in bat directory, etc.
    script_path, script_name_only = os.path.split(os.path.realpath(__file__))
    json_filename = os.path.join(script_path, 'config', 'run_params.json')
    #    # read json file

    validate_json(json_filename)
    run_params = read_json_file(json_filename)
    params = run_params['gov.usgs.cawsc.bgctech.burpro']

    return params


def read_json_file(json_file_path):
    """This function reads in a json file and outputs the info
    as a python dictionary"""
    try:
        with open(json_file_path) as data_file:
            json_data = json.load(data_file)
    except IOError, ioex:
        print(os.strerror(ioex.errno), json_file_path, sep=" ")
    else:
        return json_data


def schema_json():
    #TODO: read in schema from a json file
    schema = {
        "type": "object",
        "properties": {
            "drop_cols": {
                "type": "array",
                "required": True
            },
            "mad_criteria": {
                "type": "number",
                "required": False,
                "minimum": 2,
                "maximum": 3,
            },
            "interval": {
                "type": "integer",
                "required": False,
                "minimum": 15,
                "maximum": 60,
            },
            "index_timezone": {
                "type": "string",
                "required": True
            }
            }
    }
    return schema


def validate_json(json_data_file):
    """this function validates a json file based
        on schema_json func return"""
    json_data = read_json_file(json_data_file)
    json_data = json_data[json_data.keys()[0]]
    schema = schema_json()
    try:
        validictory.validate(json_data, schema)
    except ValueError, error:
        #        print('Check json file format for errors')
        print(error.message)
    finally:
        return
