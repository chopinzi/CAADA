import pandas as pd

from ..caada_typing import pathlike as _pathlike


def read_pems_station_csv(csv_file: _pathlike) -> pd.DataFrame:
    """Read a Caltrans PEMS daily station .csv file

    Parameters
    ----------
    csv_file
        The path to the PEMS file to read

    Returns
    -------
        A dataframe containing the PEMS data with the correct header
    """
    columns = ['timestamp', 'station', 'district', 'route', 'direction of travel', 'lane type', 'station length', 'samples',
               'percent observed', 'total flow', 'delay 35', 'delay 40', 'delay 45', 'delay 50', 'delay 55', 'delay 60']
    df = pd.read_csv(csv_file, header=None)
    df.columns = columns
    df['timestamp'] = pd.DatetimeIndex(df['timestamp'])
    return df


def read_pems_station_meta(filename):
    df = pd.read_csv(filename, sep='\t')
    df.set_index('ID', inplace=True)
    df.rename(columns=lambda s: s.lower(), inplace=True)
    return df
