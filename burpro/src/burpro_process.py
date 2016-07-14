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
from __future__ import print_function
import datetime
import getpass
import json
import logging
import os

import numpy as np
import pandas as pd
import numpy.ma as ma
import statsmodels.robust.scale as smc

# from burpro_setup import setup_logging, report_setup_error


def fetch_file_metadata(dataframe, drop_cols):
    #    def rd_kor_exo_file(filename):
    #    frame = pd.read_excel(filename, header=None,)
    #    frame = pd.read_excel(file_path, header=None,)
    #    frame.to_hdf('temp.hd5', 'df')
    #    frame = pd.read_hdf('temp.hd5')
    frame = dataframe.copy()
    date_col = drop_cols[0]
    time_col = drop_cols[1]
    # find starting row by locating Sonde model indicator field
    nrow = frame.iloc[:, 0].isin([date_col]).idxmax(axis=0, skipna=True)

    devices = extract_sensor_metadata(frame, nrow)
    dev_col_nums = extract_data_cols(frame, nrow)
    dev_cols = return_col_names(dev_col_nums, frame.columns.tolist())

    frame = frame.iloc[nrow:, :]
    frame.columns = frame.iloc[0, :]
    # rename duplicate columns of sensor swaps
    cols = pd.Series(frame.columns)  # change to: cols= frame.columns.tolist()
    for dup in frame.columns.get_duplicates():
        cols[frame.columns.get_loc(dup)] = [dup + '.' + str(d_idx)
                                            if d_idx != 0 else dup
                                            for d_idx in range(
                                            frame.columns.get_loc(dup).sum())]
    frame.columns = cols
    frame.drop(frame.index[0], inplace=True)  # drop header row

    frame_drop_col = drop_columns(frame, drop_cols)
    frame_drop_cols = frame_drop_col.columns.tolist()

    dev_cols = return_col_names(dev_col_nums, frame.columns.tolist())
    test_cols = dev_cols
    final_dev_cols = []
    tmp = []
    for item in test_cols:
        for itm in item:
            if itm in frame_drop_cols:
                tmp.append(itm)
        final_dev_cols.append(tmp)
        tmp = []

    for counter, entry in enumerate(devices):
        devices[counter]['Corresponding Data Column(s)'] = final_dev_cols[counter]

    df_time = frame[time_col].copy()
    df_time = df_time.astype(str)
    frame['date'] = frame[date_col].apply(
                    lambda x: datetime.datetime.strftime(x, "%Y-%m-%d"))
    frame.index = pd.to_datetime(frame['date'] + ' ' + df_time)
    frame.drop(['date'], axis=1, inplace=True)
    frame = drop_columns(frame, drop_cols)

    return devices


def process(exo_filename, output_dir, params):
    # TODO: Move sc_col, sc_cutoff to json file
    sc_col = u'SpCond µS/cm'
    sc_cutoff = 60
    interval = params.get('interval', 15)
    drop_cols = params.get('drop_cols', [])
    index_timezone = params.get('index_timezone', 'Datetime (PST)')
    mad_criteria = params.get('mad_criteria', 2.5)

    date_col = drop_cols[0]
    time_col = drop_cols[1]
    # end constants
    log = logging.getLogger('BurPro')
    log.info('Reading input file:' + exo_filename.split(os.sep)[-1])
    log.info('Please wait...')
    null_value = -9999
    try:
        # if .xlsx file exists, then read it into a dataframe
        df_exo = pd.read_excel(exo_filename, header=None)
    except IOError, ioerr:
        # otherwise, break out of the script with an error message
        log.info(ioerr.message)
#        report_setup_error(ioerr)

    log.info('Fetching file metatdata...')
    file_metadata = fetch_file_metadata(df_exo, drop_cols)

    log.info('Processing...')

    # make a copy of the read in dataframe for processing
    df_exo_float, grouped = process_data_frame(df_exo,
                                               date_col,
                                               time_col,
                                               drop_cols,
                                               null_value,
                                               index_timezone,
                                               interval,
                                               sc_col,
                                               sc_cutoff,
                                               file_metadata)
    exo_filename_only = exo_filename.split(os.sep)[-1]
    write_device_to_json(os.sep.join(
                         [output_dir,
                          exo_filename_only.replace('.xlsx',
                                                    '_EXOdevices.json')
                          ]),
                         file_metadata)

    # calc median absolute deviation
    exo_mad = calc_med_abs_dev(log,
                               df_exo_float,
                               grouped,
                               mad_criteria,
                               null_value)

    write_output(log, output_dir, exo_filename, exo_mad)
    log.info('Processing complete.')


