#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 16 12:50:50 2024

@author: che
"""

import pandas as pd
import numpy as np
import os
import logging

def get_ep_template(version=16.2):
    ''' Open template and return mapped df with empty values. '''
    module_dir = os.path.dirname(__file__)
    fpath = f"{module_dir}/templates/{version}/EP_MAPPED.csv"
    df = pd.read_csv(fpath, index_col=0)
    df = df.sort_values(by = ['Section', 'Tab', 'Subtab', 'Area', 'Row', 'Col'])
    df['value'] = np.nan
    df['value'] = df['value'].astype(object)
    return df

def initialise_settings(df, settings=None, version=16.2):
    ''' Initialise template, optionally using settings '''
    if settings is None:
        module_dir = os.path.dirname(__file__)
        fpath = f"{module_dir}/templates/{version}/EP_default_zeroed.txt"
        df_settings = load_settings_file(fpath)
    df['value'] = df_settings
    return df

def load_settings_file(fpath, raw=True, drop_duplicates=False):
    ''' Returns parsed settings from an EP settings .txt file. '''
    lines = read_settings_file(fpath)
    df = load_energyplan_settings(lines, raw=raw)
    return df

def read_settings_file(fpath):
    ''' Returns raw lines from an EP settings .txt file. '''
    with open(fpath, 'r', encoding='cp1252') as file:
        lines = file.readlines()
    return lines

def load_energyplan_settings(lines, raw=True, drop_duplicates=False):
    '''
    Parse EnergyPLAN settings from a list of lines.

    Parameters
    ----------
    lines : list of strings, lines read from file
    raw : bool, optional
        Set to True when reading a file saved by EnergyPLAN.
        Set to False when reading a settings file formatted by this module.
    drop_duplicates : bool, optional
        Drop index duplicates. Use with care - EnergyPLAN is known to duplicate
        the `input_cshp_el_gr3` key in some instances.

    Returns
    -------
    df : TYPE
        DESCRIPTION.

    '''
    if raw:  # Fix messy output if file hasn't been cleansed elsewhere
        # Extra newline
        lines = lines[::2]
        # The last five lines are non-semantic: `xxx` then a single blank
        lines = lines[:-5]
        # Remove all the bonus newlines
        lines = [l.rstrip('\n') for l in lines]
        # Remove all the bonus spaces between every char
        lines = [l.replace('\x00', '') for l in lines]
    # Split to key and value
    keys = lines[::2]
    vals = lines[1::2]
    # Strip the '=' from the keys
    '''Energyplan version does not have!'''
    keys = [k.rstrip('\n') for k in keys]
    keys = [k.rstrip('=') for k in keys]
    vals = [v.rstrip('\n') for v in vals]
    # Create df
    df = pd.DataFrame({'key': keys, 'value': vals})
    # Remove duplicates
    if drop_duplicates:
        idc_dup = df['key'].duplicated()
        df = df.loc[~idc_dup]
    # Set index
    df = df.set_index('key')
    ### BUG ###
    # Fix the mangled version key using a mask
    idx_mask = df.index.str.contains("PLAN version")
    version = df.loc[df.index[idx_mask], 'value'].values[0]
    df = df.drop(index=df.index[idx_mask])
    df.loc["EnergyPLAN version", 'value'] = version
    ### BUG ###
    # Insert to mapped template
    df_mapped = get_ep_template()
    df_mapped['value'] = df['value']
    return df

def save_settings_file(df, fpath, EPS=1e-4):
    '''
    Save simulation settings to EnergyPLAN input file.

    Parameters
    ----------
    df : pandas Dataframe
        EnergyPLAN simulation settings where df.index is the parameter key and
        the column 'value' is used as the parameter value.
    fpath : string
        Absolute or relative path to output file.
    EPS : float, optional
        EnergyPLAN does not reliably parse very small numbers. All numbers
        less than EPS will be set to zero The default is 1e-4.

    Returns
    -------
    None.

    '''
    logger = logging.getLogger("epnlink.utilities.save_settings_file")
    # Convert df to series
    settings = df['value']
    # Export in the format the EP expects
    lines = []
    for k,v in settings.items():
        lines.append(f"{k}=")
        if pd.api.types.is_number(v):
            if v < EPS:  # Negligible values break EP
                lines.append("0")
                logger.debug(f"Replacing with zero for {k}={v}")
            else:
                # EP may not parse floats with more than 5 digits after decimal
                lines.append(f"{np.format_float_positional(v, precision=5)}")
        else:
            lines.append(f"{v}")
    lines = '\n'.join(lines)
    with open(fpath, 'wt') as f:
        f.write(lines)
