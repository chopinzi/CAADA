import pandas as pd
import re

from ..caada_typing import pathlike

def _parse_column_name(colname):
    regex = re.compile(r'^([\w\s]+) (all sectors|residential|commercial|industrial|transportation|other) ([\w\s]+)$')
    match = regex.search(colname)

    info = dict(location=match.group(1), sector=match.group(2), units=match.group(3))
    return info


def _columns_to_multiindex(columns):
    mi_list = []
    units_dict = dict()

    for col in columns:
        info = _parse_column_name(col)
        loc = info['location']
        sec = info['sector']

        mi_list.append((loc, sec))
        if loc not in units_dict:
            units_dict[loc] = dict()
        units_dict[loc][sec] = info['units']

    return pd.MultiIndex.from_tuples(mi_list), units_dict


def load_eia_df(filename: pathlike, with_units: bool = False):
    """Load an EIA electricity consumption chart CSV as a dataframe

    Parameters
    ----------
    filename
        A path to a .csv file that is the CHART download from https://www.eia.gov/electricity/data/browser/#/topic/.

    with_units
        If `True`, then a dictionary of units is returned alongside the dataframe. If `False`, only the dataframe is
        returned.

    Returns
    -------
    pandas.DataFrame
        A dataframe corresponding to the .csv file. The index will be a datetime index matching the times in the .csv
        file and the columns will be a multiindex with the first level giving the region (e.g. United States,
        California) and the second level giving the sector.

    dict (optional)
        This is only returned if `with_units` is `True`. It is a dictionary of dictionaries, with the top

    """
    df = pd.read_csv(filename, header=4)
    df.index = pd.DatetimeIndex(df['Month'])
    df.drop(columns=['Month'], inplace=True)

    mi, units = _columns_to_multiindex(df.columns)
    df.columns = mi

    df.sort_index(inplace=True)

    if with_units:
        return df, units
    else:
        return df