def write_log_file(logger, user_id, fname, interval, min_burst_len,
                   sc_cutoff, datetime_format, exo, exo_cut,
                   grouped, grouped_cut, cut_burst_completion, devices):
    # def write_log_file(*pargs, **kwargs):
    #    write_log_file(logger, user_id, fname, interval, min_burst_len,
    #                   sc_cutoff, datetime_format, exo, exo_cut, grouped,
    #                   grouped_cut, cut_burst_completion)
    logger.info('THIS IS AN EXO DEPLOYMENT LOG FILE!!!')
    logger.info("User: %s", user_id)
    logger.info("Processed file: %s", fname)
    logger.info("Sample interval: %d minutes", interval)
    logger.info("Minimum number of measurements in each burst: %d",
                min_burst_len)
    logger.info("Specific conductance cutoff level: %d", sc_cutoff)
    logger.info("~~~~~~~~~~~~~~~~~~~~~~Deployment metadata~~~~~~~~~~~~~~~")
    logger.info("First record timestamp: %s",
                exo.index[0].strftime(datetime_format))
    logger.info("Last record timestamp: %s",
                exo.index[-1].strftime(datetime_format))
    logger.info("Starting number of measurements: %d", len(exo))
    logger.info("Number of bursts: %d", grouped.ngroups)
    logger.info("First cut record timestamp: %s",
                exo_cut.index[0].strftime(datetime_format))
    logger.info("Last cut record timestamp: %s",
                exo_cut.index[-1].strftime(datetime_format))
    logger.info("Ending number of measurements: %d", len(exo_cut))
    logger.info("Number of cut bursts: %d", grouped_cut.ngroups)
    logger.info("Number of bursts cut from record: %d",
                grouped.ngroups - grouped_cut.ngroups)

    logger.info("~~~~~~~~~~~~~~~~~~~~~~Sensor metadata~~~~~~~~~~~~~~~~~~~")

    sn_field = 'Serial Number'
    fw_field = 'Firmware Version'
    for count, name in enumerate(devices):
        logger.info("%s Serial Number: %s", devices[count]['Device Name'],
                    devices[count][sn_field])
        logger.info("%s Firmware: %s", devices[count]['Device Name'],
                    devices[count][fw_field])
        logger.info("%s Corresponding Data Column(s): %s",
                    devices[count]['Device Name'],
                    devices[count]['Corresponding Data Column(s)'],)
        logger.info("%s Start Datetime: %s",
                    devices[count]['Device Name'],
                    devices[count]['Start time'],)
        logger.info("%s End Datetime: %s",
                    devices[count]['Device Name'],
                    devices[count]['End time'],)

    logger.info("~~~~~~~~~~~~~~~~~~~~~~Burst completeness data~~~~~~~~~~~")
    for entry in sorted(cut_burst_completion.keys()):
        logger.info("%s burst completeness percentage: %3.2f",
                    entry, cut_burst_completion[entry])


def process_data_frame(df_exo,
                       date_col,
                       time_col,
                       drop_cols,
                       null_value,
                       index_timezone,
                       interval,
                       sc_col,
                       sc_cutoff,
                       file_metadata):

    fname = 'Test_datafilename'
    min_burst_len = 20
    datetime_format = "%Y-%m-%d %H:%M"
    user_id = getpass.getuser()

    frame = df_exo.copy()

    # find starting row by locating indicator date field
    nrow = frame.iloc[:, 0].isin([date_col]).idxmax(axis=0,
                                                    skipna=True)

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

    df_exo_float_cut = pd.DataFrame()
    if sc_col in df_exo_float.columns:
        df_exo_float_cut = df_exo_float[df_exo_float[sc_col] > sc_cutoff]
    # group bursts by interval
    grouped = df_exo_float.groupby(pd.TimeGrouper(str(interval) + "Min"),
                                   sort=False)

    grouped_cut = df_exo_float_cut.groupby(pd.TimeGrouper(str(interval) +
                                           "Min"), sort=False)

    start_times, end_times = get_start_end_times(df_exo_float)
    times_to_devices(start_times, end_times, file_metadata)

    cut_count = grouped_cut.count()
