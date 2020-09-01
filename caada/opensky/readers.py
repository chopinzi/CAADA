import pandas as pd

from ..caada_typing import pathlike
from ..caada_logging import logger

from . import web
from . import get_airport_code_source


def read_airport_codes(source: str = 'openflights', update: str = 'never') -> pd.DataFrame:
    """Read airport codes and geographic data from a web source

    Parameters
    ----------
    source
        Which web source to pull data from. Currently the only allowed option is `"openflights"`.

    update
        Controls whether CAADA redownloads the needed data or not. Possible values are:

            * `"never"` - only download if no local copy is available.
            * `"periodically"` - only download if the local copy is more than a week old.
            * `"always"` - always redownloads

    Returns
    -------
    pandas.DataFrame
        A dataframe containing geographic data about global airports. The exact data available depends on the source.
    """
    web._download_airport_codes(source, update=update)
    local_file = get_airport_code_source(source)['local']
    df = pd.read_csv(local_file, header=None).iloc[:, :11]
    df.columns = ['entry_id', 'airport_name', 'city_name', 'country_name', 'iata_code', 'icao_code',
                  'latitude', 'longitude', 'elevation', 'utc_offset', 'dst_group']
    # convert altitude from feet to meters
    df.loc[:, 'elevation'] *= 0.3048
    df.set_index('entry_id', inplace=True)
    return df


def read_opensky_covid_file(filename: pathlike, code_source: str = 'openflights', update_codes: str = 'never') -> pd.DataFrame:
    """Read a .csv file from https://doi.org/10.5194/essd-2020-223

    Parameters
    ----------
    filename
        Path to the .csv file to read

    code_source
        Which web source to use for the geographic data. See :func:`read_airport_codes` in this module.

    update_codes
        Controls whether the geographic data is updated. See :func:`read_airport_codes` in this module.

    Returns
    -------
    pandas.DataFrame
        A dataframe with the information from the .csv file. It will be joined with geographic data: columns prepended
        with "origin_" and "dest_" are the geographic data for the origin and destination airports, respectively.
    """
    logger.info('Reading %s', filename)
    df = pd.read_csv(filename, parse_dates=['firstseen', 'lastseen', 'day'])
    df.drop(columns=df.columns[0], inplace=True)

    airport_codes = read_airport_codes(source=code_source, update=update_codes)
    airport_codes.drop(columns=['elevation', 'utc_offset', 'dst_group'], inplace=True)

    # Add some information about the origin and destination airports
    logger.info('Adding origin & destination metadata')
    df = df.merge(airport_codes, how='left', left_on='origin', right_on='icao_code')
    df.drop(columns=['icao_code'], inplace=True)
    rename_dict = {c: 'origin_{}'.format(c) for c in airport_codes.columns if c != 'icao_code'}
    df.rename(columns=rename_dict, inplace=True)

    df = df.merge(airport_codes, how='left', left_on='destination', right_on='icao_code')
    df.drop(columns=['icao_code'], inplace=True)
    rename_dict = {c: 'dest_{}'.format(c) for c in airport_codes.columns if c != 'icao_code'}
    df.rename(columns=rename_dict, inplace=True)

    return df
