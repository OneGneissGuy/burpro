# -*- coding: utf-8 -*-
"""
:DESCRIPTION: Handles a single run processing of a EXO KOR Burst data file

:REQUIRES: .xlsx burst data files in cwd folder "data"

:#TODO:
1) Add support to write mad files to csv format

:AUTHOR: John Franco Saraceno, John M. Donovan
:ORGANIZATION: U.S. Geological Survey, United States Department of Interior
:CONTACT: saraceno@usgs.gov, jmd@usgs.gov

"""
# =============================================================================
# IMPORT STATEMENTS
# =============================================================================
import logging
import os
import sys
import datetime

import numpy as np
import pandas as pd
import numpy.ma as ma
import statsmodels.robust.scale as smc


def process(exo_filename, output_dir, params):
    
    interval = params.get('interval', 15)
    drop_cols = params.get('drop_cols', [])
    index_timezone = params.get('index_timezone', 'Datetime (PST)')
    mad_criteria = params.get('mad_criteria', 2.5)
    
    date_col = drop_cols[0]
    time_col = drop_cols[1]
    # end constants
    
    log = logging.getLogger('BurPro')
    log.info('Reading input...')

    null_value = -9999
    if os.path.isfile(exo_filename):
        # if .xlsx file exists, then read it into a dataframe
        df_exo = pd.read_excel(exo_filename, header=None)
    else:
        # otherwise, break out of the script with an error message
        sys.exit("filepath: '%s' not found" % exo_filename)
        
    log.info('Processing...')
    
    # make a copy of the read in dataframe for processing
    df_exo_float, grouped = process_data_frame(df_exo, date_col, time_col, drop_cols, null_value, index_timezone, interval)

    # calc median absolute deviation
    exo_mad = calc_med_abs_dev(log, df_exo_float, grouped, mad_criteria, null_value)

    write_output(log, output_dir, exo_filename, exo_mad)
    log.info('Processing complete.')
    
def process_data_frame(df_exo, date_col, time_col, drop_cols, null_value, index_timezone, interval):
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
                                   
    return df_exo_float, grouped
                                   
def calc_med_abs_dev(log, df_exo_float, grouped, mad_criteria, null_value):
    exo_mad = pd.DataFrame()
    # apply the mad calculation column wise to data frame
    for i in np.arange(0, len(df_exo_float.columns), 1):
        step_number = '    (' + str(i+1) + ')'
        log.info(step_number)
        exo_mad[df_exo_float.columns[i]] = grouped[
                                           df_exo_float.columns[i]].apply(
                                           custom_mad, criteria=mad_criteria)
    exo_mad.replace(to_replace=null_value, value=np.nan, inplace=True)
    
    return exo_mad
    
def write_output(log, output_dir, exo_filename, exo_mad):
    log.info('Writing output...')
    input_path, input_name_only = os.path.split(exo_filename)
    output_name_only = input_name_only.replace(".xlsx", "_mad.xlsx")
    output_filename = os.path.join(output_dir, output_name_only)
    exo_mad.to_excel(output_filename)
    # write csv
    #    exo_mad.to_csv(exo_filename.replace(".xlsx", "_mad.csv"))


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