#    count = grouped.count()
# TODO: apply this filtering to pre and post mad
#    burst_completion = count_min_n_bursts(count, min_burst_len)
    cut_burst_completion = count_min_n_bursts(cut_count, min_burst_len)
    logger = logging.getLogger('EXOdevices')
    write_log_file(logger, user_id, fname, interval, min_burst_len,
                   sc_cutoff, datetime_format, df_exo_float, df_exo_float_cut,
                   grouped, grouped_cut, cut_burst_completion, file_metadata)

    return df_exo_float_cut, grouped_cut


def calc_med_abs_dev(log, df_exo_float, grouped, mad_criteria, null_value):
    exo_mad = pd.DataFrame()
    # apply the mad calculation column wise to data frame
    for i in np.arange(0, len(df_exo_float.columns), 1):
        step_number = '    (' + df_exo_float.columns[i] + ')'
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
    return


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
        print('argument must be a string')
    else:
        return string


def write_device_to_json(filename, devices):
    # TODO: Fix issues with printing unicode characters
    with open(filename, 'w') as outfile:
        json.dump(devices, outfile, indent=4, sort_keys=True,
                  separators=(',', ':'))
    return


def times_to_devices(start_times, end_times, devices):
    datetime_format = "%Y-%m-%d %H:%M:%S"
    for i, key in enumerate(devices):
        key['Start time'] = datetime.datetime.strftime(start_times[i][0],
                                                       datetime_format)
        key['End time'] = datetime.datetime.strftime(end_times[i][0],
                                                     datetime_format)


def get_start_end_times(frame):
    # TODO: Move output to devices.json log file
    start_times = []
    end_times = []
    for j, col in enumerate(frame.columns.tolist()):
        x = frame.iloc[:, j].notnull().tolist()
        x1 = np.hstack([[False], x, [False]])  # padding
        d = np.diff(x1.astype(int))
        start = np.where(d == 1)[0]
        end = np.where(d == -1)[0]-1

        start_times.append(frame.index[start].tolist())
        end_times.append(frame.index[end].tolist())

    return start_times, end_times


def extract_sensor_metadata(frame, nrow):
    """Return a dict of dicts -
    devices with serial numbers and fw version contained in raw exo frame"""
    sn_start = frame.iloc[:, 0].isin([u'EXO2 Sonde']).idxmax(axis=0,
                                                             skipna=True)

    name = frame.iloc[sn_start:nrow-2, 0].tolist()
    SN = frame.iloc[sn_start:nrow-2, 1].tolist()
    firmware = frame.iloc[sn_start:nrow-2, 2].tolist()
    devices = []
    for counter, entry in enumerate(name):
        info = {'Device Name': entry,
                'Serial Number': SN[counter],
                'Firmware Version': firmware[counter]}
        devices.append(info)

    return devices


def return_col_names(Corresponding_Data_Column, orig_col_names):
    device_data_cols = []
    temp = []
    for i in Corresponding_Data_Column:
        if isinstance(i, basestring):
            for j in i.split(';'):
                j = int(j) - 1
                temp.append(orig_col_names[j])
        device_data_cols.append(temp)
        temp = []

    return device_data_cols


def extract_data_cols(frame, nrow):
    sn_start = frame.iloc[:, 0].isin([u'EXO2 Sonde']).idxmax(axis=0,
                                                             skipna=True)
    Corresponding_Data_Column = frame.iloc[sn_start:nrow-2, 3].tolist()

    return Corresponding_Data_Column


def count_min_n_bursts(count, min_burst_len=20):
    stats = dict()
    for col in count.columns:
        counted = count[col]
        stat = sum(counted > min_burst_len)/float(len(counted))*100.
        stats[col] = stat
    return stats
