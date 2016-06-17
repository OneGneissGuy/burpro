# -*- coding: utf-8 -*-
"""
:DESCRIPTION: This code processes EXO KOR Burst data files

:REQUIRES: helper_funcs.py, .xlsx burst data files in cwd folder "data"

:#TODO:
1) Add support to read in multiple files in a directory
2) Add support to write mad files to csv format

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
import os.path
import sys
import logging
import traceback
import getpass

import numpy as np
import pandas as pd

from helper_funcs import custom_mad, drop_columns, has_numbers, read_json_file
from helper_funcs import validate_json

# =============================================================================
# MAIN METHOD AND TESTING AREA
# =============================================================================
    
#Override error handling in the parser library
class BurProArgumentParser(argparse.ArgumentParser):    
    def error(self, message):
        raise Exception(message)

def main(argv=None):
    try:
        exo_filename = handle_args(argv)
        output_dir = setup_dir(exo_filename)
        
        logging.basicConfig(filename=os.path.join(output_dir, 'burpro.log')) 
        log = logging.getLogger('BurPro')
        log.setLevel(logging.INFO)         
        log.info('USGS California Water Science Center')
        log.info('BurPro Revision ' + burpro_version())
        
        formatter = logging.Formatter()
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        log.addHandler(console)

        try:
            process(exo_filename, output_dir)
            log.info('BurPro done.')
        except:
            log.error(formatter.formatException(sys.exc_info()))
            sys.exit(3)
    except Exception, setup_error:
        report_setup_error(setup_error)
        
def burpro_version():
    return '2016-06-17'
    
def report_setup_error(error):
    print >>sys.stderr, 'BurPro Setup Error: ', error
    traceback.print_exc()
    print >>sys.stderr, 'Exiting.'
    sys.exit(2)
    
def handle_args(argv=None):
    if argv is None:
        argv = sys.argv
    if len(sys.argv) < 2:
        raise Exception('BurPro must be given an input file for processing')
#        print >>sys.stderr, 'BurPro error on startup'
#       print >>sys.stderr, 'BurPro must be given an input file for processing'
#        print >>sys.stderr, 'Exiting.'
#        sys.exit(2)

    print 'USGS California Water Science Center'
    print 'BurPro Revision ' + burpro_version()
    print 'Reading parameters...'
    
    parser = BurProArgumentParser(
             description="KOR exo file")
    parser.add_argument('exo_filename', type=str)
    input_path = parser.parse_args()
    
    return input_path.exo_filename
    
def setup_dir(exo_filename):
    dir_name = "BurPro_" + getpass.getuser() + "_"
    dir_name = dir_name + datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    base_path = os.path.dirname(exo_filename)
    output_dir = os.path.join(base_path, dir_name)
    print 'Writing output to ' + output_dir
    os.makedirs(output_dir)    

    return output_dir

def process(exo_filename, output_dir):
    
    #TODO: hierarchal sjon support
    #TODO: Look for json exo file direc then look in bat directory, etc.
    script_path, script_name_only = os.path.split(os.path.realpath(__file__))
    json_filename = os.path.join(script_path, 'config', 'run_params.json')
    #    # read json file

    validate_json(json_filename)
    run_params = read_json_file(json_filename)
    params = run_params['gov.usgs.cawsc.bgctech.burpro']
#    filename = os.sep.join([params.get('directory', 'data'),
#                            params.get('filename', 'test_data_file.xlsx')])
    interval = params.get('interval', 15)
    drop_cols = params.get('drop_cols', [])
    index_timezone = params.get('index_timezone', 'Datetime (PST)')
    mad_criteria = params.get('mad_criteria', 2.5)
    
    log = logging.getLogger('BurPro')
    log.info('Reading input...')

    date_col = drop_cols[0]
    time_col = drop_cols[1]
    # end constants
    null_value = -9999
    if os.path.isfile(exo_filename):
        # if .xlsx file exists, then read it into a dataframe
        df_exo = pd.read_excel(exo_filename, header=None)
    else:
        # otherwise, break out of the script with an error message
        sys.exit("filepath: '%s' not found" % exo_filename)
        
    log.info('Processing...')
    
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
    # calc median absolute deviation
    exo_mad = pd.DataFrame()
    # apply the mad calculation column wise to data frame
    for i in np.arange(0, len(df_exo_float.columns), 1):
        step_number = '    (' + str(i+1) + ')'
        log.info(step_number)
        exo_mad[df_exo_float.columns[i]] = grouped[
                                           df_exo_float.columns[i]].apply(
                                           custom_mad, criteria=mad_criteria)
    exo_mad.replace(to_replace=null_value, value=np.nan, inplace=True)

    log.info('Writing output...')
    input_path, input_name_only = os.path.split(exo_filename)
    output_name_only = input_name_only.replace(".xlsx", "_mad.xlsx")
    output_filename = os.path.join(output_dir, output_name_only)
    exo_mad.to_excel(output_filename)
    # write csv
    #    exo_mad.to_csv(exo_filename.replace(".xlsx", "_mad.csv"))
    log.info('Processing complete.')

if __name__ == "__main__":
    sys.exit(main())

# %%
#if __name__ == "__main__":
    #    parser = argparse.ArgumentParser(description="JSON run settings file")
    #    parser.add_argument('filename', type=str)
    #    # get json file path passed to script at command line
    #    json_filename = parser.parse_args()
    #    # read json file
    #    validate_json(json_filename.filename)
    #    kwargs = read_json_file(json_filename.filename)
    #    # pass run params from json file onto main program
    #    main(**kwargs)

#    parser = argparse.ArgumentParser(
#             description="KOR exo file")
#    parser.add_argument('exo_filename', type=str)
#    input_path = parser.parse_args()
#    main(input_path.exo_filename)
