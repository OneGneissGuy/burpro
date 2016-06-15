import json
import os

import numpy as np
import numpy.ma as ma
import statsmodels.robust.scale as smc

import validictory


def custom_mad(array_like, criteria=2.5,):
# TODO: Add support for all NAN arrays
    """Function to calculate the median absoilute deviation of an array
    INPUT:
    array-like
    RETURNS:
    float"""
    MAD = smc.mad(array_like)
    k = (MAD*criteria)
    M = np.nanmedian(array_like)
    high = M + k
    low = M - k
    b = ma.masked_outside(array_like, high, low)
    c = ma.compressed(b)
    return np.nanmedian(c)


def drop_columns(dataframe, cols):
    """This function drops dataframe columns contained in cols
    INPUT:
    pandas dataframe
    list of column names, list like
    RETURNS:
    pandas dataframe less columns in cols"""
    frame = dataframe.copy()
    for i in cols:
        if i in frame.columns:
            frame.drop(i, inplace=True, axis=1)
    return frame


def find_col_idx(params, field):
    return [i for i, s in enumerate(params) if field in s]


def has_numbers(inputString):
    """This function identifies strings that contain numerical characters
    INPUT:
    string, string like
    RETURNS:
    bool"""
    try:
        string = any(char.isdigit() for char in inputString)
    except TypeError:
        print 'argument must be a string'
    else:
        return string


def read_json_file(json_file_path):
    """This function reads in a json file and outputs the info
    as a python dictionary"""
    try:
        with open(json_file_path) as data_file:
            json_data = json.load(data_file)
    except IOError, ioex:
        print os.strerror(ioex.errno), json_file_path
    else:
        return json_data


def schema_json():
    #TODO: read in schema from a file
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
#        print 'Check json file format for errors'
        print error
    finally:
        return
