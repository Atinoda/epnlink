#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Parse EnergyPLAN 16.2 ascii output, produced by cli simulations.'''

import pandas as pd
from io import StringIO
import re  # It just got real.
import numpy as np


#%% FUNCTIONS

def tabs_to_double_space(line):
    # Replace tabs with two consecutive spaces
    text_re = re.sub(r'\t', '  ', line)
    return text_re

def visual_indentation_to_logical(line):
    # Replace two consecutive spaces with tab
    text = re.sub(r'  ', '\t', line)
    # Replace space followed by tab with tab
    text = re.sub(r' +\t', '\t', text)
    # Replace tab followed by space with tab
    text = re.sub(r'\t +', '\t', text)
    # Replace multiple consecutive tabs with a single tab
    text = re.sub(r'\t+', '\t', text)
    # Strip leading spaces and tabs
    text = text.lstrip(' ').lstrip('\t')
    # Strip trailing spaces and tabs and newlines
    text = text.rstrip('\n').rstrip(' ').rstrip('\t')
    return text

def max_fields(lines):
    max_fields_count = 0
    for line in lines:
        fields_count = line.count('\t') + 1
        if fields_count > max_fields_count:
            max_fields_count = fields_count
    return max_fields_count

def pad_fields(lines, max_fields_count, fill_value):
    padded_lines = []
    for line in lines:
        fields = line.strip().split('\t')
        padded_fields = fields + [fill_value] * (max_fields_count - len(fields))
        padded_line = '\t'.join(padded_fields)
        padded_lines.append(padded_line)
    return padded_lines

def fill_missing_fields(lines, fill_value='nan'):
    max_fields_count = max_fields(lines)
    lines_padded = pad_fields(lines, max_fields_count, fill_value)
    return lines_padded

def lines_to_df(lines, sep='\t', header=None, index_col=None):
    df = pd.read_csv(
        StringIO('\n'.join(lines)),
        sep=sep, header=header, index_col=index_col)
    return df


#%%

def read_ascii_file(fpath):
    with open(fpath, 'r') as f:
        lines_raw = f.readlines()
    results = parse_ascii(lines_raw)
    return results


