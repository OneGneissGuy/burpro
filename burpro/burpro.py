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
import argparse
import datetime
import os
import sys

import numpy as np
import pandas as pd

from helper_funcs import custom_mad, drop_columns, has_numbers, read_json_file

# =============================================================================
# MAIN METHOD AND TESTING AREA
# =============================================================================


def main(**run_params):
    print 'Run Started!'
    print run_params
    params = run_params['gov.usgs.cawsc.bgctech.burpro']

    filename = os.sep.join([params['directory'], params['filename']])
    interval = params['interval']
    drop_cols = params['drop_cols']
    index_timezone = params['index_timezone']
    mad_criteria = params['mad_criteria']

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
#    sn_start = frame.iloc[:, 0].isin([u"EXO2 Sonde"]).idxmax(axis=0,
#                                                             skipna=True)
    # find starting row by locating indicator date field
    nrow = frame.iloc[:, 0].isin([date_col]).idxmax(axis=0,
                                                    skipna=True)
    # grab list of probes by model name
#    probe = frame.iloc[sn_start:nrow-2, 0].tolist()
    # grab list of probe serial numbers
#    sn = frame.iloc[sn_start:nrow-2, 1].tolist()
    # grab list of probe firmware versions
#    firmware = frame.iloc[sn_start:nrow-2, 2].tolist()
    # combine probe information into dicts
#    sensors = dict(zip(probe, sn))
#    sensors_fw = dict(zip(probe, firmware))
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
#    df_date = frame[date_col].copy()
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
#    dup_params = ["fDOM RFU",
#                  u"fDOM QSU",
#                  u"Chlorophyll RFU",
#                  u"Chlorophyll µg/L",
#                  u"BGA-PC RFU",
#                  u"BGA-PC µg/L",
#                  ]
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
    # calc median absolute deviation
    exo_mad = pd.DataFrame()
    # apply the mad calculation column wise to data frame
    for i in np.arange(0, len(df_exo_float.columns), 1):
        exo_mad[df_exo_float.columns[i]] = grouped[
                                           df_exo_float.columns[i]].apply(
                                           custom_mad, criteria=mad_criteria)
    exo_mad.replace(to_replace=null_value, value=np.nan, inplace=True)
    exo_mad.to_excel(filename.replace(".xlsx", "_mad.xlsx"))
    # write csv
    # exo_mad.to_csv(filename.replace(".xlsx", "_mad.csv"))
    print 'Run completed!'

# %%
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=" JSON run settings file")
    parser.add_argument('filename', type=str)
    # get json file path passed to script at commandline
    json_filename = parser.parse_args()
    # read json file
    print 'reading json file:', json_filename.filename
    kwargs = read_json_file(json_filename.filename)
    print kwargs
    # pass run params from json file onto main program
    main(**kwargs)
