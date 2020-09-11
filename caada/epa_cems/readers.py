import pandas as pd
import re
from jllutils import miscutils

from ..caada_typing import pathseq, pathlike


def read_multi_cems_files(cems_files: pathseq, **kwargs) -> pd.DataFrame:
    """Read multiple US EPA CEMS .csv files

    Parameters
    ----------
    cems_files
        A sequence of paths to CEMS .csv files.

    kwargs
        Additional keyword arguments to pass to :func:`read_cems_file`

    Returns
    -------
    pandas.DataFrame
        A dataframe representing all the .csv files given in as arguments. The index with be a multiindex with state,
        date, facility_id, and unit_id. The data will be in the same order as the file names were given.

    """
    all_dfs = []
    pbar = miscutils.ProgressBar(len(cems_files), prefix='Loading files')
    for f in cems_files:
        pbar.print_bar()
        all_dfs.append(read_cems_file(f, **kwargs))
    all_dfs = [read_cems_file(f, **kwargs) for f in cems_files]
    return pd.concat(all_dfs)


def read_cems_file(cems_file: pathlike, drop_units: bool = True) -> pd.DataFrame:
    """Read a single US EPA CEMS .csv file

    Parameters
    ----------
    cems_file
        The path to the CEMS .csv file to read

    drop_units
        Whether to remove units from the column names.

    Returns
    -------
    pandas.DataFrame
        A dataframe representing the .csv file given as the first argument. The index with be a multiindex with state,
        date, facility_id, and unit_id.
    """
    def rename_fxn(c):
        c = c.lower()
        if drop_units:
            c = re.sub(r'\(.+\)', '', c).strip()
        return c

    df = pd.read_csv(cems_file)
    df.index = _cems_multiindex(df)
    cols_to_drop = ['STATE', 'OP_DATE', 'FAC_ID', 'UNIT_ID']
    if 'OP_HOUR' in df.columns:
        cols_to_drop.append('OP_HOUR')
    df.drop(columns=cols_to_drop, inplace=True)
    df.rename(columns=rename_fxn, inplace=True)
    return df


def _cems_multiindex(df):
    states = df['STATE']
    fac = df['FAC_ID']
    unit = df['UNIT_ID']
    dates = pd.DatetimeIndex(df['OP_DATE'])
    if 'OP_HOUR' in df.columns:
        dates = [d + pd.Timedelta(hours=h) for d, h in zip(dates, df['OP_HOUR'])]
        dates = pd.DatetimeIndex(dates)
    return pd.MultiIndex.from_arrays([states, dates, fac, unit], names=['state', 'date', 'facility_id', 'unit_id'])