def parse_ascii(lines_raw):
    '''Parse string of raw ascii output to dict of dataframes.'''
    # Instantiate results object
    results = {}

    # Visual alignment
    lines = [tabs_to_double_space(line) for line in lines_raw]

    # Slice into sections
    summary_tables = lines[3:74]
    headers = lines[80:82]
    application_annual_twh = lines[84:85]
    application_monthly_avg_mw = lines[87:99]
    application_annual_avg_max_min_mw = lines[100:103]
    application_hourlies_mw = lines[105:]

    # Summaries
    idx_col0 = 80
    idx_col1 = 198
    summary_col0 = [line[:idx_col0] for line in summary_tables]
    summary_col1 = [line[idx_col0:idx_col1] for line in summary_tables]
    summary_col2 = [line[idx_col1:] for line in summary_tables]

    ### Col 0

    # Prepare lines
    summary_col0_tabbed = [visual_indentation_to_logical(line) for line in summary_col0]

    # Simulation parameters
    lines = summary_col0_tabbed
    parameters = {
        'version': lines[0],
        'dataset': lines[1].split('\t')[-1],
        'regulation_strategy': lines[2],
        'ceep_strategy': lines[3].split('\t')[-1],
        }
    # results['sim_parameters'] = parameters
    df_parameters = pd.DataFrame.from_dict(parameters, orient='index')
    df_parameters.columns = ['value']
    results['sim_parameters']= df_parameters.copy()

    # Calculation time
    # TODO: Appears to be invalid
    lines = summary_col0_tabbed[5:11]
    df = lines_to_df(lines, index_col=0)
    df.columns = ['time']
    results['calculation_time']= df.copy()

    # CO2 emissions
    lines = summary_col0_tabbed[13:15]
    df = lines_to_df(lines, index_col=0)
    df.columns = ['Mt']
    results['annual_emissions_co2'] = df.copy()

    # Share of RES
    lines = summary_col0_tabbed[17:20]
    df = lines_to_df(lines, index_col=0)
    df.columns = ['value', 'unit']
    results['annual_share_of_res'] = df.copy()

    # Annual fuel consumption
    lines = summary_col0_tabbed[22:34]
    lines = fill_missing_fields(lines, 'nan')
    df = lines_to_df(lines, index_col=0)
    df.columns = ['total', 'households']
    results['annual_fuel_consumption'] = df.copy()

    # Annual costs
    lines = summary_col0_tabbed[35:65]
    lines = fill_missing_fields(lines, 'nan')
    df = lines_to_df(lines, index_col=0)
    df.columns = ['total', 'variable', 'breakdown']
    # Drop empty and labels
    df = df.dropna(how='all')
    df = df.iloc[1:]
    # Hardcode the column membership
    idc_variable = [
        'Fuel ex. Ngas exchange',
        'Ngas Exchange costs',
        'Marginal operation costs',
        'Electricity exchange',
        'CO2 emission costs',
        ]
    idc_breakdown = [
        'Coal',
        'FuelOil',
        'Gasoil/Diesel',
        'Petrol/JP',
        'Gas handling',
        'Biomass',
        'Food income',
        'Waste',
        ]
    df.loc[idc_variable, 'variable'] = df.loc[idc_variable, 'total']
    df.loc[idc_variable, 'total'] = np.nan
    df.loc[idc_breakdown, 'breakdown'] = df.loc[idc_breakdown, 'total']
    df.loc[idc_breakdown, 'total'] = np.nan
    results['annual_costs'] = df.copy()


    ### Col 1
    # Prepare lines
    summary_col1_tabbed = [visual_indentation_to_logical(line) for line in summary_col1]

    # Simulation parameters (cont.)
    results['sim_parameters'].loc['interest_rate'] = summary_col1_tabbed[0].split('\t')[-1][:-1]

    # Investment costs
    lines = summary_col1_tabbed[4:70]
    lines = fill_missing_fields(lines, 'nan')
    df = lines_to_df(lines, index_col=0)
    cols = [
            'Total Investment',
            'Annual Investment',
            'Fixed O&M',
            'alt Total Investment',
            'alt Annual Investment',
            'alt Fixed O&M ',
            ]
    df.columns = cols
    df = df.dropna(how='all')
    results['annual_investment_costs'] = df.copy()


    ### Col 2
    # Prepare lines
    summary_col2_tabbed= [visual_indentation_to_logical(line) for line in summary_col2]

    # Fuel Balance
    lines = summary_col2_tabbed[3:13]
    df = lines_to_df(lines, header=0, index_col=0)
    results['annual_fuel_balance'] = df.copy()

    # Emissions
    lines = summary_col2_tabbed[15:20]
    df = lines_to_df(lines, index_col=0)
    df.columns = ['ton']
    results['annual_emissions'] = df.copy()


    # Application tables
    # Prepare headers
    headers_tabbed = [visual_indentation_to_logical(line) for line in headers]
    headers_listed = [line.split('\t') for line in headers_tabbed]
    # Insert blanks to align lists
    # TIP: Get the headers from Excel output, transpose, and read off the indices
    idc_blanks = [
        111,
        112,
        115,
        119,
        120,
        121,
        122,
        123,
        124,
        126,
        ]
    for idx in idc_blanks:
        headers_listed[1].insert(idx, '')
    # Join the headers
    headers_joined = list(zip(*headers_listed))
    headers_strings = [' '.join(hi).rstrip() for hi in headers_joined]

    # Applications annual total (TWh)
    lines = [visual_indentation_to_logical(line) for line in application_annual_twh]
    df = lines_to_df(lines, index_col=0)
    df.columns = headers_strings
    df.index = ['Annual']
    results['application_annual_total_twh'] = df.copy()

    # Applications monthly average (MW)
    lines = [visual_indentation_to_logical(line) for line in application_monthly_avg_mw]
    df = lines_to_df(lines, index_col=0)
    df.columns = headers_strings
    results['application_monthly_avg_mw'] = df.copy()

    # Applications annual average, maximum, minimum (MW)
    lines = [visual_indentation_to_logical(line) for line in application_annual_avg_max_min_mw]
    df = lines_to_df(lines, index_col=0)
    df.columns = headers_strings
    results['application_annual_avg_max_min_mw'] = df.copy()

    # Applications hourlies
    lines = [visual_indentation_to_logical(line) for line in application_hourlies_mw]
    df = lines_to_df(lines, index_col=0)
    df.columns = headers_strings
    results['application_hourlies_mw'] = df.copy()

    return results
