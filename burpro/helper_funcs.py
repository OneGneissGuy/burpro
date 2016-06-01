import numpy as np
import numpy.ma as ma
import pandas as pd
import statsmodels.robust.scale as smc


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


def find_col_idx(params, field):
    return [i for i, s in enumerate(params) if field in s]


def has_numbers(inputString):
    """This function identifies strings that contain numerical characters
    INPUT:
    string, string like
    RETURNS:
    bool"""
    return any(char.isdigit() for char in inputString)


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
