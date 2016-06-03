# -*- coding: utf-8 -*-
"""
:DESCRIPTION: This code processes EXO KOR Burst data files

:REQUIRES: helper_funcs.py, .xlsx burst data files in cwd folder "data"

:TODO: Add support to read in multiple files in a directory

:AUTHOR: John Franco Saraceno
:ORGANIZATION: U.S. Geological Survey, United States Department of Interior
:CONTACT: saraceno@usgs.gov
:VERSION: 0.1
Tue May 31 17:03:37 2016
"""
# =============================================================================
# IMPORT STATEMENTS
# =============================================================================
import datetime
import os
import json
import sys

import numpy as np
import pandas as pd

from helper_funcs import custom_mad, drop_columns, has_numbers
# =============================================================================
# METHODS


def read_json_file(json_file_path):
    """This function reads in a json file and outputs the info
    as a python dictionary"""
    try:
        with open(json_file_path) as data_file:
            json_data = json.load(data_file)
    except IOError as e:
        print e
    else:
        return json_data

# =============================================================================

# =============================================================================
# MAIN METHOD AND TESTING AREA
# =============================================================================


def main(**kwargs):
    print kwargs

# %%
if __name__ == "__main__":
    # read json file
    p = read_json_file(r'json_files\run_params.json')
    params = p['gov.usgs.cawsc.bgctech.burpro']
    filename = os.sep.join([params['directory'], params['filename']])
    interval = params['interval']
    drop_cols = params['drop_cols']
    index_timezone = params['index_timezone']
    mad_criteria = params['mad_criteria']
    # constants
#    filename = r"data\TOE_12G104073_021116_150000.xlsx"
#    interval = 15
#    mad_criteria = 2.5
#    index_timezone = "Datetime (PST)"
#    drop_cols = ["Date (MM/DD/YYYY)",
#                 "Time (HH:MM:SS)",
#                 u"Site Name",
#                 u"date",
#                 u"Time (Fract. Sec)",
#                 u"Fault Code",
#                 u"Battery V",
#                 u"Cable Pwr V",
#                 u"TSS mg/L",
#                 u"TDS mg/L",
#                 u"Press psi a",
#                 u"Depth m",
#                 u"Sal psu",
#                 u"nLF Cond µS/cm",
#                 u"Cond µS/cm"]
    date_col = drop_cols[0]
    time_col = drop_cols[1]
    # end constants
    null_value = -9999
    if os.path.isfile(filename):
        # if .xlsx file exists, then read it into a dataframe
        df_exo = pd.read_excel(filename, header=None)
    else:
        # otherwise, break out of the script with an error message
        sys.exit("filepath: '%s' not found" % filename)
        # make a copy of the read in dataframe for processing
    frame = df_exo.copy()
    # find starting row by locating Sonde model indicator field
    sn_start = frame.iloc[:, 0].isin([u"EXO2 Sonde"]).idxmax(axis=0,
                                                             skipna=True)
    # find starting row by locating indicator date field
    nrow = frame.iloc[:, 0].isin([date_col]).idxmax(axis=0,
                                                    skipna=True)
    # grab list of probes by model name
    probe = frame.iloc[sn_start:nrow-2, 0].tolist()
    # grab list of probe serial numbers
    sn = frame.iloc[sn_start:nrow-2, 1].tolist()
    # grab list of probe firmware versions
    firmware = frame.iloc[sn_start:nrow-2, 2].tolist()
    # combine probe information into dicts
    sensors = dict(zip(probe, sn))
    sensors_fw = dict(zip(probe, firmware))
    # lasso sensor data located in the dataframe
    frame = frame.iloc[nrow:, :]
    # set the dataframe column keys to the first row in the dataframe
    frame.columns = frame.iloc[0, :]
    # rename duplicate columns for sensor swaps
    cols = pd.Series(frame.columns)
    for dup in frame.columns.get_duplicates():
        cols[frame.columns.get_loc(dup)] = [dup + "." + str(d_idx)
                                            if d_idx != 0 else dup
                                            for d_idx in
                                            range(
                                            frame.columns.get_loc(dup).sum())]
    frame.columns = cols
    frame.drop(frame.index[0], inplace=True)
    # create dataframe of/from date col
    df_date = frame[date_col].copy()
    # create dataframe of/from time col
    df_time = frame[time_col].copy()
    # convert time data to a string
    df_time = df_time.astype(str)
    # create a new date + time column from date and time dataframes
    frame["date"] = frame[date_col].apply(
                           lambda x: datetime.datetime.strftime(x, "%Y-%m-%d"))
    # convert new date + time colum to date time index and set a df"s index
    frame.index = pd.to_datetime(frame["date"] + " " + df_time)
    # remove columns that arent needed

    # drop unnecessary cols from data frame, frame
    frame = drop_columns(frame, drop_cols)
    # concat like columns with different serials from sensor swaps
    params = list(frame)
    dup_params = ["fDOM RFU",
                  u"fDOM QSU",
                  u"Chlorophyll RFU",
                  u"Chlorophyll µg/L",
                  u"BGA-PC RFU",
                  u"BGA-PC µg/L",
                  ]
    # now drop any column names that have numbers in them
    for i in params:
        if has_numbers(i):
            frame.drop(i, axis=1, inplace=True)
    frame.fillna(null_value, inplace=True)
    # rename index axis
    frame.index.name = index_timezone
    # convert dataframe contents to floats for stat. analysis
    df_exo_float = frame.astype("float", copy=True)
    # group bursts by interval
    grouped = df_exo_float.groupby(pd.TimeGrouper(str(interval) + "Min"),
                                   sort=False)
    # calc median
    # aggregate bursts by interval and apply the built in median function
    exo_median = grouped.aggregate("median")
    # replace the null values to nans so they are written as blanks in xlsx
    exo_median.replace(to_replace=null_value, value=np.nan, inplace=True)
    # write dataframe to xlsx datafile
    exo_median.to_excel(fin.replace(".xlsx", "_median.xlsx"))
    # calc mean
    exo_mean = grouped.aggregate("mean")
    exo_mean.replace(to_replace=null_value, value=np.nan, inplace=True)
    exo_mean.to_excel(fin.replace(".xlsx", "_mean.xlsx"))
    # calc median absolute deviation
    exo_mad = pd.DataFrame()
    # apply the mad calculation column wise to data frame
    for i in np.arange(0, len(df_exo_float.columns), 1):
        exo_mad[df_exo_float.columns[i]] = grouped[
                                           df_exo_float.columns[i]].apply(
                                           custom_mad, criteria=mad_criteria)
    exo_mad.replace(to_replace=null_value, value=np.nan, inplace=True)
    exo_mad.to_excel(fin.replace(".xlsx", "_mad.xlsx"))
